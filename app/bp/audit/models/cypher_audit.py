'''
Created on 27.1.2020

@author: JMä
'''

class Cypher_audit():
    ' Cypher clauses for auditor'

    copy_batch_to_audit = '''
MATCH (u:UserProfile {username:'master'})
MERGE (u) -[:HAS_LOADED]-> (root:Audit {id:$batch, user:$user, auditor:$oper})
    SET root.timestamp = timestamp()
WITH root
    MATCH (b:Batch {id:$batch}) -[o:OWNS|OWNS_OTHER]-> (x)
    where labels(x)[0] in $labels
    WITH root, o, b, x //LIMIT $limit
        DELETE o
        CREATE (root) -[:PASSED]-> (x)
        RETURN count(x)'''
