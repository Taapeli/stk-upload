'''
Cypher clauses for models.gramps module

Created on 7.11.2020

@author: jm
'''

class CypherBatch():
    '''
    Cypher clauses for managing Batch nodes
    '''

    aquire_lock = """MERGE (lock:Lock {id:$lock_id})
SET lock.locked = true"""

    batch_find_id = """
MATCH (b:Batch) WHERE b.id STARTS WITH $batch_base
RETURN b.id AS bid
    ORDER BY bid DESC LIMIT 1"""

    batch_create = """
MATCH (u:UserProfile {username: $b_attr.user})
MERGE (u) -[:HAS_LOADED]-> (b:Batch {id: $b_attr.id})
MERGE (u) -[:HAS_ACCESS]-> (b)
    SET b = $b_attr
    SET b.timestamp = timestamp()
RETURN ID(b) AS id"""

    batch_complete = """
MATCH (u:UserProfile {username: $user})
MATCH (u) -[:HAS_LOADED]-> (b:Batch {id: $bid})
    SET b.status=$status
RETURN ID(b) AS id"""

    get_filename = """
MATCH (b:Batch {id: $batch_id, user: $username}) 
RETURN b.file"""

    list_all = """
MATCH (b:Batch) 
RETURN b """

    get_batches = '''
match (b:Batch) 
    where b.user = $user and b.status = "completed"
optional match (b) -[:OWNS]-> (x)
return b as batch,
    labels(x)[0] as label, count(x) as cnt 
    order by batch.user, batch.id'''

    get_passed = '''
match (b:Audit) 
    where b.user = $user
optional match (b) -[:PASSED]-> (x)
return b as batch, count(x) as cnt 
    order by batch.id'''

    get_single_batch = '''
match (up:UserProfile) -[r:HAS_LOADED]-> (b:Batch {id:$batch}) 
optional match (b) -[:OWNS]-> (x)
return up as profile, b as batch, labels(x)[0] as label, count(x) as cnt'''

    get_user_batch_names = '''
match (b:Batch) where b.user = $user
optional match (b) -[r:OWNS]-> (:Person)
return b.id as batch, b.timestamp as timestamp, b.status as status,
    count(r) as persons 
    order by batch'''

    TODO_get_empty_batches = '''
MATCH (a:Batch) 
WHERE NOT ((a)-[:OWNS]->()) AND NOT a.id CONTAINS "2019-10"
RETURN a AS batch ORDER BY a.id DESC'''

    # Batch removal
    delete = """
MATCH (u:UserProfile{username:$username}) -[:HAS_LOADED]-> (b:Batch{id:$batch_id}) 
OPTIONAL MATCH (b) -[*]-> (n) 
DETACH DELETE b, n"""

    remove_all_handles = """
match (b:Batch {id:$batch_id}) -[*]-> (a)
    remove a.handle
return count(a),labels(a)[0]"""

    add_missing_links = """
match (n) where exists (n.handle)
match (b:Batch{id:$batch_id})
    merge (b)-[:OWNS_OTHER]->(n)
    remove n.handle
return count(n)"""

    find_unlinked_nodes = """
match (n) where exists (n.handle)
return  count(n), labels(n)[0]"""



class CypherAudit():
    ''' 
    Query Audit materials
    '''

    get_my_audits = '''
match (b:Audit {auditor: $oper})
optional match (b) -[:PASSED]-> (x)
return b, labels(x)[0] as label, count(x) as cnt 
    order by b.user, b.id, label'''

    get_all_audits = '''
match (b:Audit)
optional match (b) -[:PASSED]-> (x)
return b, labels(x)[0] as label, count(x) as cnt 
    order by b.user, b.id, label'''

    merge_check = """
MATCH (p) WHERE id(p) IN $id_list
OPTIONAL MATCH (x) -[r:OWNS|PASSED]-> (p)
RETURN ID(x) AS root_id, LABELS(x)[0]+' '+x.id AS root_str, 
    TYPE(r) AS rel, 
    ID(p) AS obj_id, LABELS(p)[0] AS obj_label, p.id AS obj_str
 """

