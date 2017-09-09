'''
  Kokeillaan paikkahierarkian lukemista
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
MATCH x= (p:Place)-[r:HIERARCY*]->(i:Place) WHERE ID(p) = $locid
    RETURN NODES(x) AS nodes, SIZE(r) AS lv, r
    UNION
MATCH x= (p:Place)<-[r:HIERARCY*]-(i:Place) WHERE ID(p) = $locid
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
    nl[0] = ('root', '')
    rl = {}
    print("NODE {},{} {} {}".format("root", 0, nl[0][0], nl[0][1]))
    for record in result:
        for node in record['nodes']:
            if node.id in nl:
                print("#{:2d}: {},{} {}".format(record["lv"],
                    node.id, node["type"], node["pname"]))
            else:
                nl[node.id] = (node["type"], node["pname"])
                print("NODE {},{} {} {}".format(record["lv"],
                    node.id, node["type"], node["pname"]))
        for rel in record['r']:
            if len(rl) == 0:
                print("LINK {}->{}".format(nl[rel.end],nl[0]))
                rl[0] = (rel.end, 0)
            rl[rel.id] = (rel.start, rel.end)
            print("LINK {}->{}".format(nl[rel.start],nl[rel.end]))
    print("# Relaatiot {}".format(rl))
