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
#   Two-way fanchart using Vasco Asturiano's sunburst chart javascript module
#   (https://github.com/vasturiano/sunburst-chart).
#
#   Copyright (C) 2021  Heikki Roikonen

import urllib

from flask import render_template, request, redirect, url_for, flash, session as user_session #, send_from_directory, session, jsonify
from flask import send_file, json
from flask_security import login_required, roles_accepted, current_user
from flask_babelex import _ 

import collections
import shareds
import bl.person

from . import bp
from ui.user_context import UserContext
from pe.neo4j.readservice_tx import Neo4jReadServiceTx
from bl.person_reader import PersonReaderTx
from bl.base import Status
from bl.person_name import Name
from bp.gedcom.transforms.model.person_name import PersonName

MAX_ANCESTOR_LEVELS = 4
MAX_DESCENDANT_LEVELS = 3

MAX_TREE_ANCESTOR_LEVELS = 3
MAX_TREE_DESCENDANT_LEVELS = 3

readservice = Neo4jReadServiceTx(shareds.driver)

def get_fanchart_data(uuid):
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

    def get_person_for_id(uuid):
        """
        Database read access. Error handling needs an improvement here!
        """
        result = reader.get_person_data(uuid)
        if Status.has_failed(result):
            flash(f'{result.get("statustext","error")}', 'error')
        return result.get('person')

    def fanchart_from(person, size, descendant):
        """
        Format the data for fan/sunburst chart use.
        """
        all_first_names = []
        one_first_name = ''
        all_surnames = []
        one_surname = ''
        if person.names:
            if person.names[0].firstname:
                all_first_names = person.names[0].firstname.split()
                one_first_name = all_first_names[0]
            if person.names[0].surname:
                all_surnames = person.names[0].surname.split()
                one_surname = all_surnames[0] if len(all_surnames) > 0 else ''
        
        if person.death_high - person.birth_low >= 110: ## TEMP: FIND OUT HOW TO GET THE YEARS!
            death = ''
        else:
            death = f'{person.death_high}'
        return {
            'name': one_first_name +
                    (f' {one_surname}' if size > 0.2 else '') +
                    (f' {person.birth_low}' if size > 0.4 else ''),
            'color': gender_color(person.sex, descendant),
            'tooltipContent': f'{person.names[0].firstname} {person.names[0].surname}' +
                f' {person.birth_low}-{death}',
            'uuid': person.uuid
        }

    def build_parents(uuid, size, level = 1):
        """
        Recurse to ancestors, building a data structure for fanchart.
        """
        # Fill in basic data from current person
        person = get_person_for_id(uuid)
        node = fanchart_from(person, size, descendant = False)

        if person.families_as_child and level < MAX_ANCESTOR_LEVELS:  # continue recursion?

            dad = person.families_as_child[0].father
            if dad:
                dads = build_parents(dad.uuid, size/2, level + 1)
            else:
                dads = {'color': 'white', 'size': str(size/2), 'uuid': None}

            mom = person.families_as_child[0].mother
            if mom:
                moms = build_parents(mom.uuid, size/2, level + 1)
            else:
                moms = {'color': 'white', 'size': str(size/2), 'uuid': None}
            node['children'] = [dads, moms]

        else:
            node['size'] = str(size)     # leaf node, others should have no size
            
        return node
    
    def build_children(uuid, size, level = 1):
        """
        Recurse to descendants, building a data structure for fanchart.
        """
        # Fill in basic data from current person
        person = get_person_for_id(uuid)
        node = fanchart_from(person, size, descendant = True)

        if person.families_as_parent and level < MAX_DESCENDANT_LEVELS:  # continue recursion?

            child_count = 0
            for fx in person.families_as_parent:
                child_count += len(fx.children)

            if child_count == 0:
                node['size'] = str(size)     # leaf node, others should have no size
            else:
                node['children'] = []
                person.families_as_parent.sort(reverse = True,
                                               key = lambda x: x.dates.date1.value())
                for fx in person.families_as_parent:
                    fx.children.sort(reverse = True, key = lambda x: x.birth_low)
                    for cx in fx.children:
                        node['children'].append(
                            build_children(cx.uuid, size/child_count, level + 1))

        else:
            node['size'] = str(size)     # leaf node, others should have no size

        return node
    
    # Set up the database access.
    u_context = UserContext(user_session, current_user, request)
    with Neo4jReadServiceTx(shareds.driver) as readservice:
        reader = PersonReaderTx(readservice, u_context)

        # Gather all required data in two directions from the central person. Data structure used in both is a
        # recursive dictionary with unlimited children, for the Javascript sunburst chart by Vasco Asturiano
        # (https://vasturiano.github.io/sunburst-chart/)
        ancestors = build_parents(uuid, 1)
        descendants = build_children(uuid, 1)
    
    # Merge the two sunburst chart data trees to form a single two-way fan chart.
    fanchart = ancestors
    fanchart.pop('size', None)  # make sure the root node has no size attribute (will have if no ancestors)
    if 'children' in descendants.keys():    # has descendants?
        if 'children' in ancestors.keys():  # has ancestors?
            fanchart['children'] = ancestors['children'] + descendants['children']
        else:
            fanchart['children'] = descendants['children']
            # No ancestors: make empty quarters to occupy parents' slots (otherwise descendants end up in east!)
            fanchart['children'].insert(0, {'size': str(0.5), 'color': 'white', 'uuid': None})
            fanchart['children'].insert(0, {'size': str(0.5), 'color': 'white', 'uuid': None})
    else:
        # If no descendants, make empty southern hemisphere
        fanchart['children'].insert(2, {'size': str(1), 'color': 'white', 'uuid': None})
    
