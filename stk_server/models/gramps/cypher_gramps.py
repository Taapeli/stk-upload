'''
Cypher clauses for models.gramps module

Created on 21.3.2018

@author: jm
'''

class Cypher_batch(object):
    '''
    Cypher clauses for managing Batch when inputting Gramps data
    '''

    batch_find_id = """
MATCH (u:UserProfile {username: $user})
MATCH (b:Batch) 
    WHERE b.i STARTS WITH $batch_base 
RETURN b.id AS id
    ORDER BY b.id DESC 
    LIMIT 1"""

    batch_create_as_current = """
MATCH (u:UserProfile {username: $user})
MERGE (u) -[:HAS_LOADED {status: 'started'}]-> 
    (b:Batch {id: $batch, file: $file}) -[:COMPLETED]-> 
    (l:Log {status: $status, msg: $msg, size: $size, elapsed: $elapsed})
WITH u, b
    OPTIONAL MATCH (u) -[c:CURRENT_LOAD]-> (:Batch)
        DELETE c
    CREATE (u) -[:CURRENT_LOAD]-> (b)
"""

    batch_add_log = """
MATCH (u:UserProfile {username: $user})
MATCH (u) -[:HAS_LOADED]-> (b:Batch {id:$batch}) -[:COMPLETED*]-> (l0:Log)
CREATE (l0) -[:COMPLETED]-> 
    (l1:Log {status: $status, msg: $msg, size: $size, elapsed: $elapsed})
"""

    batch_log_list = """
MATCH (u:UserProfile {username: $user}) -[:HAS_LOADED]-> 
    (b:Batch {id: $batch}) -[:COMPLETED*]-> (l)
RETURN l.status AS status, l.msg AS msg, l.size AS size, l.elapsed AS elapsed
"""

#TODO Kaikki lauseet geneologisten tietojen lukemiseen ja päivittämiseen

# ==============================================================================

class Cypher_w_handle(object):
    '''
    Cypher clauses for reading and updating database by data from Gramps xml file

    Here the nodes are mostly identified by gramp_handle to recognize the
    original items from the user's Gramps database
    '''

# --- For Event class ---------------------------------------------------------

    event_save = """
MATCH (u:UserProfile) WHERE u.userName=$username
MERGE (e:Event {gramps_handle: $e_attr.gramps_handle})
    SET e = $e_attr
MERGE (u) -[r:REVISION {date: $date}]-> (e)
"""

    event_link_place = """
MATCH (n:Event) WHERE n.gramps_handle=$handle
MATCH (m:Place) WHERE m.gramps_handle=$place_hlink
MERGE (n)-[r:PLACE]->(m)"""

    event_link_note = """
MATCH (e:Event) WHERE e.gramps_handle=$handle
MATCH (n:Note)  WHERE n.gramps_handle=$noteref_hlink
MERGE (e)-[r:NOTE]->(n)"""

    event_link_citation = """
MATCH (n:Event)    WHERE n.gramps_handle=$handle
MATCH (m:Citation) WHERE m.gramps_handle=$citationref_hlink
MERGE (n)-[r:CITATION]->(m)"""

    event_link_media = """
MATCH (n:Event) WHERE n.gramps_handle=$handle
MATCH (m:Media) WHERE m.gramps_handle=$objref_hlink
MERGE (n)-[r:Media]->(m)"""


# --- For Family class --------------------------------------------------------

    family_create = """
MERGE (f:Family {gramps_handle: $f_attr.gramps_handle}) 
    SET f = $f_attr
RETURN id(f) as uniq_id"""

    family_link_father = """
MATCH (n:Family) WHERE n.gramps_handle=$f_handle
MATCH (m:Person) WHERE m.gramps_handle=$p_handle
MERGE (n)-[r:FATHER]->(m)"""

    family_link_mother = """
MATCH (n:Family) WHERE n.gramps_handle=$f_handle
MATCH (m:Person) WHERE m.gramps_handle=$p_handle
MERGE (n)-[r:MOTHER]->(m)"""

    family_link_event = """
MATCH (n:Family) WHERE n.gramps_handle=f_handle
MATCH (m:Event)  WHERE m.gramps_handle=e_handle
MERGE (n)-[r:EVENT]->(m)
    SET r.role = $role"""

    family_link_child = """
MATCH (n:Family) WHERE n.gramps_handle=$f_handle
MATCH (m:Person) WHERE m.gramps_handle=$p_handle
MERGE (n)-[r:CHILD]->(m)"""

    family_link_note = """
MATCH (n:Family) WHERE n.gramps_handle=$f_handle
MATCH (m:Note)   WHERE m.gramps_handle=$n_handle
MERGE (n)-[r:NOTE]->(m)"""

# --- For Media class ---------------------------------------------------------

# --- For Note class ----------------------------------------------------------

# --- For Person class --------------------------------------------------------

    person_create = """
MATCH (u:UserProfile {userName: $username})
MERGE (p:Person {gramps_handle: $p_attr.gramps_handle})
MERGE (u) -[r:REVISION {date: $date}]-> (p)
    SET p = $p_attr
RETURN id(p) as uniq_id"""

    person_link_name = """
CREATE (n:Name) SET n = $n_attr
WITH n
MATCH (p:Person {gramps_handle:$p_handle})
MERGE (p)-[r:NAME]->(n)"""

    person_link_weburl = """
MATCH (p:Person {gramps_handle: $handle}) 
CREATE (p) -[wu:WEBURL]-> (url:Weburl)
    SET url = $u_attr"""

    person_link_event_embedded = """
MATCH (p:Person {gramps_handle: $handle}) 
CREATE (p) -[r:EVENT {role: $role}]-> (e:Event)
    SET e = $e_attr"""

    person_link_event = """
MATCH (p:Person {gramps_handle:$p_handle})
MATCH (e:Event  {gramps_handle:$e_handle})
MERGE (p) -[r:EVENT {role: $role}]-> (e)"""

    person_link_media = """
MATCH (p:Person {gramps_handle: $p_handle})
MATCH (m:Media  {gramps_handle: $m_handle})
MERGE (p) -[r:MEDIA]-> (m)"""

    person_link_note = """
MATCH (p:Person {gramps_handle: $p_handle})
MATCH (n:Note   {gramps_handle: $n_handle})
MERGE (p) -[r:NOTE]-> (n)"""

    person_link_citation = """
MATCH (p:Person)   {gramps_handle: $p_handle})
MATCH (c:Citation) {gramps_handle: $c_handle})
MERGE (p)-[r:CITATION]->(c)"""

# --- For Place class ---------------------------------------------------------

    place_create = """
CREATE (p:Place)
SET p = $p_attr"""

    place_add_name = """
MATCH (p:Place) WHERE p.gramps_handle=$handle
CREATE (n:Place_name)
MERGE (p) -[r:NAME]-> (n)
SET n = $n_attr"""

    place_link_weburl = """
MATCH (n:Place) WHERE n.gramps_handle=$handle
CREATE (n) -[wu:WEBURL]-> (url:Weburl
                {priv: {url_priv}, href: {url_href},
                 type: {url_type}, description: {url_description}})"""

    place_link_hier = """
MATCH (n:Place) WHERE n.gramps_handle=$handle
MATCH (m:Place) WHERE m.gramps_handle=$hlink
MERGE (n) -[r:HIERARCY]-> (m)
SET r = $r_attr"""

    place_link_note = """
MATCH (n:Place) WHERE n.gramps_handle=$handle
MATCH (m:Note) WHERE m.gramps_handle=$hlink
MERGE (n) -[r:NOTE]-> (m)"""



# --- For Source and Citation classes -----------------------------------------


