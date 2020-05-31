'''
Cypher clauses for models.gramps module

Created on 21.3.2018

@author: jm
'''

class Cypher_batch():
    '''
    Cypher clauses for managing Batch nodes
    '''

    batch_find_id = """
MATCH (b:Batch) WHERE b.id STARTS WITH $batch_base
RETURN b.id AS bid
    ORDER BY bid DESC LIMIT 1"""

    batch_create = """
MATCH (u:UserProfile {username: $b_attr.user})
MERGE (u) -[:HAS_LOADED]-> (b:Batch {id: $b_attr.id})
MERGE (u) -[:HAS_ACCESS]-> (b)
    SET b = $b_attr
    SET b.timestamp = timestamp()"""

    batch_complete = """
MATCH (u:UserProfile {username: $user})
MATCH (u) -[:HAS_LOADED]-> (b:Batch {id: $bid})
    SET b.status="completed"
"""
#Removed 2.5.2020
# WITH u, b
#     OPTIONAL MATCH (u) -[c:CURRENT_LOAD]-> (:Batch)
#         DELETE c
#     MERGE (u) -[:CURRENT_LOAD]-> (b)
#Moved to models.gen.batch_audit / 3.2.2020/JMä
#     batch_list = """
#     batch_list_all = """
#     batch_delete = """
#     get_batch_filename = """
#Removed / 3.2.2020/JMä
#     batch_count = """
#     batch_person_count = """

# ==============================================================================

    '''
    Cypher clauses for reading and updating database by data from Gramps xml file

    Here the nodes are mostly identified by gramp_handle to recognize the
    original items from the user's Gramps database
    '''

class Cypher_event_w_handle():
    """ For Event class """

    create_to_batch = """
MATCH (b:Batch {id: $batch_id})
MERGE (b) -[r:OWNS]-> (e:Event {handle: $e_attr.handle})
    SET e = $e_attr
RETURN ID(e) as uniq_id"""

    link_place = """
MATCH (n:Event) WHERE n.handle=$handle
MATCH (m:Place) WHERE m.handle=$place_hlink
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

#     link_media = """
# MATCH (e:Event {handle: $handle})
# MATCH (m:Media  {handle: $m_handle})
#   CREATE (e) -[r:MEDIA]-> (m)
#     SET r = $r_attr"""


class Cypher_family_w_handle():
    """ For Family class """

    create_to_batch = """
MATCH (b:Batch {id: $batch_id})
MERGE (b) -[r:OWNS]-> (f:Family {handle: $f_attr.handle}) 
    SET f = $f_attr
RETURN ID(f) as uniq_id"""

#    create = """
#MERGE (f:Family {handle: $f_attr.handle}) 
#    SET f = $f_attr
#RETURN ID(f) as uniq_id"""

    link_parent = """
MATCH (n:Family) WHERE n.handle=$f_handle
MATCH (m:Person) WHERE m.handle=$p_handle
MERGE (n) -[r:PARENT {role:$role}]-> (m)"""
#     link_father = """
# MATCH (n:Family) WHERE n.handle=$f_handle
# MATCH (m:Person) WHERE m.handle=$p_handle
# MERGE (n)-[r:FATHER]->(m)"""
# 
#     link_mother = """
# MATCH (n:Family) WHERE n.handle=$f_handle
# MATCH (m:Person) WHERE m.handle=$p_handle
# MERGE (n)-[r:MOTHER]->(m)"""

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
CREATE (n)-[r:NOTE]->(m)"""

    link_citation = """
MATCH (n:Family) WHERE n.handle=$f_handle
MATCH (m:Citation) WHERE m.handle=$c_handle
CREATE (n)-[r:CITATION]->(m)"""


class Cypher_media_in_batch():
    """ For Media class.

        Using UUID as key
    """

    # Find the batch like '2019-02-24.006' and connect new object to that Batch
    create = """
MATCH (u:Batch {id:$bid})
MERGE (u) -[:OWNS]-> (a:Media {uuid:$uuid})
    SET a += $m_attr
RETURN ID(a) as uniq_id"""

# class Cypher_media_w_handle():
#     """ For Media class """
#     create = """
# MERGE (m:Media {handle: $m_attr.handle}) 
#     SET m = $m_attr"""


