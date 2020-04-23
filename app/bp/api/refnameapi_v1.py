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
from _operator import itemgetter

#       AND EXISTS ((r) -[:BASENAME{use:$usage}]-> ())
cypher_search_refname_v1 = """
    MATCH (r:Refname)  
    WHERE toLower(r.name) STARTS WITH toLower($prefix)
    OPTIONAL MATCH (r) -[:BASENAME*{use:$usage}]-> (base:Refname)
        WHERE NOT EXISTS ((base) -[:BASENAME{use:$usage}]-> (:Refname))
    RETURN r.name as name, r.source as source, base.name as basename
"""

cypher_search_refname_contains_v1 = """
    MATCH (r:Refname)  
    WHERE toLower(r.name) CONTAINS toLower($prefix)
    OPTIONAL MATCH (r) -[:BASENAME*{use:$usage}]-> (base:Refname)
        WHERE NOT EXISTS ((base) -[:BASENAME{use:$usage}]-> (:Refname))
    RETURN r.name as name, r.source as source, base.name as basename
"""

cypher_fetch_namefamily = """
    MATCH (base:Refname {name:$lookfor})
    OPTIONAL MATCH (base) <-[:BASENAME*{use:$usage}]- (o:Refname)
    RETURN base.name as basename, COLLECT(o.name) AS names
"""

cypher_add_to_namefamily = """
    MATCH (base:Refname {name:$basename})
    MATCH (rn:Refname {name:$name})
    MERGE (rn) -[:BASENAME{use:$usage}]-> (base)
"""

cypher_remove_from_namefamily = """
    MATCH (rn:Refname {name:$name}) -[rel:BASENAME{use:$usage}]->  (base:Refname {name:$basename})
    DELETE rel
"""

cypher_add_name = """
    MERGE (r:Refname{name:$name}) SET r.source = $source
"""

cypher_del_name = """
    MATCH (r:Refname{name:$name}) 
    DETACH DELETE r
"""

def search(prefix, usage, match):  
    "Returns refnames starting with or containing prefix (case-insensitive)"
    if match == "startswith":
        result = shareds.driver.session().run(cypher_search_refname_v1, 
                                            prefix=prefix, usage=usage)
    else:
        result = shareds.driver.session().run(cypher_search_refname_contains_v1, 
                                            prefix=prefix, usage=usage)
    records = []
    for rec in  result:
        name = rec['name']
        source = rec['source']
        basename = rec['basename']
        records.append(dict(name=name,source=source,basename=basename,is_basename=(basename is None)))
   
#    records.append(surroundedBy=sorted(places1,key=lambda x:x['name']))    
    return {"status":"OK",
     "statusText":"OK",
     "resultCount": len(records),
     "records": sorted(records, key=itemgetter("name")),
    }

def prefixes(prefix, usage):  
    """
    Returns next longer prefixes for names starting with prefix (case-sensitive)
    E.g. for the prefix "Jo" return the list ["Joh","Jos"] if there are names that start with those prefixes.
    """
    cypher = cypher_search_refname_v1.replace("toLower","") # this is case-sensitive
    result = shareds.driver.session().run(cypher, prefix=prefix, usage=usage)
    prefixlen = len(prefix)+1
    prefixes = set()
    for rec in  result:
        name = rec['name']
        if len(name) >= prefixlen:
            newprefix = name[0:prefixlen]
            prefixes.add(newprefix)
    records = sorted(list(prefixes))
   
#    records.append(surroundedBy=sorted(places1,key=lambda x:x['name']))    
    return {"status":"OK",
     "statusText":"OK",
     "resultCount": len(records),
     "records": records,
    }


def fetch(basename, usage):
    result = shareds.driver.session().run(cypher_fetch_namefamily, lookfor=basename, usage=usage).single()
    if not result:
        return dict(status="Not found",statusText="Not found",
                    resultCount=0,
                    names=[])
    names = result['names']
    basename = result['basename']
    return {"status":"OK",
        "statusText":"OK",
        "resultCount": 1,
        "names": sorted(names), 
    }

def add_to_family(basename, names_to_add, usage):
    with shareds.driver.session() as tx:
        for name in names_to_add:
            if name != basename:
                result = tx.run(cypher_add_to_namefamily, basename=basename, name=name, usage=usage)
    return fetch(basename, usage)

def remove_from_family(basename, names_to_remove, usage):
    with shareds.driver.session() as tx:
        for name in names_to_remove:
            if name != basename:
                result = tx.run(cypher_remove_from_namefamily, basename=basename, name=name, usage=usage)
    return fetch(basename, usage)


def addname(name, source):
    result = shareds.driver.session().run(cypher_add_name, name=name, source=source)
    return {"status":"OK",
     "statusText":"OK",
    }

def delnames(names_to_remove):
    with shareds.driver.session() as tx:
        for name in names_to_remove:
            result = tx.run(cypher_del_name, name=name)
    return {"status":"OK",
     "statusText":"OK",
    }
