'''
Created on 27.1.2020

@author: JMä
'''

class Cypher_audit():
    ' Cypher clauses for auditor'

# Find some OWNS relations for given $batch and replace them with Root STK relations
#Todo: Remove limit?
    copy_batch_to_root = '''
MERGE (root:Audition {id:$batch, user:$user, operator:$oper})
    SET root.timestamp = timestamp()
WITH root
    MATCH (b:Batch {id:$batch}) -[o:OWNS|OWNS_OTHER]-> (x)
    WITH root, o, b, x LIMIT 3000
        DELETE o
        CREATE (root) -[:PASSED]-> (x)
        RETURN x'''

#     move_batch_todo = '''
# MATCH (up:UserProfile) -[r:HAS_LOADED]-> (b:Batch {id:"2019-11-18.002"}) 
# WITH up, r, b ORDER BY b.id DESC LIMIT 10
# RETURN up, r, b'''
    
#     remove_my_nodes = """
# MATCH (u:UserProfile) -[*]-> (a) WHERE u.username=$user
# DETACH DELETE a"""


class Cypher_stats():
    #TODO TODO TODO TODO TODO TODO TODO TODO TODO TODO TODO TODO 
    get_batches = '''
match (b:Batch) 
    where b.user = $user and b.status = "completed"
optional match (b) -[:OWNS]-> (x)
return b as batch,
    labels(x)[0] as label, count(x) as cnt 
    order by batch.user, batch.id'''

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
