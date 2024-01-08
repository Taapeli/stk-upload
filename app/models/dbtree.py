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

'''
Creating Place hierarchy tree from database Nodes
Created on 8.9.2017
@author: jm
'''
import sys
from neo4j import GraphDatabase, basic_auth
import treelib

import logging
logger = logging.getLogger('stkserver')

class DbTree():
    """ Builds a tree structure in memory by Neo4j query and offers
        services to access it
    """

    def __init__(self, driver, query=None, field_id='name', field_type='type'):
        """ Defines a Neo4j query to access database data as a tree structure.
    
            Query result must have the following mandatory fields:
                nodes   terminal nodes
                r       relation between terminal nodes
                lv      length of the relation SIZE(r); 
                        negative, if upwards towards the root of the tree
            Other field names form arguments:
                name_field_name  node instance display name
                type_field_name  node instance type
                
        """
        self.driver = driver
        self.query = query
        self.name_field_name = field_id
        self.type_field_name = field_type


    def _get_tree_branches(self, node_id):
        """ Example: Result for query for -
             ── Venäjä
                └── Inkeri (active node_id)
                    └── Tuutari
                        └── Nurkkala
            ╒══════════════════════════════╤════╤═══════╕
            │"nodes"                       │"lv"│"r"    │
            ╞══════════════════════════════╪════╪═══════╡
            │[{"pname":"Inkeri","change":14│"1" │[{}]   │ 2 nodes
            │96429798,"handle":"_d         │    │       │ 1 relation
            │9c25aa5af17a80cc1af6a8533b","i│    │       │
            │d":"P0054","type":"State"},{"p│    │       │
            │name":"Tuutari","change":1496 │    │       │
            │431999,"handle":"_d9c2│    │       │
            │5abb00881f87b8bdbda5eb","id":"│    │       │
            │P0055","type":"Region"}]      │    │       │
            ├──────────────────────────────┼────┼───────┤
            │[{"pname":"Inkeri","change":14│"2" │[{},{}]│ 3 nodes
            │96429798,"handle":"_d         │    │       │ 2 relations
            │9c25aa5af17a80cc1af6a8533b","i│    │       │
            │d":"P0054","type":"State"},{"p│    │       │
            │name":"Tuutari","change":1496 │    │       │
            │431999","handle":"_d9c2       │    │       │
            │5abb00881f87b8bdbda5eb","id":"│    │       │
            │P0055","type":"Region"},{"pnam│    │       │
            │e":"Nurkkala","change":150030 │    │       │
            │0897,"handle":"_d9c26f        │    │       │
            │b0acf5873995a02ac6efe","id":"P│    │       │
            │0056","type":"Village"}]      │    │       │
            ├──────────────────────────────┼────┼───────┤
            │[{"pname":"Inkeri","change":1 │"-1"│[{}]   │ 2 nodes
            │496429798,"handle":"_d        │    │       │ 1 relation
            │9c25aa5af17a80cc1af6a8533b","i│    │       │
            │d":"P0054","type":"State"},{"p│    │       │
            │name":"Venäjä","change":14996 │    │       │
            │85324,"handle":"_d7917        │    │       │
            │3305b956899544","id":"P0024","│    │       │
            │type":"Country"}]             │    │       │
            └──────────────────────────────┴────┴───────┘
        """
        self.node_id = node_id
        with self.driver.session(default_access_mode='READ') as session:
            result = session.run(self.query, locid=node_id)
            return [(record["nodes"], record["lv"], record["r"]) 
                    for record in result]


    def load_to_tree_struct(self, node_id):
        """ Build a tree structure in memory from Neo4j query result
            about a Place with id=self.node_id
    
            Result must have the following mandatory fields:
                nodes       terminal nodes
                relations   list of relations so that node with id=rel.end is 
                            the parent of node with id=rel.start
            Other field names from arguments:
                name_field_name  node instance display name
                type_field_name  node instance type
                
        """
        self.tree = treelib.Tree()
        self.tree.create_node('', 0)  # an initial parent for all nodes
    
        hierarchy_result = self._get_tree_branches(node_id)
        # first create all nodes (under initial parent)
        for nodes, _level, relations in hierarchy_result:
            for node in nodes:
                # Example: <Node element_id='4:18f484ec-c98a-4e88-9acb-165fdd5a3216:1110156' 
                #    labels=frozenset({'Place'})
                #    properties={'coord': [61.203655, 24.06065], 'iid': 'P-32n6',
                #        'pname': 'Voipaalan kartano', 'change': 1693326647, 
                #        'handle': '_ef04df92a173342c2fdd249d390@2311052', 
                #        'id': 'P0009', 'type': 'Farm', 'attrs': ''}>
                iid = node.get('iid')
                if not self.tree.contains(iid):
                    self.tree.create_node(node.get(self.name_field_name), 
                                          iid, 
                                          parent=0, 
                                          data={self.type_field_name:node.get(self.type_field_name),
                                                'iid':iid})
    
        # then move all nodes under correct parent
        for nodes, _level, relations in hierarchy_result:
            for rel in relations:
                start = rel.start_node.get("iid")
                end = rel.end_node.get("iid")
                self.tree.move_node(start, end)
        return self.tree





    def print_tree(self):
        """ Test: Show tree structure
        """
        nl = {}
        lv = 0
        fill = ""
        nodes = [self.tree[node] for node in self.tree.expand_tree(mode=self.tree.DEPTH)]
        for node in nodes:
            if node.bpointer != None:
                #TODO: Call to deprecated function "bpointer"; use "node.predecessor" instead.
                # With treelib 1.6.4
                # ueing node.predecessor("a431f142-7bfd-11ee-8d6f-2bf86e8618f5")does not help!
                if node.bpointer in nl:
                    lv = nl[node.bpointer] + 1
                else:
                    lv = lv + 1
                    nl[node.identifier] = lv
                fill = ''.join([ "       " for _n in range(lv-1)])
                print("({}){} {}<-{} {} ".format(lv, fill, 
                      node.bpointer, node.identifier, node.tag))


