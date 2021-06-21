#   Isotammi Genealogical Service for combining multiple researchers' results.
#   Created in co-operation with the Genealogical Society of Finland.
#
#   Copyright (C) 2016-2021  Juha Mäkeläinen, Jorma Haapasalo, Kari Kujansuu, 
#                            Timo Nallikari, Pekka Valta
#
#   This program is free software: you can redistribute it and/or modify
#   it under the terms of the GNU General Public License as published by
#   the Free Software Foundation, either version 2 of the License, or
#   (at your option) any later version.
#
#   This program is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU General Public License for more details.
#
#   You should have received a copy of the GNU General Public License
#   along with this program.  If not, see <http://www.gnu.org/licenses/>.

'''
Reading and updating Neo4j database

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


# --- Save to Batch

    create_to_batch = """
MATCH (b:Root {id: $batch_id})
MERGE (b) -[r:OBJ_OTHER]-> (e:Event {handle: $e_attr.handle})
    SET e = $e_attr
RETURN ID(e) as uniq_id"""

    link_place = """
MATCH (n:Event) WHERE n.handle=$handle
MATCH (m:Place) WHERE m.handle=$place_handle
MERGE (n)-[r:PLACE]->(m)"""

    link_notes = """
MATCH (n:Note)  WHERE n.handle IN $note_handles
WITH n
    MATCH (e:Event)  WHERE e.handle=$handle
    CREATE (e) -[r:NOTE]-> (n)
RETURN count(r) AS cnt"""

    link_citations = """
match (c:Citation) where c.handle in $citation_handles
with c
    match (e:Event)  where e.handle=$handle
    merge (e) -[r:CITATION]-> (c)"""

    update_event = """
match (e:Event{uuid:$uuid})
set e += $attrs
return e
    """
    