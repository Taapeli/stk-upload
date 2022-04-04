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
Cypher clauses for models.gramps module

Created on 7.11.2020

@author: jm
'''

class CypherRoot():
    '''
    Cypher clauses for managing Root nodes
    '''

#-pe.neo4j.updateservice.Neo4jUpdateService.ds_aqcuire_lock
    acquire_lock = """MERGE (lock:Lock {id:$lock_id})
SET lock.locked = true
RETURN lock
"""

#-pe.neo4j.updateservice.Neo4jUpdateService.ds_find_last_used_batch_seq
    batch_find_last_id = """
MATCH (b:Root) WHERE b.id STARTS WITH $batch_base
RETURN b.id as bid
    ORDER BY bid DESC LIMIT 1"""

#-pe.neo4j.updateservice.Neo4jUpdateService.ds_find_last_used_batch_seq
    read_batch_id = """
MATCH (n:BatchId) return n
"""
#-pe.neo4j.updateservice.Neo4jUpdateService.ds_new_batch_id
    save_batch_id = """
MERGE (n:BatchId) 
SET n.prefix = $prefix 
SET n.seq = $seq
"""

#-pe.neo4j.updateservice.Neo4jUpdateService.ds_batch_save
    batch_merge = """
MATCH (u:UserProfile {username: $b_attr.user})
    MERGE (u) -[:HAS_LOADED]-> (b:Root {id: $b_attr.id})
    MERGE (u) -[:HAS_ACCESS]-> (b)
    SET b = $b_attr
    SET b.timestamp = timestamp()
RETURN ID(b) AS id"""

#-pe.neo4j.updateservice.Neo4jUpdateService.ds_batch_set_state
    batch_set_state = """
MATCH (u:UserProfile {username: $user})
MATCH (u) -[:HAS_LOADED]-> (b:Root {id: $bid})
    SET b.state=$state
RETURN ID(b) AS id"""

#-pe.neo4j.updateservice.Neo4jUpdateService.ds_batch_set_auditor
    batch_set_auditor = """
MATCH (b:Root {id: $bid}) WHERE b.state IN $states
MATCH (audi:UserProfile {username: $audi})
    SET b.state = "Auditing"
    //MERGE (audi) -[:HAS_ACCESS]-> (b)
    MERGE (audi) -[r:DOES_AUDIT]-> (b)
    SET r.ts_from = timestamp()
RETURN ID(b) AS id"""

#TODO: parameter new_state = "Audit Requested"
#TODO: Create relation DID_AUDIT
    batch_remove_auditor = """
MATCH (b:Root {id: $bid}) WHERE b.state = "Auditing"
OPTIONAL MATCH (oth:UserProfile) -[:DOES_AUDIT]-> (b)
    WHERE oth.username <> $audi
OPTIONAL MATCH (audi:UserProfile {username: $audi}) -[oldr:DOES_AUDIT]-> (b)
WITH b, oth, audi, oldr, COUNT(oth) AS oth_cnt,
    oldr.ts_from AS ts_from, 
    oldr.ts_to AS ts_to
SET (CASE WHEN oth_cnt = 0 THEN b END).state = $new_state
DELETE oldr
RETURN b, oth, audi, oth_cnt, ts_from, ts_to"""
    link_old_auditor = """
MATCH (b:Root) WHERE ID(b) = $uid
MATCH (o:Role) <-[:HAS_ROLE]- (us:User) -[:SUPPLEMENTED]-> (audi:UserProfile)
    WHERE o.name = "audit" and id(audi) = $audi_id
MERGE (audi) -[newr:DID_AUDIT]-> (b)
SET newr.ts_to = timestamp()
SET newr.ts_from = $fromtime
RETURN newr"""

#-bl.batch.root.Root.get_filename
    get_filename = """
MATCH (u:UserProfile{username: $username}) -[:HAS_ACCESS]-> (b:Root {id: $batch_id})
RETURN b.filename, u.username as username"""

#-bl.batch.root.Root.get_batch
    get_batch = """
MATCH (u:UserProfile{username:$username}) -[r:HAS_ACCESS|DOES_AUDIT]-> (b:Root {id:$batch_id})
RETURN b, type(r) AS rel_type"""
     
    list_all = """
MATCH (b:Root) 
RETURN b """

    # List 1) my batches and 2) accepted material collections
    get_root_pallette = """
match (u:UserProfile{username:$user}) -[:HAS_LOADED]-> (root:Root)
return u.username as user,  
    root.material as material_type,
    root.state as state,
    root.id as batch_id,
    root.file as filename,
    root.description as description
union
match (root:Root{state:"Accepted"})
return "" as user, 
    root.material as material_type,
    root.state as state, 
    null as batch_id,
    count(root) as filename,
    "" as description
"""

#-bl.batch.root.Root.get_batches
    get_batches = '''
match (b:Root) 
    where b.user = $user and b.state = $status // "completed"
optional match (b) --> (x)
return b as batch,
    labels(x)[0] as label, count(x) as cnt 
    order by batch.user, batch.id'''

#-bl.batch.root.Root.get_my_batches
    get_materials_accepted = """
match (root:Root) <-[:HAS_ACCESS]- (user:UserProfile)
where root.state='Accepted' and root.material = $m_type
return user, root order by root.id"""

    count_materials_accepted = """
match (root:Root) 
where root.state='Accepted' 
return root.material as material_type, count(*) as nodes order by material_type"""

    get_my_batches = """
where root.state='Candidate' 
return root order by root.id desc"""

#-bl.batch.root.Root.get_user_stats
    get_passed = '''
match (u:UserProfile) --> (b:Root) 
    where u.username = $user and b.state = 'Auditing'
