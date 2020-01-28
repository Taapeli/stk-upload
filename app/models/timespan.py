# pylint: disable=line-too-long
# pylint: disable=invalid-name
# pylint: disable=missing-docstring
# pylint: disable=bad-whitespace
# pylint: disable=trailing-whitespace
# pylint: disable=trailing-newlines
# pylint: disable=too-few-public-methods
# pylint: disable=too-many-branches

# Methods to calculate the possible lifespan of people.
#
# People are represented by objects of class Person.
# Each person has three properties, all are lists
# - parents
# - children
# - events
# Parents and children are lists of the corresponding Person objects.
# Events are objects with three properties: eventtype, datetype and year
# - eventtype: one of BIRTH, DEATH, MARRIAGE, "resi" (or basically anything- only birth, death and marriage have special handling)
# - datetype: one of: "exact", "before", "after"
# - year: integer representing the year of the event, or None if not known
#
# Usage:
# First call "calculate_estimates" for all persons. Then call "__calculate_estimates2" for all persons. The first call only calculates the
# estimates based on the events of the person itself. The latter call then examines each person's parents and children and updates
# the estimates accordingly.
#
# The result is that these four properties are set for each person:
# - earliest_possible_birth_year
# - latest_possible_birth_year
# - earliest_possible_death_year
# - latest_possible_death_year
import sys
from dataclasses import dataclass

MAX_AGE = 110
MIN_MARR_AGE = 15
MIN_CHILD_AGE = 15
MAX_CHILD_AGE = 65
MAX_BAPTISM_DELAY = 1
MAX_BURIAL_DELAY = 1

BIRTH = "Birth"
DEATH = "Death"
MARRIAGE = "Marriage"
BURIAL = "Burial"
BAPTISM = "Baptism"

class Person:
    def __init__(self):
        self.events = []
        self.parents = []
        self.children = []

@dataclass
class Year:
    valuetype: str # "min", "max", "normal"
    value: int
    def __add__(self,years):
        if self.valuetype == "normal":
            self.value += years
    def __sub__(self,years):
        if self.valuetype == "normal":
            self.value -= years
#    def __lt__(self,other):
#        if self.valuetype == "min": return True
#        if self.valuetype == "max": return False

MIN = Year("min",0)
MAX = Year("max",0)

@dataclass
class Event:
    eventtype: str
    datetype: str
    year: int
    role: str = 'Primary'

def ymin(a,b):
    if a is MAX: 
        return b
    if b is MAX: 
        return a
    return min(a,b)

def ymax(a,b):
    if a is None: 
        return b
    if b is None: 
        return a
    return max(a,b)

def __empty_range(r):
    if r[0] == MIN or r[1] == MAX 
        return False
    return r[0].value > r[1].value

def __compute_overlap(r1,r2):
    return (ymax(r1[0],r2[0]),ymin(r1[1],r2[1]))
    
def __update_range(p,rangetype,low,high):                        
    current_range1 = p.estimates[rangetype]
    if __empty_range(current_range1):
        # already empty, warning already given
        return
    current_range = __compute_overlap(current_range1,(low,high))
    if __empty_range(current_range):
        print(p.gramps_id,": empty range",rangetype,current_range1,"&",(low,high),"->",current_range,file=sys.stderr)
        #assert not __empty_range(current_range)
    else:
        p.estimates[rangetype] = current_range
    
def __get_estimates(p):                        
    return (
        p.earliest_possible_birth_year,
        p.latest_possible_birth_year,
        p.earliest_possible_death_year,
        p.latest_possible_death_year
    )

def __update_estimates(p):                        
    p.earliest_possible_birth_year = p.estimates[BIRTH][0]
    p.latest_possible_birth_year = p.estimates[BIRTH][1]
    p.earliest_possible_death_year = p.estimates[DEATH][0]
    p.latest_possible_death_year = p.estimates[DEATH][1]

    if p.earliest_possible_birth_year:                        
        p.earliest_possible_death_year = ymax(p.earliest_possible_death_year,p.earliest_possible_birth_year)
    if p.earliest_possible_death_year:                        
        p.earliest_possible_birth_year = ymax(p.earliest_possible_death_year-MAX_AGE,p.earliest_possible_birth_year)
    if p.latest_possible_death_year:        
        p.latest_possible_birth_year = ymin(p.latest_possible_birth_year,p.latest_possible_death_year)
    if p.latest_possible_birth_year:        
        p.latest_possible_death_year = ymin(p.latest_possible_birth_year+MAX_AGE,p.latest_possible_death_year)

            
