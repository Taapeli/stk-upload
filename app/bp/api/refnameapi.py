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
MATCH (p:Refname {name: $lookfor}) --> (b:Refname)
RETURN b.name as refname
"""

cypher_fetch_namefamily = """
MATCH (n:Refname {name:$lookfor})
OPTIONAL MATCH (n) --> (m:Refname)
WITH COALESCE(m, n) AS base
OPTIONAL MATCH (base) <-- (o:Refname)
RETURN [base.name] + COLLECT(o.name) AS namefamily
"""


def search_refname(rname):
#    print(f"Looking for basename of name {rname}")
    result = shareds.driver.session().run(cypher_search_refname, lookfor=rname).single()
    if not result: 
        return dict(status="Not found",statusText="Not found",resultCount=0)
    records = []
    for rec in  result:
        p = rec['p']
        records.append(p)
   
#    records.append(surroundedBy=sorted(places1,key=lambda x:x['name']))    
    return {"status":"OK",
     "statusText":"OK",
     "resultCount": len(records),
     "records": records,
    }


def fetch_namefamily(rname):
#    print(f"Getting name family of {rname}")
    result = shareds.driver.session().run(cypher_fetch_namefamily, lookfor=rname)
    if not result:
#        print(f"namefamily for {rname}  not found") 
        return dict(status="Not found",statusText="Not found",resultCount=0)
    for rec in result:
        namefamily = rec['namefamily']
#        print(namefamily)
        return {"status":"OK",
            "statusText":"OK",
            "resultCount": 1,
            "record": namefamily, 
               }
#    print(f"No namefamily in result for {rname} found")     
    return dict(status="Not found",statusText="Not found",resultCount=0)   

