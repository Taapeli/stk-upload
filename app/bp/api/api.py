# Database queries from outside
# Note. This is older version of placepai.py by kkj
#
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
import uuid

cypher_search = """
    match (p:Place {pname:$pname}) return p,id(p) as id
"""

cypher_record = """
    match (p:Place)
        where id(p) = $id 
    optional match (smallerPlace:Place)-[h2:IS_INSIDE]->(p) 
    optional match (p)-[h1:IS_INSIDE]->(largerPlace:Place) 
    return p,
        collect (distinct [h1,largerPlace,id(largerPlace)]) as largerPlaces,
        collect (distinct [h2,smallerPlace,id(smallerPlace)]) as smallerPlaces
"""

def search(lookfor):
    result = shareds.driver.session().run(cypher_search,pname=lookfor)
    records = []
    for rec in  result:
        p = rec['p']
        oid = rec['id']
        r = dict(
            id=oid,
            name=p['pname'],
            type=p['type'],
        )
        records.append(r) 
    return {"status":"OK",
     "statusText":"OK",
     "resultCount": len(records),
     "records":records,
    }



def record(oid):
    result = shareds.driver.session().run(cypher_record,id=oid).single()
    print(result)
    if not result: return dict(status="OK",resultCount=0)
    p = result.get('p')
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
        id=oid,
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

def record_with_subs(oid):
    result = shareds.driver.session().run(cypher_record,id=oid).single()
    print(result)
    if not result: return dict(status="Not found",statusText="Not found",resultCount=0)
    p = result.get('p')
    print(f"id={oid} name={p['pname']}")
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
        res = record_with_subs(id2)
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



cypher_check_apikey = """
    match   (user:User{is_active:true}) --> 
            (prof:UserProfile{apikey:$apikey})
    where 'research' in user.roles 
    return user
"""
    
cypher_get_apikey = """
    match (prof:UserProfile{username:$username})
    return prof.apikey as apikey
"""

cypher_save_apikey = """
    match (prof:UserProfile{username:$username})
    set prof.apikey = $apikey
"""

def is_validkey(apikey):
    result = shareds.driver.session().run(cypher_check_apikey,apikey=apikey).single()
    if result: 
        return True
    else:
        return False
    

def save_apikey(current_user, apikey):
    result = shareds.driver.session().run(cypher_save_apikey,username=current_user.username,apikey=apikey).single()


def get_apikey(current_user):
    if 'research' not in current_user.roles: return None
    result = shareds.driver.session().run(cypher_get_apikey,username=current_user.username).single()
    if result: 
        apikey = result['apikey']
    else:
        apikey = None
    if not apikey:
        apikey = uuid.uuid4().hex
        save_apikey(current_user,apikey)
    return apikey


