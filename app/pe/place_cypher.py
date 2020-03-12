'''
Created on 12.3.2020

@author: jm
'''

class CypherPlace():
    '''
    Neo4j Cypher clases for Place objects
    '''

    get_name_hierarchies = """
MATCH (a:Place) -[:NAME]-> (pn:Place_name)
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

