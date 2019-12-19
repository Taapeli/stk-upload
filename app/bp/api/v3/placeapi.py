import shareds
from models.gen.dates import DateRange
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

cypher_search0 = """
    match (p:Place {pname:$pname}) 
    optional match (p)-[r:IS_INSIDE]->(u:Place)
    return p, p.uuid as id, COLLECT(u.pname) as uppers
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
MATCH (p:Place {pname:$pname, type:'City'})
    OPTIONAL MATCH (p)-[ur:IS_INSIDE*]->(up:Place)
RETURN p, 
    COLLECT(DISTINCT [ur, up]) as largerPlaces
"""

cypher_record = """
MATCH (p:Place) WHERE p.id = $id 
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

def search(lookedfor):
    print(f"Looking for {lookedfor}")
    result = shareds.driver.session().run(cypher_search, pname=lookedfor)
    records = []
    for rec in  result:
        p = rec['p']
        largerPlaces = rec['largerPlaces']
        uppers = []
#        smallerPlaces = rec['smallerPlaces']
        for urel, largerPlace in largerPlaces:
#            urel=up['ur'] 
            print(urel)
            print(largerPlace)
            upper = dict(
                pname = largerPlace['pname'],
                type = largerPlace['type'],
                date1 = urel[0]['date1'] if urel[0]['date1'] else None,
                date2 = urel[0]['date2'] if urel[0]['date2'] else None,
                datetype = urel[0]['datetype'] if urel[0]['datetype'] else None,
                timespan =  DateRange(urel[0]['datetype'], urel[0]['date1'], urel[0]['date2']).__str__() if urel[0]['datetype'] else None
                )
            print(upper)
            if upper not in uppers:
                uppers.append(upper)
        r = dict(
            uuid=p['uuid'],
            name=p['pname'],
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
    print(f"Getting record {oid}")
    result = shareds.driver.session().run(cypher_record,id=oid).single()
    print(result)
    if not result: return dict(status="OK",resultCount=0)
    p = result.get('p')
    largerPlaces = result['largerPlaces']
    smallerPlaces = result['smallerPlaces']
    places1 = []
    for h1, largerPlace, id2 in largerPlaces: 
        if largerPlace is None: break
        name2 = largerPlace['pname']
        type2 = largerPlace['type']
        place = dict(name=name2, type=type2, id=id2)
        datetype = h1['datetype']
        if datetype:
            date1 = h1['date1']
            date2 = h1['date2']
            d = DateRange(datetype, date1, date2)
            timespan = d.__str__()
            date1 = DateRange.DateInt(h1['date1']).long_date()
            date2 = str(DateRange.DateInt(h1['date2']))
            place['datetype'] = datetype
            place['date1'] = date1
            place['date2'] = date2
            place['timespan'] = timespan
        places1.append(place)
    places2 = []
    for h2, smallerPlace, id2 in smallerPlaces: 
        if smallerPlace is None: break
        name2 = smallerPlace['pname']
        type2 = smallerPlace['type']
        place = dict(name=name2, type=type2, 
                     id=id2)
        datetype = h2['datetype']
        if datetype:
            date1 = h2['date1']
            date2 = h2['date2']
            d = DateRange(datetype, date1, date2)
            timespan = d.__str__()
            date1 = str(DateRange.DateInt(h2['date1']))
            date2 = str(DateRange.DateInt(h2['date2']))
            place['datetype'] = datetype
            place['date1'] = date1
            place['date2'] = date2
            place['timespan'] = timespan
        places2.append(place)
    record = dict(
        id=p['id'],
        name=p['pname'],
        type=p['type'],
        surroundedBy=sorted(places1,key=lambda x:x['name']),
        surrounds=sorted(places2,key=lambda x:x['name']),
    )
    return {"status":"OK",
     "statusText":"OK",
     "resultCount": 1,
     "record": record, 
    }

def record_with_subs(oid, subs):
    print(f"Getting record {oid} with subs {subs}")
    result = shareds.driver.session().run(cypher_record,id=oid).single()
    print(result)
    if not result: return dict(status="Not found",statusText="Not found",resultCount=0)
    p = result.get('p')
#    print(f"id={p['id']} name={p['pname']}")
    largerPlaces = result['largerPlaces']
    smallerPlaces = result['smallerPlaces']
    places1 = []
    for h1,largerPlace,id2 in largerPlaces: 
        if largerPlace is None: break
        name2 = largerPlace['pname']
        type2 = largerPlace['type']
        place = dict(name=name2,type=type2,id=id2)
        datetype = h1['datetype']
        if datetype:
            date1 = h1['date1']
            date2 = h1['date2']
            d = DateRange(datetype, date1, date2)
            timespan = d.__str__()
            date1 = DateRange.DateInt(h1['date1']).long_date()
            date2 = str(DateRange.DateInt(h1['date2']))
            place['datetype'] = datetype
            place['date1'] = date1
            place['date2'] = date2
            place['timespan'] = timespan
        places1.append(place)
    places2 = []
    for h2,smallerPlace,id2 in smallerPlaces: 
        if smallerPlace is None: break
        name2 = smallerPlace['pname']
        type2 = smallerPlace['type']
        place = dict(name=name2,type=type2,id=id2)
        res = record_with_subs(id2, None)
        if "record" in res: place = res["record"]
        place["name"] = name2
        pprint.pprint(place)
        datetype = h2['datetype']
        if datetype:
            date1 = h2['date1']
            date2 = h2['date2']
            d = DateRange(datetype, date1, date2)
            timespan = d.__str__()
            date1 = str(DateRange.DateInt(h2['date1']))
            date2 = str(DateRange.DateInt(h2['date2']))
            place['datetype'] = datetype
            place['date1'] = date1
            place['date2'] = date2
            place['timespan'] = timespan
        places2.append(place)
    resultrecord = dict(
        id=oid,
        name=p['pname'],
        type=p['type'],
        surroundedBy=[], #places1, #sorted(places1,key=lambda x:x.get('name','')),
        surrounds=sorted(places2,key=lambda x:x.get('name','')),
    )
    return {"status":"OK",
     "statusText":"OK",
     "resultCount": 1,
     "record": resultrecord, 
    }

