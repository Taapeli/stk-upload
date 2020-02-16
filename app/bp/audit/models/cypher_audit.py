'''
Created on 27.1.2020

@author: JMä
'''

class Cypher_audit():
    ' Cypher clauses for auditor'

# #Todo: Remove limit?
    copy_batch_to_audition = '''
MERGE (root:Audit {id:$batch, user:$user, auditor:$oper})
    SET root.timestamp = timestamp()
WITH root
    MATCH (b:Batch {id:$batch}) -[o:OWNS|OWNS_OTHER]-> (x)
    WITH root, o, b, x LIMIT 3000
        DELETE o
        CREATE (root) -[:PASSED]-> (x)
        RETURN x'''
   