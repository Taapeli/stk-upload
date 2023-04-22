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

import shareds
from bl.dates import DateRange
"""
https://isotammi.net/api/v1/search?lookfor=Antrea
--> {"status":"OK",
     "statusText":"OK",
     "resultCount": 2,
     "records":[ { "id":"123", "name":"Antrea", "type":"place"},
                 { "id":"333", "name":"Antrea", "type":"village"},
               ]
    }


https://isotammi.net/api/v1/record?id=123
--> {"status":"OK",
     "statusText":"OK",
     "resultCount": 1,
     "record": {   "id":"123", "name":"Antrea", "type":"place", "timespan":"...",
                    "surrounds":[{"id":"333","name":"Antrea", "type":"village","timespan":"..."}, ...],
                    "surroundedBy":[{"id":"1","name":"Finland,"type":"country","timespan":"..."}
               }
    }


"""
import pprint
# from builtins import None

cypher_search0 = """
    match (p:Place {pname:$pname}) 
    optional match (p)-[r:IS_INSIDE]->(u:Place)
    return p, p.iid as id, COLLECT(u.pname) as uppers
"""

cypher_search1 = """
MATCH (p:Place {pname:$pname, type:'City'})
    OPTIONAL MATCH (p)-[ur:IS_INSIDE*]->(up:Place)
    OPTIONAL MATCH (p)<-[lr:IS_INSIDE]-(lp:Place)
RETURN p, 
    COLLECT(DISTINCT [ur, up]) as largerPlaces,
    COLLECT(DISTINCT [lr, lp]) as smallerPlaces
"""

cypher_search = """
MATCH (p:Place {pname:$pname, type:'City'}) WHERE left(p.id, 2) = 'Pr'
    OPTIONAL MATCH (p)-[ur:IS_INSIDE*]->(up:Place)
RETURN p, 
    COLLECT(DISTINCT [ur, up, up.id]) as largerPlaces
"""

""" or
MATCH p = (:Place {pname:'Angelniemi', type:'City'})-[:IS_INSIDE*]->(up:Place)
    WITH *, relationships(p) AS ur
RETURN p, 
    COLLECT(DISTINCT [ur, up, up.id]) as largerPlaces
"""    
 
cypher_record = """
MATCH (p:Place) WHERE p.id = $id 
    OPTIONAL MATCH (p)-[:NAME]->(pn:Place_name)
    OPTIONAL MATCH (p)-[:NOTE]->(n:Note)    
    OPTIONAL MATCH (smallerPlace:Place)-[h2:IS_INSIDE]->(p) 
    OPTIONAL MATCH (p)-[h1:IS_INSIDE*]->(largerPlace:Place) 
RETURN p,
    COLLECT(DISTINCT pn.pname) as pnames,
    COLLECT(DISTINCT n) as pnotes,
    COLLECT (DISTINCT [h1, largerPlace, largerPlace.id]) as largerPlaces,
    COLLECT (DISTINCT [h2, smallerPlace, smallerPlace.id]) as smallerPlaces
"""

cypher_record_at = """
MATCH (p:Place) WHERE p.id = $id 
    OPTIONAL MATCH (p)-[:NAME]->(pn:Place_name)
    OPTIONAL MATCH (p)-[:NOTE]->(n:Note)    
    OPTIONAL MATCH (p)-[h1:IS_INSIDE {date1: $d1, date2: $d1, datetype: $dt}]->(largerPlace:Place) 
    OPTIONAL MATCH (smallerPlace:Place)-[h2:IS_INSIDE]->(p) 
RETURN p,
    COLLECT(DISTINCT pn.pname) as pnames,
    COLLECT(DISTINCT n) as pnotes,
    COLLECT (DISTINCT [h1, largerPlace, largerPlace.id]) as largerPlaces,
    COLLECT (DISTINCT [h2, smallerPlace, smallerPlace.id]) as smallerPlaces
"""

cypher_selected_records_with_subs = """
MATCH (p:Place) WHERE p.id IN $oids 
    OPTIONAL MATCH (p)-[:NAME]->(pn:Place_name)
    OPTIONAL MATCH (p)-[:NOTE]->(n:Note)    
    OPTIONAL MATCH (smallerPlace:Place)-[h2:IS_INSIDE]->(p) 
    OPTIONAL MATCH (p)-[h1:IS_INSIDE]->(largerPlace:Place) 
RETURN p,
    COLLECT(DISTINCT pn.pname) as pnames,
    COLLECT(DISTINCT n) as pnotes,
    COLLECT (DISTINCT [h1, largerPlace, largerPlace.id]) as largerPlaces,
    COLLECT (DISTINCT [h2, smallerPlace, smallerPlace.id]) as smallerPlaces
"""

