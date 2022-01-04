#   Isotammi Genealogical Service for combining multiple researchers' results.
#   Created in co-operation with the Genealogical Society of Finland.
#
#   Copyright (C) 2016-2021  Juha Mäkeläinen, Jorma Haapasalo, Kari Kujansuu,
#                            Timo Nallikari, Pekka Valta
#
#   This program is free software: you can redistribute it and/or modify
#   it under the terms of the GNU General Public License as published by
#   the Free Software Foundation, either version 2 of the License, or
#   (at your option) any later version.
#
#   This program is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU General Public License for more details.
#
#   You should have received a copy of the GNU General Public License
#   along with this program.  If not, see <http://www.gnu.org/licenses/>.

# pylint: disable=line-too-long
# pylint: disable=invalid-name
# pylint: disable=missing-docstring
# pylint: disable=bad-whitespace
# pylint: disable=trailing-whitespace
# pylint: disable=trailing-newlines
# pylint: disable=too-few-public-methods
# pylint: disable=too-many-branches

"""
    Methods to calculate the possible lifespan of people.
    
    People are represented by objects of class Person.
    Each person has three properties, all are lists
    - parents
    - children
    - events
    Parents and children are lists of the corresponding Person objects.
    Events are objects with three properties: eventtype, datetype and year
    - eventtype: one of BIRTH, DEATH, MARRIAGE, "resi" (or basically anything – 
      only birth, death and marriage have special handling)
    - datetype: one of: "exact", "before", "after"
    - year: integer representing the year of the event, or None if not known
    
    Usage:
    First call "calculate_estimates" for all persons. 
    Then call "__calculate_estimates_family" for all persons. 
    The first call only calculates the estimates based on the events of the person itself. 
    The latter call then examines each person's parents and children and updates
    the estimates accordingly.
    
    The result is that these four properties are set for each person:
    - birth_low
    - birth_high
    - death_low
    - death_high
"""

import datetime
import sys
from dataclasses import dataclass

# from json.decoder import _decode_uXXXX

MAX_AGE = 110
MIN_MARR_AGE = 15
MIN_CHILD_AGE = 15
MAX_CHILD_AGE = 65
MAX_BAPTISM_DELAY = 1
MAX_BURIAL_DELAY = 1
MAX_PARENT_DEATH_CHILD_BIRTH_GAP = 1

BIRTH = "Birth"
DEATH = "Death"
MARRIAGE = "Marriage"
BURIAL = "Burial"
BAPTISM = "Baptism"

MAX_ITERATIONS = 10 

class Person:
    def __init__(self):
        self.pid = None
        self.gramps_id = None
        self.events = []
        self.parents = []
        self.children = []
        self.spouses = []

    def __str__(self):
        # pare = [f"{x.gramps_id}({x.pid})" for x in self.parents]
        # chdr = [f"{x.gramps_id}({x.pid})" for x in self.children]
        return (
            f"{self.gramps_id}({self.pid}): {len(self.events)} events, "
            f"parents={self.parent_pids}, children={self.child_pids}"
        )


@dataclass
class Year:
    valuetype: str  # "min", "max", "normal"
    value: int

    def __add__(self, years):
        if self.valuetype == "normal":
            return Year("normal", self.value + years)
        return self

    def __sub__(self, years):
        if self.valuetype == "normal":
            return Year("normal", self.value - years)
            self.value -= years
        return self

    def __eq__(self, other):
        if isinstance(other, int):
            if self.valuetype != "normal":
                return False
            return self.value == other
        if other.valuetype != self.valuetype:
            return False
        if other.valuetype == "normal":
            return self.value == other.value
        return True

    def getvalue(self):
        if self.valuetype == "normal":
            return self.value
        if self.valuetype == "min":
            return -9999
        if self.valuetype == "max":
            return 9999


MIN = Year("min", None)
MAX = Year("max", None)
current_year = datetime.date.today().year
CURRENT_YEAR = Year("normal", current_year)


@dataclass
class Event:
    eventtype: str
    datetype: str
    year: int
    role: str = "Primary"


def ymin(a, b):
    if a is MAX:
        return b
    if b is MAX:
        return a
    if a is MIN:
        return MIN
    if b is MIN:
        return MIN
    return Year("normal", min(a.value, b.value))


def ymax(a, b):
    if a is MIN:
        return b
    if b is MIN:
        return a
    if a is MAX:
        return MAX
    if b is MAX:
        return MAX
    return Year("normal", max(a.value, b.value))


def __empty_range(r):
    if r[0] == MIN or r[1] == MAX:
        return False
    return r[0].value > r[1].value


def __compute_overlap(r1, r2):
    lo1, hi1 = r1
    lo2, hi2 = r2
    return (ymax(lo1, lo2), ymin(hi1, hi2))


def __update_range(p, eventtype, low, high):
    """
    Update the possible range for 'eventtype'
    for person p to 'low-high'
    """
    #print(p,eventtype,low,high)
    current_range1 = p.estimates[eventtype]
    if __empty_range(current_range1):
        # already empty, warning already given
        return
    current_range = __compute_overlap(current_range1, (low, high))
    if __empty_range(current_range):
        pass
#         print(
#             p.gramps_id,
#             ": empty range",
#             eventtype,
#             current_range1,
#             "&",
#             (low, high),
#             "->",
#             current_range,
#             file=sys.stderr,
#         )
        # assert not __empty_range(current_range)
    else:
        p.estimates[eventtype] = current_range


