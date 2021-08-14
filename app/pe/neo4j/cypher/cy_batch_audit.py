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

    acquire_lock = """MERGE (lock:Lock {id:$lock_id})
SET lock.locked = true
RETURN lock
"""

    batch_find_last_id = """
MATCH (b:Root) WHERE b.id STARTS WITH $batch_base
RETURN b.id as bid
    ORDER BY bid DESC LIMIT 1"""

    read_batch_id = """
MATCH (n:BatchId) return n
"""

    save_batch_id = """
MERGE (n:BatchId) 
SET n.prefix = $prefix 
SET n.seq = $seq
"""

    batch_create = """
MATCH (u:UserProfile {username: $b_attr.user})
MERGE (u) -[:HAS_LOADED]-> (b:Root {id: $b_attr.id})
MERGE (u) -[:HAS_ACCESS]-> (b)
    SET b = $b_attr
    SET b.timestamp = timestamp()
RETURN ID(b) AS id"""

    batch_set_status = """
MATCH (u:UserProfile {username: $user})
MATCH (u) -[:HAS_LOADED]-> (b:Root {id: $bid})
    SET b.state=$status
RETURN ID(b) AS id"""

    get_filename = """
MATCH (b:Root {id: $batch_id, user: $username}) 
RETURN b.file"""

    list_all = """
MATCH (b:Root) 
RETURN b """

    get_batches = '''
match (b:Root) 
    where b.user = $user and b.state = $status // "completed"
optional match (b) --> (x)
return b as batch,
    labels(x)[0] as label, count(x) as cnt 
    order by batch.user, batch.id'''

    get_passed = '''
match (b:Root) 
    where b.user = $user and b.state = 'Auditing'
optional match (b) --> (x)
return b as batch, count(x) as cnt 
    order by batch.id'''

    get_single_batch = '''
match (up:UserProfile) -[r:HAS_LOADED]-> (b:Root {id:$batch}) 
optional match (b) --> (x)
return up as profile, b as batch, labels(x)[0] as label, count(x) as cnt'''

    get_user_batch_names = '''
match (b:Root) where b.user = $user
optional match (b) -[r:OBJ_PERSON]-> (:Person)
return b.id as batch, b.timestamp as timestamp, b.status as status,
    count(r) as persons 
    order by batch'''

# TODO Batch->Root:
    get_user_batch_summary = """
match (b:Root) where b.user = $user
and b.state <> 'Audit Requested'
optional match (b) -[r:OBJ_PERSON]-> (:Person)
with b, count(r) as person_count
    optional match (b) -[:AFTER_AUDIT]-> (a:Audit) -[ar:PASSED]-> (:Person)
return 
    b, 
    person_count,  
    count(ar) as audit_count
order by b.id"""

    TODO_get_empty_batches = '''
MATCH (a:Root) 
WHERE NOT ((a)-[:OWNS]->()) AND NOT a.id CONTAINS "2019-10"
RETURN a AS batch ORDER BY a.id DESC'''

# TODO Batch->Root:
#   delete = """
# MATCH (u:UserProfile{username:$username}) -[:HAS_LOADED]-> (b:Root{id:$batch_id}) 
# OPTIONAL MATCH (b) -[*]-> (n)
# WITH b, n LIMIT $limit
# DETACH DELETE b, n"""

    # Safe Root removal in reasonable chunks:
    #    a) Nodes pointed by OWNS, 
    #    b) following nodes by relation NAME or NOTE
    #    Not Root node self
    delete_chunk = """
MATCH (:UserProfile{username:$user})
    -[:HAS_LOADED]-> (:Root{id:$batch_id}) -[:OWNS]-> (a)
WITH a LIMIT 1000 
    OPTIONAL MATCH (a) -[r]-> (b) WHERE TYPE(r) = "NAME" OR TYPE(r) = "NOTE"
    DETACH DELETE b
    DETACH DELETE a"""
    delete_batch_node = """
MATCH (:UserProfile{username:$user}) -[:HAS_LOADED]-> (c:Root{id:$batch_id})
DETACH DELETE c"""

    remove_all_handles = """
match (b:Root {id:$batch_id}) -[*2..3]-> (a)
where a.handle is not null
with distinct a
    remove a.handle
return count(a),labels(a)[0]"""

# TODO Batch->Root:
    add_missing_links = """
match (n) where n.handle is not null
match (b:Root{id:$batch_id})
    merge (b)-[:OWNS_OTHER]->(n)
    remove n.handle
return count(n)"""

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

# TODO Batch/Audit->Root
    xxmerge_check = """
MATCH (p) WHERE id(p) IN $id_list
OPTIONAL MATCH (x) -[r:OWNS|PASSED]-> (p)
RETURN ID(x) AS root_id, LABELS(x)[0]+' '+x.id AS root_str, 
    TYPE(r) AS rel, 
    ID(p) AS obj_id, LABELS(p)[0] AS obj_label, p.id AS obj_str
 """

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

    copy_batch_to_audit = """
MATCH (stk_user:UserProfile {username:'_Stk_'})
MATCH (target:Root {id:$batch, user:$user, state:$state_candidate})
MATCH (original_user:UserProfile{username:$user}) -[original_access:HAS_ACCESS]-> (target)
MATCH (original_user) -[original_has_loaded:HAS_LOADED]-> (target)
DELETE original_has_loaded
DELETE original_access
MERGE (stk_user) -[:HAS_ACCESS]-> (target)
    SET target.auditor = $oper
    SET target.timestamp = timestamp()
    SET target.state = $state_auditing
CREATE (new_root:Root {id:$batch})
    SET new_root.user = $user
    SET new_root.file = target.file
    SET new_root.material = target.material
    SET new_root.state = $state_for_audit
MERGE (new_root) -[:AFTER_AUDIT]-> (target)        
MERGE (original_user) -[:HAS_LOADED]-> (new_root)
MERGE (original_user) -[:HAS_ACCESS]-> (new_root)
return *        
"""
