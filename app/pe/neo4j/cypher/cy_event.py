'''
Reading and updating Neo4j database

See also: gramps.cypher_gramps for updates from Gramps xml file

Created on 2.9.2020

@author: JMä
'''

class CypherEvent(object):

    get_an_event_common = '''
MATCH (root:Audit) -[r:PASSED]-> (e:Event {uuid:$uuid}) 
RETURN e, type(r) AS root_type, root'''
    get_an_event_own = '''
MATCH (root:Batch {user:$user}) -[r:OWNS]-> (e:Event {uuid:$uuid}) 
RETURN e, type(r) AS root_type, root'''

    get_event_place = """
MATCH (e:Event) -[rp:PLACE]-> (place)
    WHERE ID(e) = $uid
OPTIONAL MATCH (place) -[:NAME_LANG {lang:$lang}]-> (name)
OPTIONAL MATCH (place) -[r:IS_INSIDE]-> (upper)
OPTIONAL MATCH (upper) -[:NAME_LANG {lang:$lang}]-> (uname)
RETURN place, name, 
    COLLECT(DISTINCT [properties(r), upper,uname]) as upper_n
"""
    get_event_source = """
MATCH (e:Event) -[:CITATION]-> (cite) -[:SOURCE]-> (source)
    WHERE ID(e) = $uid
RETURN e, cite,source
"""
    get_event_notes_medias = """
MATCH (e:Event)
    WHERE ID(e) = $uid
OPTIONAL MATCH (e) -[rel_n:NOTE]-> (note)
OPTIONAL MATCH (e) -[rel_m:MEDIA]-> (media)
WITH e, note, rel_n, media, rel_m 
    WHERE NOT note IS NULL OR NOT media IS NULL
RETURN COLLECT(DISTINCT [properties(rel_n), note]) AS notes, 
       COLLECT(DISTINCT [properties(rel_m), media]) AS medias
"""

    # Get Event with referring Persons and Families
    get_event_participants = """
MATCH (event:Event) <-[r:EVENT]- (p) 
    WHERE ID(event) = $uid
OPTIONAL MATCH (p) -[:NAME]-> (n:Name {order:0})
RETURN  r.role AS role, p, n AS name
    ORDER BY role"""
#     get_event_notes = """
# MATCH (e:Event) -[rn:NOTE]-> (note)
#     WHERE ID(e) = $uid
# RETURN note, properties(rn) AS rel"""
#     get_event_medias = """
# MATCH (e:Event) -[rn:NOTE]-> (note)
#     WHERE ID(e) = $uid
# RETURN note, properties(rn) AS rel"""

    