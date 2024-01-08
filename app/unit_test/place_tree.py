#!/usr/bin/python
# -*- coding:utf-8 -*-
'''
  Demo-ohjelma: Kokeillaan paikkahierarkian lukemista
Created on 8.9.2017
@author: jm
'''
import sys
from neo4j import GraphDatabase
import treelib

def connect_db():
    global driver
    host = "bolt:localhost:7687"
    driver = GraphDatabase.driver(host, auth=("neo4j", "2000Neo4j"))


def get_connections(locid):
    """ Kyselyn tulos, kun puurakenne on
         ── Venäjä
            └── Inkeri (kysytty locid)
                └── Tuutari
                    └── Nurkkala
        ╒══════════════════════════════╤════╤═══════╕
        │"nodes"                       │"lv"│"r"    │
        ╞══════════════════════════════╪════╪═══════╡
        │[{"pname":"Inkeri","change":"1│"1" │[{}]   │ 2 nodea ja
        │496429798","handle":"_d│    │       │ 1 yhteys
        │9c25aa5af17a80cc1af6a8533b","i│    │       │
        │d":"P0054","type":"State"},{"p│    │       │
        │name":"Tuutari","change":"1496│    │       │
        │431999","handle":"_d9c2│    │       │
        │5abb00881f87b8bdbda5eb","id":"│    │       │
        │P0055","type":"Region"}]      │    │       │
        ├──────────────────────────────┼────┼───────┤
        │[{"pname":"Inkeri","change":"1│"2" │[{},{}]│ 3 nodea ja
        │496429798","handle":"_d│    │       │ 2 yhteyttä
        │9c25aa5af17a80cc1af6a8533b","i│    │       │
        │d":"P0054","type":"State"},{"p│    │       │
        │name":"Tuutari","change":"1496│    │       │
        │431999","handle":"_d9c2│    │       │
        │5abb00881f87b8bdbda5eb","id":"│    │       │
        │P0055","type":"Region"},{"pnam│    │       │
        │e":"Nurkkala","change":"150030│    │       │
        │0897","handle":"_d9c26f│    │       │
        │b0acf5873995a02ac6efe","id":"P│    │       │
        │0056","type":"Village"}]      │    │       │
        ├──────────────────────────────┼────┼───────┤
        │[{"pname":"Inkeri","change":"1│"-1"│[{}]   │ 2 nodea ja
        │496429798","handle":"_d│    │       │ 1 yhteys
        │9c25aa5af17a80cc1af6a8533b","i│    │       │
        │d":"P0054","type":"State"},{"p│    │       │
        │name":"Venäjä","change":"14996│    │       │
        │85324","handle":"_d7917│    │       │
        │3305b956899544","id":"P0024","│    │       │
        │type":"Country"}]             │    │       │
        └──────────────────────────────┴────┴───────┘
    """
    global driver
    query = """
MATCH x= (p:Place)<-[r:IS_INSIDE*]-(i:Place) WHERE ID(p) = $locid
    RETURN NODES(x) AS nodes, SIZE(r) AS lv, r
    UNION
MATCH x= (p:Place)-[r:IS_INSIDE*]->(i:Place) WHERE ID(p) = $locid
    RETURN NODES(x) AS nodes, SIZE(r)*-1 AS lv, r
"""
    return (driver.session().run(query, locid=int(locid)))


def load_to_tree_struct(result):
    t = treelib.Tree()
    nl = {}
    nl[0] = 'root'
    nstack = []
    rl = {}
    # Juurisolu 0 mahdollistaa solun lisäämisen ylimmän varsinaisen solun
    # yläpuolelle
    t.create_node('', 0)
    nstack.append((0, "root", "", -99))

    for record in result:
        # Tuloksessa on kaikki ko. relaatioon osallistuvat solut ja niiden
        # väliset yksittäiset yhteydet
        for node in record['nodes']:
            if not node.id in nl:
                nl[node.id] = node["pname"]
                nstack.append((node.id, node["type"], 
                               node["pname"], record["lv"]))
        for rel in record['r']:
            # Käydään läpi relaatioketjun yksittäiset (start)-->(end) -välit
            if not rel.id in rl:
                rl[rel.id] = rel.end
                nid, ntype, nname, lv = nstack.pop()
                if len(rl) == 1:    # Ensimmäinen solmu rootin alle
                    nid1, ntype1, nname1, _lv1 = nstack.pop()
                    rl[0] = rel.end
#                     print("create_node('{}', '{}', parent={}, data={})".\
#                           format(nname1, nid1, 0, {'type':ntype1}))
                    t.create_node(nname1, nid1, parent=0, data={'type':ntype1})
                if lv > 0:
                    parent = rel.end
                else:
                    parent = t.parent(rel.start).identifier
                # Lisätään uusi solu ensin nykyisen rinnalle ja 
                # sitten siirretään nykyinen uuden alle
                t.create_node(nname, nid, parent=parent, data={'type':ntype})
#                 print("create_node('{}', '{}', parent={}, data={})".\
#                       format(nname, nid, parent, {'type':ntype}))
                if lv < 0:
#                     print("  move_node('{}', '{}')".format(rel.start, nid))
                    t.move_node(rel.start, nid)
    return t

def print_tree(t):
    nl = {}
    lv = 0
    fill = ""
    nodes = [t[node] for node in t.expand_tree(mode=t.DEPTH)]
    for node in nodes:
        if node.bpointer != None:
            if node.bpointer in nl:
                lv = nl[node.bpointer] + 1
            else:
                lv = lv + 1
                nl[node.identifier] = lv
            fill = "        " * (lv-1)
            print(f"({lv}){fill} {node.bpointer:6d}<-{node.identifier:6d} {node.tag} ")

if __name__ == '__main__':
    """ Run 'python unit_test/place_tree.py 103338'
        where the argument is iid of a place
    """
    if len(sys.argv) <= 1:
        locid = 21773
    else:
        locid = int(sys.argv[1])
    print (f"paikka {locid}")

    connect_db()
    # Suoritetaan haku tietokannasta: paikkaan locid liittyvät
    # solmut ja relaatiot
    neo_result = get_connections(locid)
    # Talletetaan tiedot muistinvaraiseen puurakenteeseen
    t = load_to_tree_struct(neo_result)
    print(t)
    print_tree(t)
#     print(t.to_json())
    