optional match (b) --> (x)
return b as batch, count(x) as cnt 
    order by batch.id'''

#-bl.batch.root.Root.get_batch_stats
#-bl.batch.root.Root.list_empty_batches.Upload.get_stats
#-pe.neo4j.updateservice.Neo4jUpdateService.ds_get_batch (Obsolete!)
    get_single_batch = '''
match (up:UserProfile) -[r:HAS_LOADED]-> (b:Root {id:$batch})
optional match (acc:UserProfile) -[:HAS_ACCESS]-> (b)
    where not up.username = acc.username
optional match (b) --> (x)
optional match (aup:UserProfile) -[aur:DOES_AUDIT]-> (b)
optional match (pap:UserProfile) -[par:DID_AUDIT]-> (b)
return up as profile, b as root,
    labels(x)[0] as label, 
    count(x) as cnt,
    collect(distinct [aup.username,aur.ts_from,aur.ts_to]) as auditors,
    collect(distinct [pap.username,par.ts_from,par.ts_to]) as prev_audits,
    collect(distinct acc.username) as has_access
'''

#-bp.admin.uploads.list_uploads
    get_user_roots_summary = """
match (u:UserProfile) -[:HAS_LOADED]-> (root:Root)
    where u.username = $user
optional match (audi:UserProfile) -[ar:DOES_AUDIT]-> (root)
optional match (root) -[r:OBJ_PERSON]-> (:Person)
with u, audi, root, count(r) as person_count,
    audi.username as auditor,
    ar.ts_from as ts_from,
    ar.ts_to as ts_to
return u.name as u_name, 
    root, person_count,
    collect(distinct [auditor, ts_from, ts_to]) as auditors
order by root.id"""

# #-bl.batch.root.Root.list_empty_batches
#     TODO_get_empty_batches = '''
# MATCH (a:Root) 
# WHERE NOT ((a)-[:OWNS]->()) AND NOT a.id CONTAINS "2019-10"
# RETURN a AS batch ORDER BY a.id DESC'''

    delete_chunk = """
MATCH (:UserProfile{username:$user})
    -[:HAS_LOADED]-> (:Root{id:$batch_id}) -[:OBJ_PERSON|OBJ_FAMILY|OBJ_PLACE|OBJ_SOURCE|OBJ_OTHER]-> (a)
WITH a LIMIT 2000 
    OPTIONAL MATCH (a) -[r]-> (b) WHERE TYPE(r) = "NAME" OR TYPE(r) = "NOTE"
    DETACH DELETE b
    DETACH DELETE a"""

#-bl.batch.root.Root.delete_batch
    delete_batch_node = """
MATCH (:UserProfile{username:$user}) -[:HAS_ACCESS]-> (c:Root{id:$batch_id})
DETACH DELETE c"""

#-pe.neo4j.updateservice.Neo4jUpdateService.ds_obj_remove_gramps_handles
    remove_all_handles = """
match (b:Root {id:$batch_id}) -[*1..3]-> (a)
where a.handle is not null
with distinct a
    remove a.handle
return count(a),labels(a)[0]"""

#-bl.gramps.xml_dom_handler.DOM_handler.add_missing_links
    add_missing_links = """
match (n) where n.handle is not null
match (b:Root{id:$batch_id})
    merge (b)-[:OWNS_OTHER]->(n)
    remove n.handle
return count(n)"""

#-pe.neo4j.updateservice.Neo4jUpdateService.ds_obj_remove_gramps_handles
    find_unlinked_nodes = """
match (n) where n.handle is not null
return  count(n), labels(n)[0]"""


class CypherAudit():
    ''' 
    Query Audit materials
    '''

    get_my_audits = '''
match (b:Root {state:'Auditing', auditor: $oper})
optional match (b) --> (x)
return b, labels(x)[0] as label, count(x) as cnt 
    order by b.user, b.id, label'''

    get_all_audits = '''
match (b:Root{state:'Auditing'})
optional match (b) --> (x)
return b, labels(x)[0] as label, count(x) as cnt 
    order by b.user, b.id, label'''

# # TODO Batch/Audit->Root
#     xxmerge_check = """
# MATCH (p) WHERE id(p) IN $id_list
# OPTIONAL MATCH (x) -[r:OWNS|PASSED]-> (p)
# RETURN ID(x) AS root_id, LABELS(x)[0]+' '+x.id AS root_str, 
#     TYPE(r) AS rel, 
#     ID(p) AS obj_id, LABELS(p)[0] AS obj_label, p.id AS obj_str
#  """

    delete = '''
MATCH (a:Root{id: $batch, state:'Auditing'}) -[:OBJ_PERSON|OBJ_FAMILY|OBJ_PLACE|OBJ_SOURCE|OBJ_OTHER]-> (x)
WHERE labels(x) IN [$labels]
DETACH DELETE x
RETURN count(x)
'''

    delete_names = '''
MATCH (a:Root {id: $batch, state:'Auditing'}) -[:OBJ_PERSON]-> (Person) -[:NAME]-> (x:Name)
DETACH DELETE x
RETURN count(x)
'''

    delete_place_names = '''
MATCH (a:Root{id: $batch, state:'Auditing'}) -[:OBJ_PLACE]-> (Place) -[:NAME]-> (x:Place_name)
DETACH DELETE x
RETURN count(x)
'''

#     delete_citations = '''
# MATCH (a:Audit {id: $batch}) -[:PASSED]-> (Place) -[:NAME]-> (x:Citation) #######
# DETACH DELETE x
# RETURN count(x)
# '''

    delete_audit_node = '''
MATCH (a:Root {id: $batch})
DETACH DELETE a
'''
