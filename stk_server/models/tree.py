#!/usr/bin/python
# -*- coding:utf-8 -*-
'''
  Demo-ohjelma: Kokeillaan paikkahierarkian lukemista
Created on 8.9.2017
@author: jm
'''
import sys
from neo4j.v1 import GraphDatabase, basic_auth
import treelib

class Tree():
    """ Builds a tree structure in memory by Neo4j query and offers
        services to access it
    """

    def __init__(self, query=None, field_id='name', field_type='type'):
        """ Defines a Neo4j query to access database data as a tree structure.
    
            Query result must have the following mandatory fields:
                nodes   terminal nodes
                r       relation between terminal nodes
                lv      lenght of the relation SIZE(r); 
                        negative, if upwards to the root of the tree
            Other field names form arguments:
                field_id    node instance display name
                field_type  node instance type
                
        """
        if query:
            self.query = query
        else:
            # Default example query gets place hierarcy
            self.query = """
MATCH x= (p:Place)<-[r:HIERARCY*]-(i:Place) WHERE ID(p) = $locid
    RETURN NODES(x) AS nodes, SIZE(r) AS lv, r
    UNION
MATCH x= (p:Place)-[r:HIERARCY*]->(i:Place) WHERE ID(p) = $locid
    RETURN NODES(x) AS nodes, SIZE(r)*-1 AS lv, r
"""
        self.field_id = field_id
        self.field_type = field_type


    def _get_db_connections(self, node_id):
        """ Example: Kyselyn tulos, kun puurakenne on
             ── Venäjä
                └── Inkeri (kysytty node_id)
                    └── Tuutari
                        └── Nurkkala
            ╒══════════════════════════════╤════╤═══════╕
            │"nodes"                       │"lv"│"r"    │
            ╞══════════════════════════════╪════╪═══════╡
            │[{"pname":"Inkeri","change":"1│"1" │[{}]   │ 2 nodea ja
            │496429798","gramps_handle":"_d│    │       │ 1 yhteys
            │9c25aa5af17a80cc1af6a8533b","i│    │       │
            │d":"P0054","type":"State"},{"p│    │       │
            │name":"Tuutari","change":"1496│    │       │
            │431999","gramps_handle":"_d9c2│    │       │
            │5abb00881f87b8bdbda5eb","id":"│    │       │
            │P0055","type":"Region"}]      │    │       │
            ├──────────────────────────────┼────┼───────┤
            │[{"pname":"Inkeri","change":"1│"2" │[{},{}]│ 3 nodea ja
            │496429798","gramps_handle":"_d│    │       │ 2 yhteyttä
            │9c25aa5af17a80cc1af6a8533b","i│    │       │
            │d":"P0054","type":"State"},{"p│    │       │
            │name":"Tuutari","change":"1496│    │       │
            │431999","gramps_handle":"_d9c2│    │       │
            │5abb00881f87b8bdbda5eb","id":"│    │       │
            │P0055","type":"Region"},{"pnam│    │       │
            │e":"Nurkkala","change":"150030│    │       │
            │0897","gramps_handle":"_d9c26f│    │       │
            │b0acf5873995a02ac6efe","id":"P│    │       │
            │0056","type":"Village"}]      │    │       │
            ├──────────────────────────────┼────┼───────┤
            │[{"pname":"Inkeri","change":"1│"-1"│[{}]   │ 2 nodea ja
            │496429798","gramps_handle":"_d│    │       │ 1 yhteys
            │9c25aa5af17a80cc1af6a8533b","i│    │       │
            │d":"P0054","type":"State"},{"p│    │       │
            │name":"Venäjä","change":"14996│    │       │
            │85324","gramps_handle":"_d7917│    │       │
            │3305b956899544","id":"P0024","│    │       │
            │type":"Country"}]             │    │       │
            └──────────────────────────────┴────┴───────┘
        """
        global driver
        self.node_id = node_id
        self.result = driver.session().run(self.query, locid=int(node_id))


    def create_tree(self):
        """ Build a tree structure in memory from Neo4j query result
            about self.node_id
    
            Result must have the following mandatory fields:
                nodes   terminal nodes
                r       relation between terminal nodes
                lv      lenght of the relation SIZE(r); 
                        negative, if upwards to the root of the tree
            Other field names form arguments:
                field_id    node instance display name
                field_type  node instance type
                
        """
        #self._get_db_connections(node_id)
        self.tree = treelib.Tree()
        nl = {}
        nl[0] = 'root'
        nstack = []
        rl = {}
        # Juurisolu 0 mahdollistaa solun lisäämisen ylimmän varsinaisen solun
        # yläpuolelle
        self.tree.create_node('', 0)
        nstack.append((0, "root", "", -9999))
    
        for record in self.result:
            # Tuloksessa on kaikki ko. relaatioon osallistuvat solut ja niiden
            # väliset yksittäiset yhteydet
            for node in record['nodes']:
                if not node.id in nl:
                    nl[node.id] = node[self.field_id]              #["pname"]
                    nstack.append((node.id, node[self.field_type], #["type"], 
                                   node[self.field_id],            #["pname"], 
                                   record["lv"]))
            for rel in record['r']:
                # Käydään läpi relaatioketjun yksittäiset (start)-->(end) -välit
                if not rel.id in rl:
                    rl[rel.id] = rel.end
                    nid, ntype, nname, lv = nstack.pop()
                    if len(rl) == 1:    # Ensimmäinen solmu rootin alle
                        nid1, ntype1, nname1, lv1 = nstack.pop()
                        rl[0] = rel.end
    #                     print("create_node('{}', '{}', parent={}, data={})".\
    #                           format(nname1, nid1, 0, {'type':ntype1}))
                        self.tree.create_node(nname1, nid1, parent=0, 
                                              data={self.field_type:ntype1})
                    if lv > 0:
                        parent = rel.end
                    else:
                        parent = self.tree.parent(rel.start).identifier
                    # Lisätään uusi solu ensin nykyisen rinnalle ja 
                    # sitten siirretään nykyinen uuden alle
                    self.tree.create_node(nname, nid, parent=parent, 
                                          data={self.field_type:ntype})
    #                 print("create_node('{}', '{}', parent={}, data={})".\
    #                       format(nname, nid, parent, {'type':ntype}))
                    if lv < 0:
    #                     print("  move_node('{}', '{}')".format(rel.start, nid))
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
                fill = ''.join([ "       " for n in range(lv-1)])
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
    global driver
    host = "bolt:localhost:7687"
    driver = GraphDatabase.driver(host, auth=basic_auth("neo4j", "2000Neo4j"))

    # Suoritetaan haku tietokannasta: paikkaan locid liittyvät
    # solmut ja relaatiot
    t = Tree(None, 'pname', 'type')
    t._get_db_connections(locid)
    # Talletetaan tiedot muistinvaraiseen puurakenteeseen
    tree = t.create_tree()
    print(tree)
    t.print_tree()
#     print(tree.to_json())
    