# cypher_record_with_selected_subs = """
# MATCH (p:Place) WHERE p.id = $oid 
#     OPTIONAL MATCH (p)-[:NAME]->(pn:Place_name)
#     OPTIONAL MATCH (p)-[:NOTE]->(n:Note)    
#     OPTIONAL MATCH (smallerPlace:Place) WHERE smallerPlace.id IN $subs -[h2:IS_INSIDE]->(p) 
#     OPTIONAL MATCH (p)-[h1:IS_INSIDE]->(largerPlace:Place) 
# RETURN p,
#     COLLECT(DISTINCT pn.pname) as pnames,
#     COLLECT(DISTINCT n) as pnotes,
#     COLLECT (DISTINCT [h1, largerPlace, largerPlace.id]) as largerPlaces,
#     COLLECT (DISTINCT [h2, smallerPlace, smallerPlace.id]) as smallerPlaces
# """


def search(lookedfor):
#    print(f"Looking for {lookedfor}")
    result = shareds.driver.session().run(cypher_search, pname=lookedfor)#
    records = []
    for rec in  result:
        p = rec['p']
        uppers = __process_larger_places(rec['largerPlaces'])
        r = dict(
            iid=p['iid'],
            pname=p['pname'],
            id=p['id'],
            type=p['type'],    
            ups=uppers)

        records.append(r)
   
#    records.append(surroundedBy=sorted(places1,key=lambda x:x['name']))    
    return {"status":"OK",
     "statusText":"OK",
     "resultCount": len(records),
     "records":records,
    }


def record(oid):
#    print(f"Getting record {oid}")
    result = shareds.driver.session().run(cypher_record, id=oid).single()
#    print(result)
    if not result: return dict(status="OK",resultCount=0)
    p = result.get('p')
    largerPlaces = __process_larger_places(result['largerPlaces'])
    smallerPlaces = __process_places(result['smallerPlaces'])

    record = dict(
        id=p['id'],
        pname=p['pname'],
        type=p['type'],
        surroundedBy=largerPlaces, # sorted(largerPlaces,key=lambda x:x['name']),
        surrounds=sorted(smallerPlaces,key=lambda x:x['pname']),
    )
    return {"status":"OK",
     "statusText":"OK",
     "resultCount": 1,
     "record": record, 
    }


def record_with_subs(oid, **kwargs):
#    print(f"Getting record {oid} with all subs")
    if 'd1' in kwargs and 'd2' in kwargs and 'dt' in kwargs:
        dt = int(kwargs['dt'])
        d1 = int(kwargs['d1'])
        d2 = int(kwargs['d2'])
        result = shareds.driver.session().run(cypher_record_at, id=oid, dt=dt, d1=d1, d2=d2).single() 
#       result = shareds.driver.session().run(cypher_record, id=oid).single()   
    else:    
        result = shareds.driver.session().run(cypher_record, id=oid).single()
#    print(result)
    if not result: 
        return dict(status="Not found",statusText="Not found",resultCount=0)
    p = result.get('p')
#    print(f"id={p['id']} name={p['pname']}")
    largerPlaces = __process_larger_places(result['largerPlaces'])
    smallerPlaces = __process_places(result['smallerPlaces'])

    resultrecord = dict(
        id=oid,
        pname=p['pname'],
        lang=p['lang'] if p['lang'] else None,
        type=p['type'],
        coord=p['coord'] if p['coord'] else None,
        surroundedBy=largerPlaces, #sorted(places1,key=lambda x:x.get('name','')),
        surrounds=sorted(smallerPlaces, key=lambda x:x.get('pname','')),
    )
    return {"status":"OK",
     "statusText":"OK",
     "resultCount": 1,
     "record": resultrecord, 
    }

def __process_larger_places(largerPlaces):
    uppers = [] 
    if largerPlaces != None:      
        for urel, largerPlace, lid in largerPlaces:
            d1 = d2 = dt = None
            if urel and urel[0]:
                print(f"urel  {urel[0].values()} ")
                d1 = urel[0]['date1'] if urel else None
                d2 = urel[0]['date2'] if urel and urel[0]['date2'] else None
                dt = urel[0]['datetype'] if urel[0]['datetype'] else None
            print(largerPlace)
            upper = dict(
                id = largerPlace['id'],
                pname = largerPlace['pname'],
                type = largerPlace['type'],
                coord = largerPlace.get('coord'),
#                date1 = urel[0]['date1'] if urel and urel[0]['date1'] else None,
#                date2 = urel[0]['date2'] if urel and urel[0]['date2'] else None,
#                datetype = urel[0]['datetype'] if urel[0]['datetype'] else None,
                date1 = d1,
                date2 = d2,
                datetype = dt,                
                timespan =  DateRange(dt, d1, d2).__str__() if dt else None
                )
    #            print(upper)
            if upper not in uppers:
                uppers.append(upper)
    return uppers    
    
def __process_places(places):
    rplaces = []
    for h1, place, pid in places: 
        if place is None: break
        pname = place['pname']
        ptype = place['type']
        rplace = dict(pname=pname, type=ptype, id=pid)
        datetype = h1['datetype']
        if datetype:
            date1 = h1['date1']
            date2 = h1['date2']
            d = DateRange(datetype, date1, date2)
            timespan = d.__str__()
            date1 = DateRange.DateInt(h1['date1']).long_date()
            date2 = str(DateRange.DateInt(h1['date2']))
            rplace['datetype'] = datetype
            rplace['date1'] = date1
            rplace['date2'] = date2
            rplace['timespan'] = timespan
        rplaces.append(rplace)
    return rplaces        
