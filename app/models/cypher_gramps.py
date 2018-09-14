'''
Cypher clauses for models.gramps module

Created on 21.3.2018

@author: jm
'''

class Cypher_batch(object):
    '''
    Cypher clauses for managing Batch and Log nodes
    '''

    batch_find_id = """
MATCH (u:UserProfile {userName: $user})
MATCH (u) -[:HAS_LOADED]-> (b:Batch) 
    WHERE b.id STARTS WITH $batch_base 
RETURN b.id AS bid
    ORDER BY b.bid DESC 
    LIMIT 1"""

    batch_create = """
MATCH (u:UserProfile {userName: $b_attr.user})
MERGE (u) -[:HAS_LOADED {status: $b_attr.status}]-> (b:Batch {id: $b_attr.id})
    SET b = $b_attr"""

    batch_complete = """
MATCH (u:UserProfile {userName: $user})
MATCH (u) -[r1:HAS_LOADED]-> (b:Batch {id: $bid})
    SET r1.status="completed"
    SET b.status="completed"
WITH u, b
CREATE (b) -[r:COMPLETED]-> (l:Log)
    SET l = l_attr // {status: $status, msg: $msg, size: $size, elapsed: $elapsed}
WITH u, b
    OPTIONAL MATCH (u) -[c:CURRENT_LOAD]-> (:Batch)
        DELETE c
    CREATE (u) -[:CURRENT_LOAD]-> (b)
"""
    batch_x = """
MATCH (u:UserProfile {userName: $user})
MERGE (u) -[:HAS_LOADED {status: $status}]-> 
    (b:Batch {id: $batch, file: $file}) -[:COMPLETED]-> 
    (l:Log {status: $status, msg: $msg, size: $size, elapsed: $elapsed})
WITH u, b
    OPTIONAL MATCH (u) -[c:CURRENT_LOAD]-> (:Batch)
        DELETE c
    CREATE (u) -[:CURRENT_LOAD]-> (b)
"""

    batch_add_log = """
MATCH (u:UserProfile {userName: $user})
MATCH (u) -[:HAS_LOADED]-> (b:Batch {id:$batch}) -[:COMPLETED*]-> (l0:Log)
CREATE (l0) -[:COMPLETED]-> 
    (l1:Log {status: $status, msg: $msg, size: $size, elapsed: $elapsed})
"""

    batch_log_list = """
MATCH (u:UserProfile {userName: $user}) -[:HAS_LOADED]-> 
    (b:Batch {id: $batch}) -[:COMPLETED*]-> (l)
RETURN l.status AS status, l.msg AS msg, l.size AS size, l.elapsed AS elapsed
"""

#TODO Kaikki lauseet geneologisten tietojen lukemiseen ja päivittämiseen Batchin kautta puuttuvat

# ==============================================================================

    '''
    Cypher clauses for reading and updating database by data from Gramps xml file

    Here the nodes are mostly identified by gramp_handle to recognize the
    original items from the user's Gramps database
    '''


class Cypher_event_w_handle():
    """ For Event class """

    create = """
MATCH (u:UserProfile) WHERE u.userName=$username
MERGE (e:Event {handle: $e_attr.handle})
    SET e = $e_attr
MERGE (u) -[r:REVISION {date: $date}]-> (e)
"""

    link_place = """
MATCH (n:Event) WHERE n.handle=$handle
MATCH (m:Place) WHERE m.handle=$place_hlink
MERGE (n)-[r:PLACE]->(m)"""

    link_notes = """
match (n:Note)  where n.handle in $note_handles
with n
    match (e:Event)  where e.handle=$handle
    merge (e) -[r:NOTE]-> (n)"""
#return count(r) as cnt"""

    link_citations = """
match (c:Citation) where c.handle in $citation_handles
with c
    match (e:Event)  where e.handle=$handle
    merge (e) -[r:CITATION]-> (c)"""

    link_media = """
MATCH (n:Event) WHERE n.handle=$handle
MATCH (m:Media) WHERE m.handle=$objref_hlink
MERGE (n)-[r:Media]->(m)"""


class Cypher_family_w_handle():
    """ For Family class """

    create = """
MERGE (f:Family {handle: $f_attr.handle}) 
    SET f = $f_attr
RETURN ID(f) as uniq_id"""

    link_father = """
MATCH (n:Family) WHERE n.handle=$f_handle
MATCH (m:Person) WHERE m.handle=$p_handle
MERGE (n)-[r:FATHER]->(m)"""

    link_mother = """
MATCH (n:Family) WHERE n.handle=$f_handle
MATCH (m:Person) WHERE m.handle=$p_handle
MERGE (n)-[r:MOTHER]->(m)"""

    link_event = """
MATCH (n:Family) WHERE n.handle=$f_handle
MATCH (m:Event)  WHERE m.handle=$e_handle
MERGE (n)-[r:EVENT]->(m)
    SET r.role = $role"""

    link_child = """
MATCH (n:Family) WHERE n.handle=$f_handle
MATCH (m:Person) WHERE m.handle=$p_handle
MERGE (n)-[r:CHILD]->(m)"""

    link_note = """
MATCH (n:Family) WHERE n.handle=$f_handle
MATCH (m:Note)   WHERE m.handle=$n_handle
MERGE (n)-[r:NOTE]->(m)"""


