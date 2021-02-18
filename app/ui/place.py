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

'''
Created on 13.3.2020

@author: jm
'''
from flask_security import current_user


def place_names_local_from_nodes(nodes):
    ''' Filter Name objects from a list of Cypher nodes.

        :param:     nodes     list of Neo4j Nodes
        :return:    list of selected PlaceName objects

        Create a list of place_bl.names with PlaceNames by following rules:
        1. Place_names using lang == current_user.language
        2. Place_names using lang == ""
        3. If none found, use the last Place_name
        Place_names using other languages are discarded

        nodes=[
            <Node id=305800 labels={'Place_name'} properties={'name': 'Helsingfors', 'lang': ''}>, 
            <Node id=305799 labels={'Place_name'} properties={'name': 'Helsinki', 'lang': 'sv'}>
        ]>
    '''
    from bl.place import PlaceName
    ret = []
    own_lang = []
    no_lang = []
    alien_lang = []
    for node in nodes:
        pn = PlaceName.from_node(node)
        if pn.lang == "":
            no_lang.append(pn)
            ##print(f"# - no lang {len(place_bl.names)} (Place_name {pn.uniq_id} {pn})")
        elif pn.lang == current_user.language:
            own_lang.append(pn)
            ##print(f"# - my lang (Place_name {pn.uniq_id} {pn})")
        else:
            alien_lang.append(pn)
            ##print(f"# - alien lang (Place_name {pn})")

    if own_lang:
        ret = own_lang
    elif no_lang:
        ret = no_lang
    else:
        ret = alien_lang
#     for pn in ret:
#         print(f"#  PlaceNames: {pn}")

    return ret


