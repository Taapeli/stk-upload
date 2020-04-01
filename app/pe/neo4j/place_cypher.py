'''
Created on 12.3.2020

@author: jm
'''

class CypherPlace():
    '''
    Neo4j Cypher clases for Place objects
    '''

    get_common_name_hierarchies = """
MATCH (b) -[:PASSED]-> (a:Place) -[:NAME]-> (pn:Place_name)
    WHERE a.pname >= $fw
OPTIONAL MATCH (a:Place) -[:IS_INSIDE]-> (up:Place) -[:NAME]-> (upn:Place_name)
OPTIONAL MATCH (a:Place) <-[:IS_INSIDE]- (do:Place) -[:NAME]-> (don:Place_name)
RETURN ID(a) AS id, a.uuid as uuid, a.type AS type,
    COLLECT(DISTINCT pn) AS names, a.coord AS coord,
    COLLECT(DISTINCT [ID(up), up.uuid, up.type, upn.name, upn.lang]) AS upper,
    COLLECT(DISTINCT [ID(do), do.uuid, do.type, don.name, don.lang]) AS lower
ORDER BY names[0].name LIMIT $limit"""

    get_my_name_hierarchies = """
MATCH (prof:UserProfile) -[:HAS_LOADED]-> (b:Batch) -[:OWNS]-> (a:Place)
    WHERE prof.username = $user AND a.pname >= $fw
MATCH (a:Place) -[:NAME_LANG {lang:$lang}]-> (pn:Place_name)
OPTIONAL MATCH (a:Place) -[:IS_INSIDE]-> (up:Place) -[:NAME_LANG {lang:$lang}]-> (upn:Place_name)
OPTIONAL MATCH (a:Place) <-[:IS_INSIDE]- (do:Place) -[:NAME_LANG {lang:$lang}]-> (don:Place_name)
RETURN ID(a) AS id, a.uuid as uuid, a.type AS type,
    COLLECT(DISTINCT pn) AS names, a.coord AS coord,
    COLLECT(DISTINCT [ID(up), up.uuid, up.type, upn.name, upn.lang]) AS upper,
    COLLECT(DISTINCT [ID(do), do.uuid, do.type, don.name, don.lang]) AS lower
ORDER BY names[0].name LIMIT $limit"""

# Default language names update with $place_id, $fi_id, $sv_id
    link_name_lang = """
MATCH (fi:Place_name) <-[:NAME]- (place:Place),
    (place) -[:NAME]-> (sv:Place_name)  
    WHERE ID(place) = $place_id AND ID(fi) = $fi_id AND ID(sv) = $sv_id
OPTIONAL MATCH (place) -[r:NAME_LANG]-> ()
    DELETE r
MERGE (place) -[:NAME_LANG {lang:'fi'}]-> (fi)
MERGE (place) -[:NAME_LANG {lang:'sv'}]-> (sv)
RETURN DISTINCT ID(place) AS pl, ID(fi) AS fi, ID(sv) AS sv"""

# Default language names update with $place_id, $fi_id; sv_id is the same
    link_name_lang_single = """
MATCH (n:Place_name) <-[:NAME]- (place:Place)  
    WHERE ID(place) = $place_id AND ID(n) = $fi_id
OPTIONAL MATCH (place) -[r:NAME_LANG]-> ()
    DELETE r
MERGE (place) -[:NAME_LANG {lang:'fi'}]-> (n)
MERGE (place) -[:NAME_LANG {lang:'sv'}]-> (n)
RETURN DISTINCT ID(place) AS pl, ID(n) AS fi, ID(n) AS sv"""

# For place page
    get_w_names_notes = """
MATCH (prof:UserProfile) -[:HAS_LOADED]-> (:Batch) -[:OWNS]-> (place:Place)
    WHERE prof.username = $user AND place.uuid=$uuid
MATCH (place) -[:NAME_LANG {lang:$lang}]-> (name:Place_name)
with place, name
    OPTIONAL MATCH (place) -[:NAME]-> (n:Place_name) WHERE not n = name
    OPTIONAL MATCH (place) -[nr:NOTE]-> (note:Note)
    OPTIONAL MATCH (place) -[mr:MEDIA]-> (media:Media)
RETURN place, name,
    COLLECT(DISTINCT n) AS names,
    COLLECT (DISTINCT note) AS notes,
    COLLECT (DISTINCT media) AS medias"""

    get_person_events = """
MATCH (p:Person) -[r:EVENT]-> (e:Event) -[:PLACE]-> (l:Place)
    WHERE id(l) = $locid
    MATCH (p) --> (n:Name)
WITH p, r, e, l, n ORDER BY n.order
RETURN p AS person, r.role AS role,
    COLLECT(n) AS names, e AS event
ORDER BY e.date1"""

     # Query for Place hierarcy
    hier_query = """
MATCH x= (p:Place)<-[r:IS_INSIDE*]-(i:Place) WHERE ID(p) = $locid
    RETURN NODES(x) AS nodes, SIZE(r) AS lv, r
    UNION
MATCH x= (p:Place)-[r:IS_INSIDE*]->(i:Place) WHERE ID(p) = $locid
    RETURN NODES(x) AS nodes, SIZE(r)*-1 AS lv, r
"""
    # Query for single Place without hierarcy
    root_query = """
MATCH (p:Place) WHERE ID(p) = $locid
RETURN p.type AS type, p.uuid as uuid, p.pname AS name
"""
    # Query to get names for a Place
    name_query="""
MATCH (l:Place)-->(n:Place_name) WHERE ID(l) = $locid
RETURN COLLECT(n) AS names LIMIT 15
"""

