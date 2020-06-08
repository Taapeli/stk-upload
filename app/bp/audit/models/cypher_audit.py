'''
Created on 27.1.2020

@author: JMä
'''

class Cypher_audit():
    """
        Cypher clauses for auditor.
    """

    copy_batch_to_audit = '''
MATCH (u:UserProfile {username:'_Stk_'})
MERGE (u) -[:HAS_ACCESS]-> (audit:Audit {id:$batch, user:$user, auditor:$oper})
    SET audit.timestamp = timestamp()
WITH audit
    MATCH (b:Batch {id:$batch})
    MERGE (b) -[:AFTER_AUDIT]-> (audit)
    WITH audit
        MATCH (b:Batch {id:$batch}) -[o:OWNS|OWNS_OTHER]-> (x)
            WHERE labels(x)[0] in $labels
        WITH audit, o, b, x //LIMIT $limit
            DELETE o
            CREATE (audit) -[:PASSED]-> (x)
            RETURN count(x)'''
