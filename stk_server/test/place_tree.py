'''
  Demo-ohjelma: Kokeillaan paikkahierarkian lukemista
Created on 8.9.2017
@author: jm
'''
import sys
from neo4j.v1 import GraphDatabase, basic_auth
driver = None

def connect_db():
    global driver
    host = "bolt:localhost:7687"
    driver = GraphDatabase.driver(host, auth=basic_auth("neo4j", "2000Neo4j"))

def lue(locid):
    global driver
    query = """
MATCH x= (p:Place)<-[r:HIERARCY*]-(i:Place) WHERE ID(p) = $locid
    RETURN NODES(x) AS nodes, SIZE(r) AS lv, r
    UNION
MATCH x= (p:Place)-[r:HIERARCY*]->(i:Place) WHERE ID(p) = $locid
    RETURN NODES(x) AS nodes, SIZE(r)*-1 AS lv, r
"""
    return (driver.session().run(query, locid=int(locid)))

if __name__ == '__main__':
    if len(sys.argv) <= 1:
        locid = 21773
    else:
        locid = int(sys.argv[1])
    print ("paikka {}".format(locid))

    connect_db()
    result = lue(locid)
    nl = {}
    nl[0] = 'root'
    nstack = []
    rl = {}
    print("create_node('{}', '{}')".format('', 0))
    nstack.append((0, "root", "", -99))

    for record in result:
        for node in record['nodes']:
            if node.id in nl:
                print("#{:2d}: {},{} {}".format(record["lv"],
                    node.id, node["type"], node["pname"]))
            else:
                nl[node.id] = node["pname"]
                nstack.append((node.id, node["type"], 
                               node["pname"], record["lv"]))
                print("# NODE {},{} {} {}".format(record["lv"],
                    node.id, node["type"], node["pname"]))
        for rel in record['r']:
            if not rel.id in rl:
                rl[rel.id] = rel.end
                nid, ntype, nname, lv = nstack.pop()
                if len(rl) == 1:    # Ensimmäinen solmu rootin alle
                    nid1, ntype1, nname1, lv1 = nstack.pop()
                    rl[0] = rel.end
                    print("create_node('{}', '{}', parent={}, data={})".\
                          format(nname1, nid1, 0, {'type':ntype1}))
                if lv > 0:
                    parent = rel.end
                else:
                    parent = "Parent({})".format(rel.start)
                print("# LINK {}->{}".format(rel.start,rel.end))
    
                print("create_node('{}', '{}', parent={}, data={})".\
                      format(nname, nid, parent, {'type':ntype}))
                if lv < 0:
                    print("move_node('{}', '{}')".format(parent, nid))

    #print("# Relaatiot {}".format(rl))
