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
MATCH (a:Place) -[:NAME]-> (pn:Place_name)
OPTIONAL MATCH (a:Place) -[:IS_INSIDE]-> (up:Place) -[:NAME]-> (upn:Place_name)
OPTIONAL MATCH (a:Place) <-[:IS_INSIDE]- (do:Place) -[:NAME]-> (don:Place_name)
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

