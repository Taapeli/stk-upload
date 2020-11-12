'''
Cypher clauses for models.gramps module

Created on 7.11.2020

@author: jm
'''

class CypherBatch():
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

    get_empty_batches = '''
MATCH (a:Batch) 
WHERE NOT ((a)-[:OWNS]->()) AND NOT a.id CONTAINS "2019-10"
RETURN a AS batch ORDER BY a.id DESC'''

    # Batch removal
    delete = """
MATCH (u:UserProfile{username:$username}) -[:HAS_LOADED]-> (b:Batch{id:$batch_id}) 
OPTIONAL MATCH (b) -[*]-> (n) 
DETACH DELETE b, n"""


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