def __get_estimates(p):
    return (p.birth_low, p.birth_high, p.death_low, p.death_high)


def __update_estimates(p):
    p.birth_low = p.estimates[BIRTH][0]
    p.birth_high = p.estimates[BIRTH][1]
    p.death_low = p.estimates[DEATH][0]
    p.death_high = p.estimates[DEATH][1]

    p.death_low = ymax(p.death_low, p.birth_low)
    p.birth_low = ymax(p.death_low - MAX_AGE, p.birth_low)
    p.birth_high = ymin(p.birth_high, p.death_high)
    p.death_high = ymin(p.birth_high + MAX_AGE, p.death_high)


def __calculate_estimates1(p):
    """
    Update values based on personal events
    """
    p.birth_low = MIN
    p.death_low = MIN
    p.birth_high = MAX
    p.death_high = MAX
    p.estimates = {BIRTH: (MIN, CURRENT_YEAR), DEATH: (MIN, MAX)}
    for e in p.events:
        if e.year is None:
            continue
        year = Year("normal", e.year)
        if e.datetype == "exact":
            if e.eventtype == BIRTH and e.role == "Primary":
                __update_range(p, BIRTH, year, year)
            if e.eventtype == DEATH and e.role == "Primary":
                __update_range(p, DEATH, year, year)
            if e.eventtype == BAPTISM and e.role == "Primary":
                __update_range(p, BIRTH, year - MAX_BAPTISM_DELAY, year)
            if e.eventtype == BURIAL and e.role == "Primary":
                __update_range(p, DEATH, year - MAX_BURIAL_DELAY, year)
            else:
                __update_range(p, DEATH, year, year + MAX_AGE)
            if e.eventtype == MARRIAGE and e.role == "Family":
                __update_range(p, BIRTH, MIN, year - MIN_MARR_AGE)
                __update_range(p, DEATH, year, year - MIN_MARR_AGE + MAX_AGE)
            __update_range(p, BIRTH, year - MAX_AGE, year)

        if e.datetype == "after":
            if e.eventtype == BIRTH and e.role == "Primary":
                __update_range(p, BIRTH, year, MAX)
            if e.eventtype == BAPTISM and e.role == "Primary":
                __update_range(p, BIRTH, year - MAX_BAPTISM_DELAY, MAX)
            if e.eventtype == BURIAL and e.role == "Primary":
                __update_range(p, BIRTH, year - MAX_BURIAL_DELAY - MAX_AGE, MAX)
                __update_range(p, DEATH, year - MAX_BURIAL_DELAY, MAX)
            else:
                __update_range(p, BIRTH, year - MAX_AGE, MAX)
                __update_range(p, DEATH, year, MAX)

        if e.datetype == "before":
            if e.eventtype == MARRIAGE and e.role == "Family":
                __update_range(p, BIRTH, MIN, year - MIN_MARR_AGE)
            __update_range(p, BIRTH, MIN, year)
            if e.eventtype == DEATH and e.role == "Primary":
                __update_range(p, DEATH, MIN, year)
            elif e.eventtype == BURIAL and e.role == "Primary":
                __update_range(p, DEATH, MIN, year)
            else:
                __update_range(p, DEATH, MIN, year + MAX_AGE)

    __update_estimates(p)


def __calculate_estimates_family(p):
    """
    Update values based on parent and children values
    """
    for par in p.parents:
        __update_range(p, BIRTH, par.birth_low + MIN_CHILD_AGE, MAX)
        __update_range(
            p, BIRTH, MIN, par.death_high + MAX_PARENT_DEATH_CHILD_BIRTH_GAP
        )  # a child may be born after father's death
        __update_range(p, BIRTH, MIN, par.birth_high + MAX_CHILD_AGE)
    for c in p.children:
        __update_range(p, BIRTH, c.birth_low - MAX_CHILD_AGE, MAX)
        __update_range(p, BIRTH, MIN, c.birth_high - MIN_CHILD_AGE)
        __update_range(
            p, DEATH, c.birth_low - MAX_PARENT_DEATH_CHILD_BIRTH_GAP, MAX
        )  # father may have died before a child was born

    for sp in p.spouses:
        #print("spouse",p,sp)
        __update_range(p, BIRTH, sp.birth_low - MAX_AGE + MIN_MARR_AGE, MAX)
        __update_range(p, BIRTH, MIN, sp.birth_high + MAX_AGE - MIN_MARR_AGE)
        __update_range(p, BIRTH, MIN, sp.death_high - MIN_MARR_AGE)
        __update_range(p, DEATH, sp.birth_low + MIN_MARR_AGE, MAX)

    __update_estimates(p)


def calculate_estimates(personlist):
    for p in personlist:
        __calculate_estimates1(p)
    n = 0
    while True:
        personlist2 = set()
        for p in personlist:
            orig = __get_estimates(p)
            __calculate_estimates_family(p)
            new = __get_estimates(p)
            if new != orig:
                for parent in p.parents:
                    personlist2.add(parent)
                for c in p.children:
                    personlist2.add(c)
                for sp in p.spouses:
                    personlist2.add(sp)
        if len(personlist2) == 0:
            break
        personlist = personlist2
        n += 1
        if n > MAX_ITERATIONS:
            break  # prevent infinite loop
