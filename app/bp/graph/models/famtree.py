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
#
# Copyright 2019–2020 Observable, Inc.
#
# Permission to use, copy, modify, and/or distribute this software for any
# purpose with or without fee is hereby granted, provided that the above
# copyright notice and this permission notice appear in all copies.

# THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
# WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
# MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
# ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
# WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
# ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
# OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.

# Copyright (C) 2021  Heikki Roikonen

from flask import render_template, request, flash, session as user_session
from flask import json  # , send_file
from flask_security import login_required, roles_accepted, current_user

from ui.user_context import UserContext
from bl.person import PersonReader
from bl.base import Status

MAX_ANCESTOR_LEVELS = 4
MAX_DESCENDANT_LEVELS = 3


class FamTree:
    def gender_color(self, sex, descendant):
        """
        Given the gender code according to ISO 5218, returns a color for famtree.
        """
        if descendant:
            descendant_colors = {
                0: "lightgrey",  # ISO 5218: 0 = Not known
                1: "lightskyblue",  # ISO 5218: 1 = Male
                2: "lightpink",  # ISO 5218: 2 = Female
                9: "lightyellow",  # ISO 5218: 9 = Not applicable
            }
            return descendant_colors.get(
                sex, "white"
            )  # white if value is not in ISO 5218
        else:
            ancestor_colors = {
                0: "lightgrey",  # ISO 5218: 0 = Not known
                1: "lightsteelblue",  # ISO 5218: 1 = Male
                2: "thistle",  # ISO 5218: 2 = Female
                9: "lightyellow",  # ISO 5218: 9 = Not applicable
            }
            return ancestor_colors.get(
                sex, "white"
            )  # white if value is not in ISO 5218

    def famtree_data(self, person_attributes, descendant):
        """
        Format the data for fan/sunburst chart use.
        """
        def mk_int(s):
            """
            Convert string to integer, empty string to zero.
            """
            s = s.strip()
            return int(s) if s else 0

        names = person_attributes["sortname"].split("#")
        birth, death = "", ""
        for ev in person_attributes["events"]:
            if len(ev) == 2 and ev[0] == "Birth" and ev[1] != None:
                birth = f"{ev[1]}"
            elif len(ev) == 2 and ev[0] == "Death" and ev[1] != None:
                death = f"{ev[1]}"
        return {
            "name": f"{names[1]} {names[0]}",
            "color": self.gender_color(person_attributes["gender"], descendant),
            "birth": mk_int(birth),
            "death": mk_int(death),
            "years": f"{birth}-{death}" if birth + death != "" else "",
            "gender": person_attributes["gender"],
            "title": f"{names[1]} {names[0]}, {birth}-{death}",
            "uuid": person_attributes["uuid"],
            "too_new": person_attributes["too_new"]
        }

    def build_parents(self, u_context, uniq_id, privacy, level=1):
        """
        Recurse to ancestors, building a data structure for famtree.
        """

        with PersonReader("read", u_context) as service:
            result = service.get_parents(uniq_id, privacy)

        parents = []
        result.sort(key=lambda x: x["gender"])
        for par in result:
            node = self.famtree_data(par, descendant=False)
            if level < MAX_ANCESTOR_LEVELS:  # continue recursion?
                node["parents"] = self.build_parents(
                    u_context, par["uniq_id"], privacy, level + 1
                )
            parents.append(node)
        return parents

    def build_children(self, u_context, uniq_id, privacy, level=1):
        """
        Recurse to descendants, building a data structure for famtree.
        """

        def b_year(x):
            """
            Make sure no indexing errors occur in fetching potentially missing birth year.
            """
            if "events" in x:
                for ev in x["events"]:
                    if ev[0] == "Birth":
                        return ev[1]
            return (
                9999  # no birth year given, sort after siblings with known birth years
            )

        with PersonReader("read", u_context) as service:
            result = service.get_children(uniq_id, privacy)

        children = []
        result.sort(reverse=True, key=lambda x: b_year(x))
        for chi in result:
            node = self.famtree_data(chi, descendant=True)
            if level < MAX_DESCENDANT_LEVELS:  # continue recursion?
                node["children"] = self.build_children(
                    u_context, chi["uniq_id"], privacy, level + 1
                )
            children.append(node)
        return children

    def get(self, uuid):
        """
        Fetch data from the ancestors and descendants of the giving uuid, creating a data
        structure that can be fed to the sunburst chart Javascript component for creating
        a simple two-way famtree.
        """
        # Set up the database access.
        u_context = UserContext(user_session, current_user, request)
        privacy = u_context.context == u_context.ChoicesOfView.COMMON

        # Fill in basic data from current person
        with PersonReader("read", u_context) as service:
            result = service.get_person_minimal(uuid, privacy)

        if len(result) == 0:
            return ""

        for person in result:
            famtree = self.famtree_data(person, descendant=True)
            uniq_id = person["uniq_id"]

        # Gather all required data in two directions from the central person. Data structure used in both is a
        # recursive dictionary with unlimited children, for the Javascript sunburst chart by Vasco Asturiano
        # (https://vasturiano.github.io/sunburst-chart/)
        famtree["parents"] = self.build_parents(u_context, uniq_id, privacy)
        famtree["children"] = self.build_children(u_context, uniq_id, privacy)

        return famtree
