'''
Created on 5.12.2019

@author: jm
'''
import shareds
from flask_login.utils import current_user


class Batch_merge(object):
    '''
    Methods to move User Batch items to Common Data.
    
    Replace the (b:Batch {id:...}) -[o:OWNS]-> (x)
                relations with given Batch id
    with        (s:Root {id:...}) -[:PASSED]-> (x)
                with same id
    
    The Root node should include
    - id = b.id    User Batch id
    - user         käyttäjä
    - admin        the user who executed the transfer
    - timestamp    viimeisin muutosaika
    - 
    #Todo: Make decisions, which items should be moved, merged or left alone
    '''

# Find some OWNS relations for given $batch and replace them with Root STK relations
    cypher_cp_batch_to_root = '''
MERGE (root:Root {id:$batch, user:$user, operator:$oper})
    SET root.timestamp = timestamp()
WITH root
    MATCH (b:Batch {id:$batch}) -[o:OWNS|OWNS_OTHER]-> (x)
    WITH root, o, b, x LIMIT 5
        DELETE o
        CREATE (root) -[:PASSED]-> (x)'''

    def __init__(self):
        '''
        Constructor
        '''
        pass

    def move_whole_batch(self, batch_id, user, operator):
        '''
        Move all Batch elements which are supplemented by given user to Root.

        batch_id    active Batch
        user        owner of the Batch
        operator    active auditor user id

        '''
        counters = None
        with shareds.driver.session() as session:
            result = session.run(self.cypher_cp_batch_to_root, 
                                 user=user, batch=batch_id, oper=operator)
            counters = result.summary().counters
        print(counters)
        return counters
