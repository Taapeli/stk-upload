#
# Reading and updating Neo4j database
#
# 12.2.2018 - 16.5.2020 / JMä
#

class CypherFamily():
    '''
    Cypher classes for reading and creating Families
    '''

# Get Family node by uuid
    get_a_family_common = '''
MATCH (root:Audit) -[r:PASSED]-> (f:Family {uuid:$f_uuid}) 
RETURN f, type(r) AS root_type, root'''
    get_a_family_own = '''
MATCH (root:Batch {user:$user}) -[r:OWNS]-> (f:Family {uuid:$f_uuid}) 
RETURN f, type(r) AS root_type, root'''

    get_family_parents = """
MATCH (f:Family) -[r:PARENT]-> (pp:Person) WHERE ID(f) = $fuid
    OPTIONAL MATCH (pp) -[:NAME]-> (np:Name {order:0}) 
    OPTIONAL MATCH (pp) -[:EVENT]-> (pbe:Event {type:"Birth"})
    OPTIONAL MATCH (pp) -[:EVENT]-> (pde:Event {type:"Death"})
RETURN r.role AS role, pp AS person, np AS name, pbe AS birth, pde AS death"""

    get_family_children = """
MATCH (f:Family) WHERE ID(f) = $fuid
OPTIONAL MATCH (f) -[:CHILD]- (pc:Person) 
    OPTIONAL MATCH (pc) -[:NAME]-> (nc:Name {order:0}) 
    OPTIONAL MATCH (pc) -[:EVENT]-> (cbe:Event {type:"Birth"})
    OPTIONAL MATCH (pc) -[:EVENT]-> (cde:Event {type:"Death"})
RETURN pc AS person, nc AS name, cbe AS birth, cde AS death
    ORDER BY cbe.date1"""

# Not in use:
    get_family_events = """
MATCH (f:Family) -[:EVENT]-> (fe:Event) WHERE ID(f) = $fuid
OPTIONAL MATCH (fe) -[:PLACE]-> (fep:Place)
RETURN fe as event, fep AS place"""

    get_events_w_places = """
MATCH (x) -[:EVENT]-> (e:Event) WHERE ID(x) = $fuid
OPTIONAL MATCH (e) -[:PLACE]-> (pl:Place)
OPTIONAL MATCH (pl) -[:NAME]-> (pn:Place_name)
OPTIONAL MATCH (pl) -[ri:IS_INSIDE]-> (pi:Place)
OPTIONAL MATCH (pi) -[NAME]-> (pin:Place_name)
WITH e AS event, pl AS place, COLLECT(DISTINCT pn) AS names,
    pi, ri, COLLECT(DISTINCT pin) AS in_names
RETURN event, place, names,
    COLLECT(DISTINCT [pi, ri, in_names]) AS inside"""

    get_family_sources = """
MATCH (f) -[:CITATION]-> (c:Citation)  WHERE ID(f) in $id_list
    OPTIONAL MATCH (c) -[:SOURCE]-> (s:Source)-[:REPOSITORY]-> (re:Repository)
RETURN ID(f) AS src_id,
    re AS repository, s AS source, c AS citation"""

    get_family_notes = """
MATCH (f) -[:NOTE]- (note:Note) WHERE ID(f) in $id_list
    OPTIONAL MATCH (f) 
RETURN ID(f) AS src_id, note"""

    get_dates_parents = """
MATCH (family:Family) WHERE ID(family)=$id
OPTIONAL MATCH (family)-[:PARENT {role:"father"}]-(father:Person)
OPTIONAL MATCH (father)-[:EVENT]-(father_death:Event {type:"Death"})
OPTIONAL MATCH (family)-[:PARENT {role:"mother"}]-(mother:Person)
OPTIONAL MATCH (mother)-[:EVENT]-(mother_death:Event {type:"Death"})
OPTIONAL MATCH (family)-[:EVENT]-(event:Event) WHERE event.type="Marriage"
OPTIONAL MATCH (family)-[:EVENT]-(divorce_event:Event {type:"Divorce"})
RETURN father.sortname AS father_sortname, father_death.date1 AS father_death_date,
       mother.sortname AS mother_sortname, mother_death.date1 AS mother_death_date,
       event.date1 AS marriage_date, divorce_event.date1 AS divorce_date"""

    obsolete_get_family_data = """
MATCH (f:Family) WHERE ID(f) in $id_list
OPTIONAL MATCH (f) -[r:PARENT]-> (pp:Person)
    OPTIONAL MATCH (pp) -[:NAME]-> (np:Name {order:0}) 
    OPTIONAL MATCH (pp) -[:EVENT]-> (pbe:Event {type:"Birth"})
    OPTIONAL MATCH (pp) -[:EVENT]-> (pde:Event {type:"Death"})
OPTIONAL MATCH (f) -[:CHILD]- (pc:Person) 
    OPTIONAL MATCH (pc) -[:NAME]-> (nc:Name {order:0}) 
    OPTIONAL MATCH (pc) -[:EVENT]-> (cbe:Event {type:"Birth"})
    OPTIONAL MATCH (pc) -[:EVENT]-> (cde:Event {type:"Death"})
WITH f, r, pp, np, pbe, pde, pc, nc, cbe, cde ORDER BY cbe.date1
    OPTIONAL MATCH (f) -[:EVENT]-> (fe:Event)
    OPTIONAL MATCH (fe) -[:PLACE]-> (fep:Place)
    OPTIONAL MATCH (f) -[:CITATION]-> (fc:Citation) -[:SOURCE]-> (fs:Source)-[:REPOSITORY]-> (fre:Repository)
    OPTIONAL MATCH (fe) -[:CITATION]-> (c:Citation) -[:SOURCE]-> (s:Source)-[:REPOSITORY]-> (re:Repository)
    OPTIONAL MATCH (f) -[:NOTE]- (note:Note) 
RETURN //f, 
    COLLECT(DISTINCT [fe, fep]) AS family_event,
    COLLECT(DISTINCT [r.role, pp, np, pbe, pde]) AS parent, 
    COLLECT(DISTINCT [pc, nc, cbe, cde]) AS child, 
    // COUNT(DISTINCT pc) AS no_of_children,
    COLLECT(DISTINCT [re, s, c]) + COLLECT(DISTINCT [fre, fs, fc]) AS sources,
    COLLECT(DISTINCT note) AS note"""
    
    get_person_families = """
MATCH (p:Person) <-- (family:Family) WHERE p.uuid = $p_uuid
MATCH (family) -[r]-> (person:Person)
OPTIONAL MATCH (person) -[:EVENT]-> (birth:Event {type:'Birth'}) 
RETURN family, TYPE(r) AS type, r.role AS role, person, birth 
ORDER BY family, person.birth_high"""

# ----- Family load in Batch

    create_to_batch = """
MATCH (b:Batch {id: $batch_id})
MERGE (b) -[r:OWNS]-> (f:Family {handle: $f_attr.handle}) 
    SET f = $f_attr
RETURN ID(f) as uniq_id"""

    link_parent = """
MATCH (n:Family) WHERE n.handle=$f_handle
MATCH (m:Person) WHERE m.handle=$p_handle
MERGE (n) -[r:PARENT {role:$role}]-> (m)"""

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

    set_dates_sortname = """
MATCH (family:Family) WHERE ID(family) = $id
SET family += $f_attr"""

