'''
Created on 27.1.2020

@author: JMä
'''

class Cypher_audit():
    ' Cypher clauses for auditor'

# Find some OWNS relations for given $batch and replace them with Audition STK relations
#Todo: Remove limit?
    copy_batch_to_audition = '''
MERGE (root:Audition {id:$batch, user:$user, auditor:$oper})
    SET root.timestamp = timestamp()
WITH root
    MATCH (b:Batch {id:$batch}) -[o:OWNS|OWNS_OTHER]-> (x)
    WITH root, o, b, x LIMIT 3000
        DELETE o
        CREATE (root) -[:PASSED]-> (x)
        RETURN x'''
   
#     remove_my_nodes = """
# MATCH (u:UserProfile) -[*]-> (a) WHERE u.username=$user
# DETACH DELETE a"""



class Cypher_batch_stats():
    
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


class Cypher_stats():
    ' Query Audition materials '

# ╒══════╤════════════════╤════════════╤═════╕
# │"user"│"id"            │"label"     │"cnt"│
# ╞══════╪════════════════╪════════════╪═════╡
# │"jpek"│"2020-01-03.001"│"Note"      │17   │
# ├──────┼────────────────┼────────────┼─────┤
# │"jpek"│"2020-01-03.001"│"Place"     │30   │
# ├──────┼────────────────┼────────────┼─────┤
# │"jpek"│"2020-01-03.002"│"Media"     │1    │
# ├──────┼────────────────┼────────────┼─────┤
# │"jpek"│"2020-01-03.002"│"Note"      │7    │
# ├──────┼────────────────┼────────────┼─────┤
# │"juha"│"2020-01-02.001"│"Citation"  │11   │
# ├──────┼────────────────┼────────────┼─────┤
# │"juha"│"2020-01-02.001"│"Event"     │1    │
# └──────┴────────────────┴────────────┴─────┘
    get_my_auditions = '''
match (b:Audition {auditor: $oper})
optional match (b) -[:PASSED]-> (x)
return b.user as user, b.id as id, labels(x)[0] as label, count(x) as cnt 
    order by user, id, label'''

# ╒════════════╤═════╕
# │"label"     │"cnt"│
# ╞════════════╪═════╡
# │"Family"    │12   │
# ├────────────┼─────┤
# │"Media"     │1    │
# ├────────────┼─────┤
# │"Person"    │25   │
# └────────────┴─────┘
    get_single_audition = '''
match (b:Audition {id:$batch}) 
optional match (b) -[:PASSED]-> (x)
return labels(x)[0] as label, count(x) as cnt'''

# ╒════════════════╤═════════════╤══════════╤════════╤═════════╕
# │"audition"      │"timestamp"  │"auditor" │"status"│"persons"│
# ╞════════════════╪═════════════╪══════════╪════════╪═════════╡
# │"2020-01-02.001"│1579789440355│"juha"    │null    │2146     │
# ├────────────────┼─────────────┼──────────┼────────┼─────────┤
# │"2020-01-23.001"│1579794614154│"juha"    │null    │25       │
# └────────────────┴─────────────┴──────────┴────────┴─────────┘
    get_my_audition_names = '''
match (b:Audition) where b.auditor = $oper
optional match (b) -[r:PASSED]-> (:Person)
return b.id as audition, b.timestamp as timestamp, 
    b.auditor as auditor, b.status as status,
    count(r) as persons 
order by audition'''