class Cypher_note_in_batch():
    """ A Note is added to given batch or parent node 
    
        # MATCH (u:Batch {id:$bid}) -[*]-> (a {handle:$parent_handle})
    """

    # Find the batch like '2019-02-24.006' and connect Note in that Batch
    create = """
MATCH (u:Batch {id:$bid})
CREATE (u) -[:OWNS]-> (n:Note) 
    SET n = $n_attr
RETURN ID(n)"""

    # Find a known parent node with uniq_id and connect a new Note to it
    create_as_leaf = """
MATCH (a) WHERE ID(a) = $parent_id
CREATE (a) -[:NOTE]-> (n:Note) 
    SET n = $n_attr
RETURN ID(n)"""


class Cypher_note_w_handle():
    """ For Note class """

# create_in_batch = """MATCH (u:Batch {id:$bid}) -[*]-> (x {handle:$parent_id})

    create = """
CREATE (n:Note {handle: $n_attr.handle}) 
    SET n = $n_attr
RETURN ID(n)"""

    create_as_leaf = """
MATCH (a) WHERE ID(a) = $parent_id
MERGE (a) -[:NOTE]-> (n:Note) 
    SET n = $n_attr
RETURN ID(n)"""

    merge_as_leaf = """
MATCH (a) WHERE ID(a) = $parent_id
MERGE (a) -[:NOTE]-> (n:Note {handle: $n_attr.handle}) 
    SET n = $n_attr
RETURN ID(n)"""


class Cypher_person_w_handle():
    """ For Person class """

    create_to_batch = """
MATCH (b:Batch {id: $batch_id})
MERGE (p:Person {handle: $p_attr.handle})
MERGE (b) -[r:OWNS]-> (p)
    SET p = $p_attr
RETURN ID(p) as uniq_id"""

    link_name = """
CREATE (n:Name) SET n = $n_attr
WITH n
MATCH (p:Person {handle:$p_handle})
MERGE (p)-[r:NAME]->(n)"""

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
  CREATE (p) -[r:MEDIA]-> (m)
    SET r = $r_attr"""

# use models.gen.cypher.Cypher_name (there is no handle)

    link_citation = """
MATCH (p:Person   {handle: $p_handle})
MATCH (c:Citation {handle: $c_handle})
MERGE (p)-[r:CITATION]->(c)"""

    link_note = """
MATCH (n) WHERE n.handle=$p_handle
MATCH (m:Note)   WHERE m.handle=$n_handle
CREATE (n)-[r:NOTE]->(m)"""



class Cypher_place_in_batch():
    """ For Place class """

    # Find the batch like '2019-02-24.006' and connect new object to that Batch
    create = """
MATCH (u:Batch {id:$batch_id})
CREATE (new_pl:Place)
    SET new_pl = $p_attr
CREATE (u) -[:OWNS]-> (new_pl) 
RETURN ID(new_pl) as uniq_id"""

    # Set properties for an existing Place and connect it to Batch
    complete = """
MATCH (u:Batch {id:$batch_id})
MATCH (pl:Place) WHERE ID(pl) = $plid
    SET pl += $p_attr
CREATE (u) -[:OWNS]-> (pl)"""
# plid=plid, p_attr=pl_attr
#MERGE (u) -[:OWNS]-> (pl) <-[r:IS_INSIDE]- (plu:Place {handle: $up_handle}) 
#RETURN ID(pl) as uniq_id"""

    add_name = """
MATCH (pl:Place) WHERE id(pl) = $pid
CREATE (pl) -[r:NAME {order:$order}]-> (n:Place_name)
    SET n = $n_attr
RETURN ID(n) AS uniq_id"""

    # Link to a known upper Place
    link_hier = """
MATCH (pl:Place) WHERE id(pl) = $plid
MATCH (up:Place) WHERE id(up) = $up_id
MERGE (pl) -[r:IS_INSIDE]-> (up)
    SET r = $r_attr"""

    # Link to a new dummy upper Place
    link_create_hier = """
MATCH (pl:Place) WHERE id(pl) = $plid
CREATE (new_pl:Place)
    SET new_pl.handle = $up_handle
CREATE (pl) -[r:IS_INSIDE]-> (new_pl)
    SET r = $r_attr
return ID(new_pl) as uniq_id"""

    add_urls = """
MATCH (u:Batch {id:$batch_id})
CREATE (u) -[:OWNS]-> (n:Note) 
    SET n = $n_attr
WITH n
    MATCH (pl:Place) WHERE id(pl) = $pid
    MERGE (pl) -[r:NOTE]-> (n)"""

    link_note = """
MATCH (pl:Place) WHERE id(pl) = $pid
MATCH (n:Note)  WHERE n.handle=$hlink
CREATE (pl) -[r:NOTE]-> (n)"""

    link_media = """
MATCH (p:Place {handle: $p_handle})
MATCH (m:Media  {handle: $m_handle})
  CREATE (p) -[r:MEDIA]-> (m)
    SET r = $r_attr"""