def __calculate_estimates1(p):
    """
    Update values based on personal events
    """
    p.earliest_possible_birth_year = MIN
    p.earliest_possible_death_year = MIN
    p.latest_possible_birth_year = MAX
    p.latest_possible_death_year = MAX
    p.estimates = {BIRTH:(MIN,MAX),DEATH:(MIN,MAX)}
    for e in p.events:
        if e.year is None: 
            continue
        if e.datetype == "exact":
            if e.eventtype == BIRTH and e.role == 'Primary': 
                __update_range(p,BIRTH,e.year,e.year)
            if e.eventtype == DEATH and e.role == 'Primary':
                __update_range(p,DEATH,e.year,e.year)
            if e.eventtype == BAPTISM and e.role == 'Primary':
                __update_range(p,BIRTH,e.year-MAX_BAPTISM_DELAY,e.year)
            if e.eventtype == BURIAL and e.role == 'Primary':
                __update_range(p,DEATH,e.year-MAX_BURIAL_DELAY,e.year)
            else:
                __update_range(p,DEATH,e.year,e.year+MAX_AGE)
            __update_range(p,BIRTH,e.year-MAX_AGE,e.year)

        if e.datetype == "after": 
            if e.eventtype == BIRTH  and e.role == 'Primary':
                __update_range(p,BIRTH,e.year,None)
            if e.eventtype == BAPTISM  and e.role == 'Primary':
                __update_range(p,BIRTH,e.year-MAX_BAPTISM_DELAY,None)
            __update_range(p,BIRTH,e.year-MAX_AGE,None)
            __update_range(p,DEATH,e.year,None)

        if e.datetype == "before": 
            if e.eventtype == MARRIAGE and e.role == 'Primary':
                __update_range(p,BIRTH,None,e.year-MIN_MARR_AGE)
            __update_range(p,BIRTH,None,e.year)
            __update_range(p,DEATH,None,e.year+MAX_AGE)

    __update_estimates(p)

def __calculate_estimates2(p):
    """
    Update values based on parent and children values
    """
    for par in p.parents:
        if par.earliest_possible_birth_year:
            __update_range(p,BIRTH,par.earliest_possible_birth_year+MIN_CHILD_AGE,None)
        if par.latest_possible_death_year:
            __update_range(p,BIRTH,None,par.latest_possible_death_year+1)   # a child may be born after father's death
        if par.latest_possible_birth_year:
            __update_range(p,BIRTH,None,par.latest_possible_birth_year+MAX_CHILD_AGE)
    for c in p.children:
        if c.earliest_possible_birth_year:
            __update_range(p,BIRTH,c.earliest_possible_birth_year-MAX_CHILD_AGE,None)
        if c.latest_possible_birth_year:
            __update_range(p,BIRTH,None,c.latest_possible_birth_year-MIN_CHILD_AGE)
        if c.earliest_possible_birth_year:
            __update_range(p,DEATH,c.earliest_possible_birth_year-1,None)  # father may have died before a child was born

    __update_estimates(p)


def calculate_estimates(personlist):
    for p in personlist:
        __calculate_estimates1(p)
    n = 0
    while True:
        print(n,len(personlist))
        personlist2 = set()
        for p in personlist:
            orig = __get_estimates(p)
            __calculate_estimates2(p)
            new = __get_estimates(p)
            if new != orig:
                for parent in p.parents:
                    personlist2.add(parent)
                for c in p.children:
                    personlist2.add(c)
        if len(personlist2) == 0: break
        personlist = personlist2
        n += 1
        if n > 10: break # prevent infinite loop
        
