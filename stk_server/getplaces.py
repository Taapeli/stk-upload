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
    RETURN ID(p) AS id1, p.type AS type1, p.pname AS name1,
           ID(i) AS id2, i.type AS type2, i.pname AS name2, 
           LENGTH(r) AS lv, r
    UNION
MATCH x= (p:Place)<-[r:HIERARCY*]-(i:Place) WHERE ID(p) = $locid
    RETURN ID(i) AS id1, i.type AS type1, i.pname AS name1,
           ID(p) AS id2, p.type AS type2, p.pname AS name2,
           LENGTH(r)*-1 AS lv, r
"""
    return (driver.session().run(query, locid=int(locid)))

if __name__ == '__main__':
    if len(sys.argv) == 1:
        locid = input("Give the unique id of the place (q to quit): ")
    else:
        print(str(sys.argv[1]))
        locid = int(sys.argv[1])
        

    connect_db()
    while locid != 'q':
        print ("lue({})".format(locid))
        result = lue(locid)
        for record in result:
            nuoli = record['r']
            print("{:2d}: {},{},{} / {},{},{}".format(record["lv"],
                   record["id1"], record["type1"], record["name1"],
                   record["id2"], record["type2"], record["name2"]
                   )
                  )
            for rel in nuoli:
                print("    {}->{}".format(rel.start,rel.end))
                
        locid = input("\n\nGive the unique id of the place (q to quit): ")