class Cypher_media_w_handle():
    """ For Media class """

    create = """
MERGE (m:Media {handle: $m_attr.handle}) 
    SET m = $m_attr"""



class Cypher_note_w_handle():
    """ For Note class """

    create = """
MERGE (n:Note {handle: $n_attr.handle}) 
    SET n = $n_attr"""


class Cypher_person_w_handle():
    """ For Person class """

    create = """
MATCH (u:UserProfile {userName: $username})
MERGE (p:Person {handle: $p_attr.handle})
MERGE (u) -[r:REVISION {date: $date}]-> (p)
    SET p = $p_attr
RETURN ID(p) as uniq_id"""

    link_name = """
CREATE (n:Name) SET n = $n_attr
WITH n
MATCH (p:Person {handle:$p_handle})
MERGE (p)-[r:NAME]->(n)"""

    link_weburl = """
MATCH (p:Person {handle: $p_handle}) 
CREATE (p) -[wu:WEBURL]-> (url:Weburl)
    SET url = $u_attr"""

    link_event_embedded = """
MATCH (p:Person {handle: $handle}) 
CREATE (p) -[r:EVENT {role: $role}]-> (e:Event)
    SET e = $e_attr"""

    link_event = """
MATCH (p:Person {handle:$p_handle})
MATCH (e:Event  {handle:$e_handle})
MERGE (p) -[r:EVENT {role: $role}]-> (e)"""

    link_media = """
MATCH (p:Person {handle: $p_handle})
MATCH (m:Media  {handle: $m_handle})
MERGE (p) -[r:MEDIA]-> (m)"""

    link_note = """
MATCH (p:Person {handle: $p_handle})
MATCH (n:Note   {handle: $n_handle})
MERGE (p) -[r:NOTE]-> (n)"""

    link_citation = """
MATCH (p:Person   {handle: $p_handle})
MATCH (c:Citation {handle: $c_handle})
MERGE (p)-[r:CITATION]->(c)"""


class Cypher_place_w_handle():
    """ For Place class """

    create = """
CREATE (p:Place)
SET p = $p_attr"""

    add_name = """
MATCH (p:Place) WHERE p.handle=$handle
CREATE (n:Place_name)
MERGE (p) -[r:NAME]-> (n)
SET n = $n_attr"""

    link_weburl = """
MATCH (n:Place) WHERE n.handle=$handle
CREATE (n) -[wu:WEBURL]-> (url:Weburl
                {priv: {url_priv}, href: {url_href},
                 type: {url_type}, description: {url_description}})"""

    link_hier = """
MATCH (n:Place) WHERE n.handle=$handle
MATCH (m:Place) WHERE m.handle=$hlink
MERGE (n) -[r:HIERARCY]-> (m)
SET r = $r_attr"""

    link_note = """
MATCH (n:Place) WHERE n.handle=$handle
MATCH (m:Note)  WHERE m.handle=$hlink
MERGE (n) -[r:NOTE]-> (m)"""



class Cypher_source_w_handle():
    """ For Source class """

#TODO: Source, Citation and Repository: sulautettava 
#      saman omistajan duplikaatit gramps_handlen mukaan
#      Nyt tulee aina uusi instanssi


    create = """
CREATE (s:Source)
SET s = $s_attr"""

    link_note = """
MATCH (n:Source) WHERE n.handle=$handle
MATCH (m:Note)   WHERE m.handle=$hlink
MERGE (n) -[r:NOTE]-> (m)"""

    link_repository = """
MATCH (n:Source) WHERE n.handle=$handle
MATCH (m:Repository) WHERE m.handle=$hlink
MERGE (n) -[r:REPOSITORY]-> (m)"""

    set_repository_medium = """
MATCH (n:Source) -[r:REPOSITORY]-> (m) 
    WHERE n.handle=$handle
SET r.medium=$medium"""


class Cypher_citation_w_handle():
    """ For Citation class """

    create = """
CREATE (n:Citation)
    SET n = $c_attr"""

    link_note = """
MERGE (n:Citation {handle: $handle})
MERGE (m:Note     {handle: $hlink})
MERGE (n) -[r:NOTE]-> (m)"""

    link_source = """
MERGE (n:Citation {handle: $handle})
MERGE (m:Source   {handle: $hlink})
MERGE (n) -[r:SOURCE]-> (m)"""


class Cypher_repository_w_handle():
    """ For Repository class """

    create = """
CREATE (r:Repository)
SET r = $r_attr
return id(r) as uniq_id"""


class Cypher_x():
    """ For Batch and Log classes """

    batch_create = '''
MATCH (p:UserProfile {userName:$user}); 
CREATE (p) -[:HAS_LOADED]-> (b:Batch {id:$bid, status:$status}) 
RETURN ID(b) AS uniq_id'''
