#!/usr/bin/python
# -*- coding:utf-8 -*-
'''
  hierarkiapuun luonti kannasta
Created on 8.9.2017
@author: jm
'''
import sys
from neo4j import GraphDatabase, basic_auth
import treelib

class DbTree():
    """ Builds a tree structure in memory by Neo4j query and offers
        services to access it
    """

    def __init__(self, driver, query=None, field_id='name', field_type='type'):
        """ Defines a Neo4j query to access database data as a tree structure.
    
            Query result must have the following mandatory fields:
                nodes   terminal nodes
                r       relation between terminal nodes
                lv      lenght of the relation SIZE(r); 
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
        with self.driver.session() as session:
            result = session.run(self.query, locid=int(node_id))
            return [(record["nodes"], record["lv"], record["r"]) 
                    for record in result]


    def load_to_tree_struct(self, node_id):
        """ Build a tree structure in memory from Neo4j query result
            about self.node_id
    
            Result must have the following mandatory fields:
                nodes   terminal nodes
                r       relation between terminal nodes
                lv      lenght of the relation SIZE(r); 
                        negative, if upwards to the root of the tree
            Other field names from arguments:
                name_field_name  node instance display name
                type_field_name  node instance type
                
        """
        self.tree = treelib.Tree()
        nl = {}
        nl[0] = 'root'
        nstack = []
        rl = {}
        # Juurisolu 0 mahdollistaa solun lisäämisen ylimmän varsinaisen solun
        # yläpuolelle
        self.tree.create_node('', 0)
        nstack.append((0, "root", "", -9999))
    
        for nodes, level, relations in self._get_tree_branches(node_id):
            # The result has all nodes in the relation and their connections
            # Tuloksessa on kaikki ko. relaatioon osallistuvat solut ja niiden
            # väliset yksittäiset yhteydet
            for node in nodes:
                if not node.id in nl:
                    nl[node.id] = node[self.name_field_name]            #["pname"]
                    nstack.append((node.id, node[self.type_field_name], #["type"], 
                                   node[self.name_field_name],          #["pname"], 
                                   level))
            for rel in relations:
                # Walk thru all (start)-->(end) relations
                if not rel.id in rl:
                    rl[rel.id] = rel.end
                    nid, ntype, nname, lv = nstack.pop()
                    if not nid:
                        raise ValueError("Hierarchy tree error")
                    if len(rl) == 1:    # Ensimmäinen solmu rootin alle
                        nid1, ntype1, nname1, _lv1 = nstack.pop()
                        rl[0] = rel.end
                        print("create_node('{}', '{}', parent={}, data={})".\
                              format(nname1, nid1, 0, {'type':ntype1}))
                        self.tree.create_node(nname1, nid1, parent=0, 
                                              data={self.type_field_name:ntype1})
                    if lv > 0:
                        parent = rel.end
                    else:
                        parent = self.tree.parent(rel.start).identifier
                    # Add the new node by side on current; then move current under that 
                    # Lisätään uusi solu ensin nykyisen rinnalle ja sitten siirretään nykyinen uuden alle
                    print("create_node('{}', '{}', parent={}, data={})".\
                          format(nname, nid, parent, {'type':ntype}))
                    self.tree.create_node(nname, nid, parent=parent, 
                                          data={self.type_field_name:ntype})
                    if lv < 0:
                        print("  move_node('{}', '{}')".format(rel.start, nid))
                        self.tree.move_node(rel.start, nid)
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
                if node.bpointer in nl:
                    lv = nl[node.bpointer] + 1
                else:
                    lv = lv + 1
                    nl[node.identifier] = lv
                fill = ''.join([ "       " for _n in range(lv-1)])
                print("({}){} {:5d}<-{:5d} {} ".format(lv, fill, 
                      node.bpointer, node.identifier, node.tag))


if __name__ == '__main__':
    # Valinnainen argumentti: id of a place
    if len(sys.argv) <= 1:
        locid = 21773
    else:
        locid = int(sys.argv[1])
    print ("paikka {}".format(locid))

    # Connect db
    host = "bolt:localhost:7687"
    driver = GraphDatabase.driver(host, auth=basic_auth("neo4j", "2000Neo4j"))

    # Suoritetaan haku tietokannasta: paikkaan locid liittyvät
    # solmut ja relaatiot
    query = """
MATCH x= (p:Place)<-[r:HIERARCY*]-(i:Place) WHERE ID(p) = $locid
    RETURN NODES(x) AS nodes, SIZE(r) AS lv, r
    UNION
MATCH x= (p:Place)-[r:HIERARCY*]->(i:Place) WHERE ID(p) = $locid
    RETURN NODES(x) AS nodes, SIZE(r)*-1 AS lv, r
"""
    t = DbTree(driver, query, 'pname', 'type')
    # Luetaan tiedot muistinvaraiseen puurakenteeseen
    t.load_to_tree_struct(locid)
    if t.tree.depth() == 0:
        # Vain ROOT-solmu: Tällä paikalla ei ole hierarkiaa. 
        # Hae oman paikan tiedot ilman yhteyksiä
        query = """
MATCH (p:Place) WHERE ID(p) = $locid
RETURN p.type AS type, p.pname AS name
"""
        with driver.session() as session:
            result = session.run(query, locid=int(locid))
            record = result.single()
            t.tree.create_node(record["name"], locid, parent=0, 
                                      data={'type': record["type"]})

    print(t.tree)
    t.print_tree()
#     print(t.to_json())
