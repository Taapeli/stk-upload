'''
Created on 16.1.2021

@author: jm
'''

class CypherMedia():

    _match_my_access = """MATCH (o:Media) <-[owner:OWNS]- (b:Batch) 
        <-[:HAS_ACCESS]- (u:UserProfile {username:$user})"""

    get_by_uuid = """
MATCH (media:Media) <-[r:MEDIA] - (n) 
    WHERE media.uuid = $rid
OPTIONAL MATCH (n) <-[:EVENT]- (m)
RETURN media,
    COLLECT(DISTINCT [properties(r), n]) as m_ref,
    COLLECT(DISTINCT [ID(n), m]) AS e_ref"""

    get_all = "MATCH (o:Media) RETURN o"

    # Media list by description with count limit
    read_common_media = """
MATCH (prof) -[:PASSED]-> (o:Media) <- [r:MEDIA] - () 
WHERE o.description >= $start_name 
RETURN o, prof.user as credit, prof.id as batch_id, COUNT(r) AS count
    ORDER BY o.description LIMIT $limit"""

    read_my_own_media = """
MATCH (u:UserProfile {username:$user}) -[:HAS_ACCESS]-> (b:Batch)
    -[owner:OWNS]-> (o:Media) <- [r:MEDIA] - ()
WHERE o.description >= $start_name
RETURN o, b.username as credit, b.id as batch_id, COUNT(r) AS count
    ORDER BY o.description LIMIT $limit"""
