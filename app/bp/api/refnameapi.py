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

import shareds
from bl.dates import DateRange
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

