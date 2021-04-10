#   Isotammi Geneological Service for combining multiple researchers' results.
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
#   Two-way fanchart adapted from Vasco Asturiano's sunburst chart javascript module
#   (https://github.com/vasturiano/sunburst-chart).
#
#   Copyright (C) 2021  Heikki Roikonen

from flask import render_template, request, flash, session as user_session
from flask import json #, send_file
from flask_security import login_required, roles_accepted, current_user

#from . import bp
from ui.user_context import UserContext
from bl.person import PersonReader
from bl.base import Status

MAX_ANCESTOR_LEVELS = 4
MAX_DESCENDANT_LEVELS = 3

class FanChart:

    def get(self, uuid):
        '''
        Fetch data from the ancestors and descendants of the giving uuid, creating a data
        structure that can be fed to the sunburst chart Javascript component for creating
        a simple two-way fanchart.
        '''
        def gender_color(sex, descendant):
            """
            Given the gender code according to ISO 5218, returns a color for fanchart.
            """
            ancestor_colors = {
                0: 'lightgrey',         # ISO 5218: 0 = Not known
                1: 'lightsteelblue',    # ISO 5218: 1 = Male
                2: 'thistle',           # ISO 5218: 2 = Female
                9: 'lightyellow'        # ISO 5218: 9 = Not applicable
            }
            descendant_colors = {
                0: 'lightgrey',         # ISO 5218: 0 = Not known
                1: 'lightskyblue',      # ISO 5218: 1 = Male
                2: 'lightpink',         # ISO 5218: 2 = Female
                9: 'lightyellow'        # ISO 5218: 9 = Not applicable
            }
            if descendant:
                return descendant_colors.get(sex, 'white') # white if value is not in ISO 5218
            else:
                return ancestor_colors.get(sex, 'white') # white if value is not in ISO 5218

        def fanchart_data(person_attributes, descendant):
            """
            Format the data for fan/sunburst chart use.
            """
            names = person_attributes['sortname'].split("#")
            if len(person_attributes['events']) > 0 and person_attributes['events'][0][1] != None:
                birth = f"{person_attributes['events'][0][1]}"
            else:
                birth = ''
            if len(person_attributes['events']) > 1 and person_attributes['events'][0][1] != None:
                death = f"{person_attributes['events'][1][1]}"
            else:
                death = ''
            return {
                'name': f'{names[1]} {names[0]}',
                'color': gender_color(person_attributes['gender'], descendant),
                'years': f'{birth}-{death}' if birth+death != '' else '',
                'gender': person_attributes['gender'],
                'title': f'{names[1]} {names[0]}, {birth}-{death}',
                'uuid': person_attributes['uuid']
            }

        def build_parents(uniq_id, size, level=1):
            """
            Recurse to ancestors, building a data structure for fanchart.
            """

            with PersonReader("read", u_context) as service:
                result = service.get_parents(uniq_id)

            par_count = max(len(result), 2)         # prepare for any number, but space the chart for 2
            parents = []
            result.sort(key = lambda x: x['gender'])
            for par in result:
                node = fanchart_data(par, descendant=False)
                if level >= MAX_ANCESTOR_LEVELS:    # do not continue recursion?
                    node['size'] = size/par_count   # leaf node, others must have no size
                else:
                    ancest = build_parents(par['uniq_id'], size/par_count, level + 1)
                    if len(ancest) == 0:
                        node['size'] = size/par_count   # leaf node, others must have no size
                    else:
                        if len(ancest) == 1:                # need empty space for missing parent?
                            node['size'] = size/par_count/2 # "half-leaf" node, half the size
                        node['children'] = ancest
                parents.append(node)
            return parents
        
        def build_children(uniq_id, size, level=1):
            """
            Recurse to descendants, building a data structure for fanchart.
            """
            def b_year(x):
                """
                Make sure no indexing errors occur in fetching potentially missing birth year.
                """
                if 'events' in x and len(x['events']) > 1:
                    birth = x['events'][0]
                    return birth[1] if len(birth) > 1 else 0
                else:
                    return 0

            with PersonReader("read", u_context) as service:
                result = service.get_children(uniq_id)

            chi_count = len(result)
            children = []
            result.sort(reverse = True, key = lambda x: b_year(x))
            for chi in result:
                node = fanchart_data(chi, descendant=True)
                if level >= MAX_DESCENDANT_LEVELS:  # do not continue recursion?
                    node['size'] = size/chi_count   # leaf node, others should have no size
                else:
                    descend = build_children(chi['uniq_id'], size/chi_count, level + 1)
                    if len(descend) == 0:
                        node['size'] = size/chi_count   # leaf node, others must have no size
                    else:
                        node['children'] = descend
                children.append(node)
            return children
    
        # Set up the database access.
        u_context = UserContext(user_session, current_user, request)

        # Fill in basic data from current person
        with PersonReader("read", u_context) as service:
            result = service.get_person_minimal(uuid)

        if len(result) == 0:
            return ''
    
        for person in result:
            fanchart = fanchart_data(person, descendant=True)
            uniq_id = person['uniq_id']

        # Gather all required data in two directions from the central person. Data structure used in both is a
        # recursive dictionary with unlimited children, for the Javascript sunburst chart by Vasco Asturiano
        # (https://vasturiano.github.io/sunburst-chart/)
        ancestors = build_parents(uniq_id, 1)
        descendants = build_children(uniq_id, 1)
        
        # Merge the two sunburst chart data trees to form a single two-way fan chart.
        # This step involves handling several special cases related to the fact that the data structure (inherited
        # from sunburst chart) does not partition the chart in two separate halves for ancestors and descendants.
        fanchart.pop('size', None)  # make sure the root node has no size attribute (will have if no ancestors)
        if len(descendants) > 0:    # has descendants?
            if len(ancestors) > 0:  # has ancestors?
                fanchart['children'] = ancestors + descendants
                # If only one parent, create an empty quadrant (only needed if the root node has one parent)
                if len(ancestors) == 1:
                    slot = 2 - ancestors[0]['gender'] # For father, yields slot 1; for mother, slot 0.
                    fanchart['children'].insert(slot, {'size': 0.5, 'color': 'white', 'uuid': None})
            else:
                fanchart['children'] = descendants
                # No ancestors: make two empty quarters to occupy parents' slots (otherwise descendants end up in east!)
                fanchart['children'].insert(0, {'size': 0.5, 'color': 'white', 'uuid': None})   # Can't combine these two!
                fanchart['children'].insert(0, {'size': 0.5, 'color': 'white', 'uuid': None})   # One will be moved next.
        else:
            fanchart['children'] = ancestors
            # If only one parent, create an empty quadrant (only needed if the root node has one parent)
            if len(ancestors) == 1:
                slot = 2 - ancestors[0]['gender'] # For father, yields slot 1; for mother, slot 0.
                fanchart['children'].insert(slot, {'size': 0.5, 'color': 'white', 'uuid': None})
            # No descendants, create empty southern hemisphere
            fanchart['children'].append({'size': 1, 'color': 'white', 'uuid': None})

        # The sectors are drawn anticlockwise, starting from North. To get the ancestors to occupy the
        # Northern hemisphere, we need to move the first node on top level list (father) to end of list.
        if 'children' in fanchart.keys():
            fanchart['children'].append(fanchart['children'].pop(0))

        return fanchart
        