# class Cypher_place_w_handle():
#     """ For Place class """

#     create = """
# CREATE (p:Place)
#     SET p = $p_attr
# RETURN id(p) AS uniq_id"""

#     add_name = """
# MATCH (p:Place) WHERE p.handle=$handle
# CREATE (n:Place_name)
# MERGE (p) -[r:NAME]-> (n)
# SET n = $n_attr"""

#     link_hier = """
# MATCH (n:Place) WHERE n.handle=$handle
# MATCH (m:Place) WHERE m.handle=$hlink
# MERGE (n) -[r:IS_INSIDE]-> (m)
# SET r = $r_attr"""

#     link_note = """
# MATCH (n:Place) WHERE n.handle=$handle
# MATCH (m:Note)  WHERE m.handle=$hlink
# MERGE (n) -[r:NOTE]-> (m)"""



class Cypher_source_w_handle():
    """ For Source class """

#TODO: Source, Citation and Repository: sulautettava 
#      saman omistajan duplikaatit gramps_handlen mukaan
#      Nyt tulee aina uusi instanssi

    create_to_batch = """
MATCH (b:Batch {id: $batch_id})
MERGE (b) -[r:OWNS]-> (s:Source {handle: $s_attr.handle}) 
    SET s = $s_attr
RETURN ID(s) as uniq_id"""
#     create = """
# MERGE (s:Source {handle: $s_attr.handle})
#     SET s = $s_attr
# RETURN ID(s) as uniq_id"""

    link_note = """
MATCH (n:Source) WHERE n.handle=$handle
MATCH (m:Note)   WHERE m.handle=$hlink
CREATE (n) -[r:NOTE]-> (m)"""

    link_repository = """
MATCH (n:Source) WHERE n.handle=$handle
MATCH (m:Repository) WHERE m.handle=$hlink
MERGE (n) -[r:REPOSITORY {medium:$medium}]-> (m)"""


class Cypher_citation_w_handle():
    """ For Citation class """

    create_to_batch = """
MATCH (b:Batch {id: $batch_id})
MERGE (b) -[r:OWNS]-> (c:Citation {handle: $c_attr.handle}) 
    SET c = $c_attr
RETURN ID(c) as uniq_id"""

#     create = """
# CREATE (n:Citation)
#     SET n = $c_attr
# RETURN ID(n) as uniq_id"""

    link_note = """
MERGE (n:Citation {handle: $handle})
MERGE (m:Note     {handle: $hlink})
CREATE (n) -[r:NOTE]-> (m)"""

    link_source = """
MERGE (n:Citation {handle: $handle})
MERGE (m:Source   {handle: $hlink})
MERGE (n) -[r:SOURCE]-> (m)"""


class Cypher_repository_in_batch():
    """ For Repository class """

    # Find the batch like '2019-02-24.006' and connect new object to that Batch
    create = """
MATCH (u:Batch {id:$bid})
CREATE (u) -[:OWNS]-> (a:Repository) 
    SET a = $r_attr
RETURN ID(a) as uniq_id"""


class Cypher_mixed():
    
    remove_handles = """
match (b:Batch {id:$batch_id}) -[*]-> (a)
    remove a.handle
return count(a),labels(a)[0]"""

    add_links = """
match (n) where exists (n.handle)
match (b:Batch{id:$batch_id})
    merge (b)-[:OWNS_OTHER]->(n)
    remove n.handle
return count(n)"""

    set_mediapath = """
match (b:Batch{id:$batch_id})
set b.mediapath = $path"""


class Cypher_x():
    """ For Batch and Log classes """

    batch_create = '''
MATCH (p:UserProfile {username:$user}); 
CREATE (p) -[:HAS_LOADED]-> (b:Batch {id:$bid, status:$status}) 
RETURN ID(b) AS uniq_id'''