if __name__ == '__main__':
    # Valinnainen argumentti: id of a place
    if len(sys.argv) <= 1:
        locid = "P-32n6"
    else:
        locid = sys.argv[1]
    print ("paikka {}".format(locid))

    # Connect db
    host = "bolt:localhost:7687"
    driver = GraphDatabase.driver(host, auth=basic_auth("neo4j", "2000Neo4j"))

    # Suoritetaan haku tietokannasta: paikkaan locid liittyvät
    # solmut ja relaatiot
    query = """
MATCH x= (p:Place)<-[r:IS_INSIDE*]-(i:Place) WHERE p.iid = $locid
    RETURN NODES(x) AS nodes, SIZE(r) AS lv, r
    UNION
MATCH x= (p:Place)-[r:IS_INSIDE*]->(i:Place) WHERE p.iid = $locid
    RETURN NODES(x) AS nodes, SIZE(r)*-1 AS lv, r
"""
    t_test = DbTree(driver, query, 'pname', 'type')
    # Luetaan tiedot muistinvaraiseen puurakenteeseen
    t_test.load_to_tree_struct(locid)
    if t_test.tree.depth() == 0:
        # Vain ROOT-solmu: Tällä paikalla ei ole hierarkiaa. 
        # Hae oman paikan tiedot ilman yhteyksiä
        query = """
MATCH (p:Place) WHERE p.iid = $locid
RETURN p.type AS type, p.pname AS name
"""
        with driver.session() as session:
            result = session.run(query, locid=int(locid))
            record = result.single()
            t_test.tree.create_node(record["name"], locid, parent=0, 
                                      data={'type': record["type"]})

    print(t_test.tree)
    t_test.print_tree()
#     print(t_test.to_json())
