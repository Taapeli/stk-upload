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
MERGE (e:Event {gramps_handle: $e_attr.gramps_handle})
    SET e = $e_attr
MERGE (u) -[r:REVISION {date: $date}]-> (e)
"""

    link_place = """
MATCH (n:Event) WHERE n.gramps_handle=$handle
MATCH (m:Place) WHERE m.gramps_handle=$place_hlink
MERGE (n)-[r:PLACE]->(m)"""

    link_note = """
MATCH (e:Event) WHERE e.gramps_handle=$handle
MATCH (n:Note)  WHERE n.gramps_handle=$noteref_hlink
MERGE (e)-[r:NOTE]->(n)"""

    link_citation = """
MATCH (n:Event)    WHERE n.gramps_handle=$handle
MATCH (m:Citation) WHERE m.gramps_handle=$citationref_hlink
MERGE (n)-[r:CITATION]->(m)"""

    link_media = """
MATCH (n:Event) WHERE n.gramps_handle=$handle
MATCH (m:Media) WHERE m.gramps_handle=$objref_hlink
MERGE (n)-[r:Media]->(m)"""


class Cypher_family_w_handle():
    """ For Family class """

    create = """
MERGE (f:Family {gramps_handle: $f_attr.gramps_handle}) 
    SET f = $f_attr
RETURN id(f) as uniq_id"""

    link_father = """
MATCH (n:Family) WHERE n.gramps_handle=$f_handle
MATCH (m:Person) WHERE m.gramps_handle=$p_handle
MERGE (n)-[r:FATHER]->(m)"""

    link_mother = """
MATCH (n:Family) WHERE n.gramps_handle=$f_handle
MATCH (m:Person) WHERE m.gramps_handle=$p_handle
MERGE (n)-[r:MOTHER]->(m)"""

    link_event = """
MATCH (n:Family) WHERE n.gramps_handle=f_handle
MATCH (m:Event)  WHERE m.gramps_handle=e_handle
MERGE (n)-[r:EVENT]->(m)
    SET r.role = $role"""

    link_child = """
MATCH (n:Family) WHERE n.gramps_handle=$f_handle
MATCH (m:Person) WHERE m.gramps_handle=$p_handle
MERGE (n)-[r:CHILD]->(m)"""

    link_note = """
MATCH (n:Family) WHERE n.gramps_handle=$f_handle
MATCH (m:Note)   WHERE m.gramps_handle=$n_handle
MERGE (n)-[r:NOTE]->(m)"""


class Cypher_media_w_handle():
    """ For Media class """

    create = """
MERGE (m:Media {gramps_handle: $m_attr.gramps_handle}) 
    SET m = $m_attr"""



class Cypher_note_w_handle():
    """ For Note class """

    create = """
MERGE (n:Note {gramps_handle: $n_attr.gramps_handle}) 
    SET n = $n_attr"""


class Cypher_person_w_handle():
    """ For Person class """

    create = """
MATCH (u:UserProfile {userName: $username})
MERGE (p:Person {gramps_handle: $p_attr.gramps_handle})
MERGE (u) -[r:REVISION {date: $date}]-> (p)
    SET p = $p_attr
RETURN ID(p) as uniq_id"""

    link_name = """
CREATE (n:Name) SET n = $n_attr
WITH n
MATCH (p:Person {gramps_handle:$p_handle})
MERGE (p)-[r:NAME]->(n)"""

    link_weburl = """
MATCH (p:Person {gramps_handle: $handle}) 
CREATE (p) -[wu:WEBURL]-> (url:Weburl)
    SET url = $u_attr"""

    link_event_embedded = """
MATCH (p:Person {gramps_handle: $handle}) 
CREATE (p) -[r:EVENT {role: $role}]-> (e:Event)
    SET e = $e_attr"""

    link_event = """
MATCH (p:Person {gramps_handle:$p_handle})
MATCH (e:Event  {gramps_handle:$e_handle})
MERGE (p) -[r:EVENT {role: $role}]-> (e)"""

    link_media = """
MATCH (p:Person {gramps_handle: $p_handle})
MATCH (m:Media  {gramps_handle: $m_handle})
MERGE (p) -[r:MEDIA]-> (m)"""

    link_note = """
MATCH (p:Person {gramps_handle: $p_handle})
MATCH (n:Note   {gramps_handle: $n_handle})
MERGE (p) -[r:NOTE]-> (n)"""

    link_citation = """
MATCH (p:Person)   {gramps_handle: $p_handle})
MATCH (c:Citation) {gramps_handle: $c_handle})
MERGE (p)-[r:CITATION]->(c)"""


class Cypher_place_w_handle():
    """ For Place class """

    create = """
CREATE (p:Place)
SET p = $p_attr"""

    add_name = """
MATCH (p:Place) WHERE p.gramps_handle=$handle
CREATE (n:Place_name)
MERGE (p) -[r:NAME]-> (n)
SET n = $n_attr"""

    link_weburl = """
MATCH (n:Place) WHERE n.gramps_handle=$handle
CREATE (n) -[wu:WEBURL]-> (url:Weburl
                {priv: {url_priv}, href: {url_href},
                 type: {url_type}, description: {url_description}})"""

    link_hier = """
MATCH (n:Place) WHERE n.gramps_handle=$handle
MATCH (m:Place) WHERE m.gramps_handle=$hlink
MERGE (n) -[r:HIERARCY]-> (m)
SET r = $r_attr"""

    link_note = """
MATCH (n:Place) WHERE n.gramps_handle=$handle
MATCH (m:Note)  WHERE m.gramps_handle=$hlink
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
MATCH (n:Source) WHERE n.gramps_handle=$handle
MATCH (m:Note)   WHERE m.gramps_handle=$hlink
MERGE (n) -[r:NOTE]-> (m)"""

    link_repository = """
MATCH (n:Source) WHERE n.gramps_handle=$handle
MATCH (m:Repository) WHERE m.gramps_handle=$hlink
MERGE (n) -[r:REPOSITORY]-> (m)"""

    set_repository_medium = """
MATCH (n:Source) -[r:REPOSITORY]-> (m) 
    WHERE n.gramps_handle=$handle
SET r.medium=$medium"""


class Cypher_citation_w_handle():
    """ For Citation class """

    create = """
CREATE (n:Citation)
    SET n = $c_attr"""

    link_note = """
MERGE (n:Citation {gramps_handle: $handle})
MERGE (m:Note     {gramps_handle: $hlink})
MERGE (n) -[r:NOTE]-> (m)"""

    link_source = """
MERGE (n:Citation {gramps_handle: $handle})
MERGE (m:Source   {gramps_handle: $hlink})
MERGE (n) -[r:SOURCE]-> (m)"""


class Cypher_repository_w_handle():
    """ For Repository class """

    create = """
CREATE (r:Repository)
SET r = $r_attr"""
