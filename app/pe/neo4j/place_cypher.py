'''
Created on 12.3.2020

@author: jm
'''

class CypherPlace():
    '''
    Neo4j Cypher clases for Place objects
    '''

    _get_name_hierarchies_tail = """
    OPTIONAL MATCH (place:Place) -[:NAME]-> (pn:Place_name)
        WHERE NOT pn = name
//  WITH place, name, COLLECT(DISTINCT pn) AS names, COUNT(ref) AS uses
        OPTIONAL MATCH (place:Place) -[:IS_INSIDE]-> (up:Place) -[:NAME]-> (upn:Place_name)
        OPTIONAL MATCH (place:Place) <-[:IS_INSIDE]- (do:Place) -[:NAME]-> (don:Place_name)
        RETURN place, name, COUNT(DISTINCT ref) AS uses,
            COLLECT(DISTINCT pn) AS names,
            COLLECT(DISTINCT [ID(up), up.uuid, up.type, upn.name, upn.lang]) AS upper,
            COLLECT(DISTINCT [ID(do), do.uuid, do.type, don.name, don.lang]) AS lower
    ORDER BY name.name"""

    get_common_name_hierarchies = """
MATCH () -[:PASSED]-> (place:Place) -[:NAME_LANG {lang:$lang}]-> (name:Place_name)
    WHERE name.name >= $fw
WITH place, name ORDER BY name.name LIMIT  $limit
    OPTIONAL MATCH (place:Place) <-[:PLACE]- (ref)
""" + _get_name_hierarchies_tail

    get_my_name_hierarchies = """
MATCH (b:Batch) -[:OWNS]-> (place:Place) -[:NAME_LANG {lang:$lang}]-> (name:Place_name)
    WHERE b.user = $user AND name.name >= $fw
WITH place, name ORDER BY name.name LIMIT $limit
    OPTIONAL MATCH (place:Place) <-[:PLACE]- (ref) <-[*2]- (b:Batch)
        WHERE b.user = $user
""" + _get_name_hierarchies_tail

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
    _get_w_names_notes_tail = """
MATCH (place) -[:NAME_LANG {lang:$lang}]-> (name:Place_name)
WITH place, name
    OPTIONAL MATCH (place) -[:NAME]-> (n:Place_name) WHERE not n = name
    OPTIONAL MATCH (place) -[nr:NOTE]-> (note:Note)
    OPTIONAL MATCH (place) -[mr:MEDIA]-> (media:Media)
RETURN place, name,
    COLLECT(DISTINCT n) AS names,
    COLLECT (DISTINCT note) AS notes,
    COLLECT (DISTINCT media) AS medias"""
    get_common_w_names_notes = """
MATCH () -[:PASSED]-> (place:Place)
    WHERE place.uuid=$uuid""" + _get_w_names_notes_tail
    get_my_w_names_notes = """
MATCH (prof:UserProfile) -[:HAS_LOADED]-> (:Batch) -[:OWNS]-> (place:Place)
    WHERE prof.username = $user AND place.uuid=$uuid""" + _get_w_names_notes_tail

    get_person_events = """
MATCH (p:Person) -[r:EVENT]-> (e:Event) -[:PLACE]-> (l:Place)
    WHERE id(l) = $locid
    MATCH (p) --> (n:Name)
WITH p, r, e, l, n ORDER BY n.order
RETURN p AS person, r.role AS role,
    COLLECT(n) AS names, e AS event
ORDER BY e.date1"""

    # Queries for Place page hierarcy
    read_pl_hierarchy = """
MATCH x= (p:Place)<-[:IS_INSIDE*]-(i:Place) WHERE ID(p) = $locid
    WITH NODES(x) AS nodes, relationships(x) as r
    RETURN nodes, SIZE(r) AS lv, r
    UNION
MATCH x= (p:Place)-[:IS_INSIDE*]->(i:Place) WHERE ID(p) = $locid
    WITH NODES(x) AS nodes, relationships(x) as r
    RETURN nodes, SIZE(r)*-1 AS lv, r
"""
    # Query for single Place without hierarcy
    root_query = """
MATCH (p:Place) WHERE ID(p) = $locid
RETURN p.type AS type, p.uuid as uuid, p.pname AS name
"""
    # Query to get names for a Place with $locid, $lang
    read_pl_names="""
MATCH (place:Place) -[:NAME_LANG {lang:$lang}]-> (name:Place_name)
    WHERE ID(place) = $locid
with place, name
    OPTIONAL MATCH (place) -[:NAME]-> (n:Place_name) WHERE not n = name
RETURN name, COLLECT(n) AS names LIMIT 15
"""
# MATCH (l:Place)-[:NAME]->(n:Place_name) WHERE ID(l) = $locid
# RETURN COLLECT(n) AS names LIMIT 15

