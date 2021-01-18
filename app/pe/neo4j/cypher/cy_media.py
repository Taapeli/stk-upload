'''
Created on 16.1.2021

@author: jm
'''

class CypherMedia():

    get_my_media_by_uuid = """
MATCH (:UserProfile {username:$user}) -[:HAS_ACCESS]-> (b) -[ro:OWNS]->
      (media:Media {uuid:$uuid}) <-[r:MEDIA]- (ref)
OPTIONAL MATCH (ref) <-[:EVENT]- (ref2)
RETURN media, PROPERTIES(r) AS prop, ref, ref2"""
    get_approved_media_by_uuid = """
MATCH () -[ro:OWNS|PASSED]-> (media:Media {uuid:$uuid}) <-[r:MEDIA]- (ref)
OPTIONAL MATCH (ref) <-[:EVENT]- (ref2)
RETURN media, PROPERTIES(r) AS prop, ref, ref2"""

    get_all = "MATCH (o:Media) RETURN o"

    # Media list by description with count limit
    read_approved_medias = """
MATCH (prof) -[:PASSED]-> (o:Media) <- [r:MEDIA] - () 
WHERE o.description >= $start_name 
RETURN o, prof.user as credit, prof.id as batch_id, COUNT(r) AS count
    ORDER BY o.description LIMIT $limit"""

    read_my_medias = """
MATCH (u:UserProfile {username:$user}) -[:HAS_ACCESS]-> (b:Batch)
    -[owner:OWNS]-> (o:Media) <- [r:MEDIA] - ()
WHERE o.description >= $start_name
RETURN o, b.username as credit, b.id as batch_id, COUNT(r) AS count
    ORDER BY o.description LIMIT $limit"""
