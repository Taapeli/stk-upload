import shareds
from _operator import itemgetter
from models.gen.dates import DateRange
import pprint
from bl.place import PlaceBl, PlaceName
from pe.neo4j.write_driver import Neo4jWriteDriver
from pe.db_writer import DBwriter
import json
from operator import attrgetter


cypher_test_create = """
    create (p:Place{pname:'zSuomi',coord:[60.17,24.94]}) 
    merge (p) -[r:NAME]-> (pn:Place_name{name:'zSuomi',lang:'fi',order:0})
    merge (p) -[x1:NAME_LANG{lang:'fi'}]-> (pn)
    create (a1:Place{pname:'zHelsinki',type:'City'}) -[:IS_INSIDE]-> (p)
    merge (a1) -[:NAME]-> (pn1a:Place_name{name:'zHelsinki',lang:'fi'})

    create (p2:Place{pname:'zSuomi',type:'Country'})
    merge (p2) -[r2:NAME]-> (pn2:Place_name{name:'zFinland',lang:'sv',order:0})
    merge (p2) -[x2:NAME_LANG{lang:'sv'}]-> (pn2)
    create (a2:Place{pname:'zTurku',type:'City'}) -[:IS_INSIDE]-> (p2)
    merge (a2) -[:NAME]-> (pn2a:Place_name{name:'zÅbo',lang:'sv'})

    return id(p) as id1, id(p2) as id2
"""

cypher_test_delete = """
    MATCH (p:Place{pname:'zSuomi'})-[r]-(x) detach delete p,r,x
"""

cypher_test_show = """
    MATCH (n:Place{pname:'zSuomi'})-[r]-(x) RETURN * LIMIT 25
"""
cypher_search = """
    match (p:Place {pname:$pname}) return p,id(p) as id
"""

cypher_list_subordinate_places = """
    match (p:Place)-[h1:IS_INSIDE]->(largerPlace:Place) 
    match(p) -[r:NAME]-> (pn:Place_name)
    where id(largerPlace) = $parent_id
    return p, id(p) as id, collect([r,pn]) as names
"""

cypher_list_top_level_places = """
    match (p:Place)
    match(p) -[r:NAME]-> (pn:Place_name)
    where not exists( (p)-[:IS_INSIDE]->(:Place) ) 
    return p, id(p) as id, collect([r,pn]) as names
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

cypher_getplace = """
    match (p:Place)
        where id(p) = $id 
    optional match(p) -[r:NAME]-> (pn:Place_name)
    optional match (smallerPlace:Place)-[h2:IS_INSIDE]->(p) 
    optional match (p)-[h1:IS_INSIDE]->(largerPlace:Place) 
    return p,id(p) as id,
        collect(distinct pn) as names,
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


def list_top_level_places():
    result = shareds.driver.session().run(cypher_list_top_level_places)
    places = []
    for rec in  result:
        place_node = rec['p']
        place = PlaceBl.from_node(place_node)
        place.names = [PlaceName.from_node(pn) for (r,pn) in rec['names']]
        places.append(place) 
    return {"status":"OK",
         "statusText":"OK",
         "resultCount": len(places),
         "places":sorted(places, key=attrgetter('pname'))
    }

def list_subordinate_places(parent_id):
    result = shareds.driver.session().run(cypher_list_subordinate_places,parent_id=parent_id)
    places = []
    for rec in  result:
        place_node = rec['p']
        place = PlaceBl.from_node(place_node)
        place.names = [PlaceName.from_node(pn) for (place,pn) in rec['names']]
        places.append(place) 
    return {"status":"OK",
         "statusText":"OK",
         "resultCount": len(places),
         "places":sorted(places, key=attrgetter('pname'))
    }

def getplace(id):
    print('id:',id)
    result = shareds.driver.session().run(cypher_getplace,id=id).single()
    print('result:',result)
    if not result: return dict(status="Error",resultCount=0)
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
    #names = [dict(name=pn['name'],lang=pn['lang']) for pn in result['names']]
    place = PlaceBl.from_node(p)
    place.names = [PlaceName.from_node(pn) for pn in result['names']]
    print(smallerPlaces)
    if smallerPlaces == [[None,None,None]]: smallerPlaces = []
    place.surrounds = [PlaceName.from_node(p2) for (h2,p2,id2) in smallerPlaces]
    place.surrounds=sorted(places2,key=itemgetter('name'))
    return {"status":"OK",
     "statusText":"OK",
     "resultCount": 1,
     "place": place, 
    }

def test_create():
    result = shareds.driver.session().run(cypher_test_create).single()

def test_delete():
    result = shareds.driver.session().run(cypher_test_delete).single()
