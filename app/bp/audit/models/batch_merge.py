'''
Created on 5.12.2019

@author: jm
'''
import shareds
from flask_babelex import _
from flask import flash

import logging
logger = logging.getLogger('stkserver')


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
    WITH root, o, b, x LIMIT 100
        DELETE o
        CREATE (root) -[:PASSED]-> (x)
        RETURN x'''

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
        relationships_created = 0
        nodes_created = 0
        new_relationships = -1
        moved_nodes = {}
        text = ""

        with shareds.driver.session() as session:
            try:
                tx = session.begin_transaction()
                # while new_relationships != 0:
                result = tx.run(self.cypher_cp_batch_to_root, 
                                user=user, batch=batch_id, oper=operator)
                counters = result.summary().counters
                print(counters)
                new_relationships = counters.relationships_created
                relationships_created += new_relationships
                nodes_created += counters.nodes_created
                for record in result:
                    # <Record x=<Node id=318538 labels={'Place'} 
                    #    properties={'id': 'P0294', 'type': 'Farm', 
                    #        'uuid': '2d93295ef606433a8e339967e50bf6b0', 'pname': 'Sottungsby', 
                    #        'change': 1495632125}>>
                    node = record[0]
                    label = list(node.labels)[0]
                    text += ' ' + node['id']
                    if label in moved_nodes:
                        moved_nodes[label] += 1
                    else:
                        moved_nodes[label] = 1

                logger.info(f"-moved {text}")
                tx.commit()

            except Exception as e:
                msg = _("No objects transferred: ") + str(e)
                flash(msg, "flash_error")
                logger.error(msg)
                return msg

        msg = _("moved %(new_rel)s objects to ", new_rel=relationships_created)
        if nodes_created: msg += _("a new Common data set")
        else:             msg += _("Common data set")

        flash(_("Transfer succeeded: ") + msg)
        return msg