#     # The sectors are drawn anticlockwise, starting from North. To get the ancestors to occupy the
#     # Northern hemisphere, we need to move the first node on top level list (father) to end of list.
#     if 'children' in fanchart.keys():
#         fanchart['children'].append(fanchart['children'].pop(0))
    
    return fanchart
    
def get_treechart_data(uuid):
    '''
    Get the spouse(s) and a number of ancestor and descendant generations for the given central id.
    '''
    def get_person_for_id(uuid):
        """
        Database read access. Error handling needs an improvement here!
        """
        result = reader.get_person_data(uuid)
        if Status.has_failed(result):
            flash(f'{result.get("statustext","error")}', 'error')
        return result.get('person')

    def treechart_from(items, person, spouses = True):
        """
        Format the data for treechart use.
        """
        # Create a dictionary that allows appending to non-existing keys to simplify code
        node = collections.defaultdict(list)

        all_first_names = []
        one_first_name = ''
        all_surnames = []
        one_surname = ''
        if person.names:
            if person.names[0].firstname:
                all_first_names = person.names[0].firstname.split()
                one_first_name = all_first_names[0]
            if person.names[0].surname:
                all_surnames = person.names[0].surname.split()
                one_surname = all_surnames[0] if len(all_surnames) > 0 else ''
        
        if person.death_high - person.birth_low >= 110: ## TEMP: FIND OUT HOW TO GET THE YEARS!
            death = ''
        else:
            death = f'{person.death_high}'

        node['title'] = f'{one_first_name} {one_surname}'
        node['description'] = f'{person.names[0].firstname} {person.names[0].surname} {person.birth_low}-{death}'
        node['id'] = person.uuid
        node['image'] = ''

        # Handle the spouse(s)
        return (items, node)

    def build_parents(items, uuid, level = 1):
        """
        Recurse to ancestors, building a data structure for treechart.
        """
        person = get_person_for_id(uuid)
        (items, node) = treechart_from(items, person)

        # Check whether to continue recursion
        if person.families_as_child and level < MAX_TREE_ANCESTOR_LEVELS:

            dad = person.families_as_child[0].father
            if dad:
                node['parents'].append(dad.uuid)
                dad = get_person_for_id(dad.uuid)   # get the families
                (items, nodedad) = treechart_from(items, dad)
                (items, nodedad, dad) = build_parents(items, dad.uuid, level + 1)
                items.append(nodedad)

            mom = person.families_as_child[0].mother
            if mom:
                node['parents'].append(mom.uuid)
                mom = get_person_for_id(mom.uuid)   # get the families
                (items, nodemom) = treechart_from(items, mom)
                (items, nodemom, mom) = build_parents(items, mom.uuid, level + 1)
                items.append(nodemom)

        items.append(node)
        return (items, node, person)
    
    def build_children(items, node, person, level = 1):
        """
        Recurse to descendants, building a data structure for treechart. Skip the current person.
        """
        # Check whether to continue recursion
        if person.families_as_parent and level < MAX_TREE_DESCENDANT_LEVELS:

            # Go through all this persons' families, sorted by marriage date
            person.families_as_parent.sort(key = lambda x: x.dates.date1.value())
            familycounter = 0
            childcounter = 0
            for fx in person.families_as_parent:
                familycounter += 1
                if fx.father and fx.father.uuid != person.uuid:
                    node['spouses'].append(fx.father.uuid)      # create the linking
                    (items, node1) = treechart_from(items, fx.father, spouses = False)  # create the (single) node
                    if len(person.families_as_parent) > 1 and familycounter > 1:
                        node1['placementType'] = 3   # AdviserPlacementType.Right for second husband etc.
                    else:
                        node1['placementType'] = 7   # AdviserPlacementType.Left
                    node1['relativeItem'] = person.uuid
                    node1['position'] = familycounter
                    items.append(node1)

                if fx.mother and fx.mother.uuid != person.uuid:
                    node['spouses'].append(fx.mother.uuid)
                    (items, node2) = treechart_from(items, fx.mother, spouses = False)
                    if len(person.families_as_parent) > 1 and familycounter == 1:
                        node2['placementType'] = 7   # AdviserPlacementType.Left for the first wife
                    else:
                        node2['placementType'] = 3   # AdviserPlacementType.Right
                    node2['relativeItem'] = person.uuid
                    node2['position'] = familycounter
                    items.append(node2)

                # Go through all the children, sorted by birthdate
                fx.children.sort(key = lambda x: x.birth_low)
                for cx in fx.children:

                    # Collect this child's data and add linkage to the parents IDs
                    child = get_person_for_id(cx.uuid)
                    (items, node) = treechart_from(items, child)
                    for px in child.families_as_child:
                        node['parents'].append(px.father.uuid)
                        node['parents'].append(px.mother.uuid)

                    # Set up the fields needed for positioning siblings from oldest to youngest
                    childcounter += 1
                    if childcounter == 1:
                        firstchild = cx.uuid
                    else:
                        node['placementType'] = 3   # AdviserPlacementType.Right
                        node['relativeItem'] = firstchild
                        node['position'] = childcounter

                    # Append current node to the list and recurse to its children
                    items.append(node)
                    items = build_children(items, node, child, level + 1)

        return items

    # Set up the database access.
    u_context = UserContext(user_session, current_user, request)

    with Neo4jReadServiceTx(shareds.driver) as readservice:
        reader = PersonReaderTx(readservice, u_context)

        # Gather all required data in two directions from the central person. Data structure used in
        # both is a list, as defined by the BasicPrimitives diagram (https://www.basicprimitives.com/)
        (treechart, node, person) = build_parents([], uuid)
        treechart = build_children(treechart, node, person)
    
    return treechart

@bp.route('/graph', methods=['GET'])
@login_required
@roles_accepted('audit')
def graph_home(uuid=None):
    uuid = request.args.get('uuid', None)
    fanchart = get_fanchart_data(uuid)
    return render_template('/graph/layout.html', fanchart_data=json.dumps(fanchart))


@bp.route('/tree', methods=['GET'])
@login_required
@roles_accepted('audit')
def tree_test(uuid=None):
    uuid = request.args.get('uuid', None)
    treechart = get_treechart_data(uuid)
    return render_template('/graph/tree_layout.html', treechart_data=json.dumps(treechart))