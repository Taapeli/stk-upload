import shareds
from models.gen.dates import DateRange
"""
https://isotammi.net/api/v0/search?lookfor=Pekka
--> {"status":"OK",
     "statusText":"OK",
     "resultCount": 2,
     "records":[ { "id":"123", "name":"Antrea", "type":"place"},
                 { "id":"333", "name":"Antrea", "type":"village"},
               ]
    }

 
"""
import pprint

cypher_search_refname = """
MATCH (p:Refname) WHERE p.name = $lookedfor
RETURN p.name
"""

cypher_fetch_namegroup = """
MATCH (p:Refname) WHERE (p)<-[:BASENAME]-(:Refname{name:$lookedfor})
MATCH (q:Refname) WHERE (q)-[:BASENAME]->(p)
RETURN p.name AS basename, COLLECT(q.name) AS namegroup
"""
cypher_fetch_namefamily = """
match (n:Refname {name:"Lissu"})
optional match (n) --> (m:Refname)
with coalesce(m, n) AS base
optional match (base) <-- (o:Refname)
return base,o  limit 25"""

def search_refname(lookedfor):
    print(f"Looking for name {lookedfor}")
    result = shareds.driver.session().run(cypher_search_refname, name=lookedfor).single()
    records = []
    for rec in  result:
        p = rec['p']
        r = dict(
                )

        records.append(r)
   
#    records.append(surroundedBy=sorted(places1,key=lambda x:x['name']))    
    return {"status":"OK",
     "statusText":"OK",
     "resultCount": len(records),
     "records":records,
    }


def fetch_namegroup(rname):
    print(f"Getting basename of {rname} with group names")
    result = shareds.driver.session().run(cypher_fetch_namegroup, name=rname)
    print(result)
    if not result: return dict(status="Not found",statusText="Not found",resultCount=0)
    p = result.get('p')

    namegroup = dict(
    )
    return {"status":"OK",
     "statusText":"OK",
     "resultCount": 1,
     "record": namegroup, 
    }

