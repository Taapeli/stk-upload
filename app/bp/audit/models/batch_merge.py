'''
Created on 5.12.2019

@author: jm
'''
import shareds
from .cypher_audit import Cypher_audit

from flask_babelex import _
from flask import flash

import logging
logger = logging.getLogger('stkserver')


class Batch_merge(object):
    '''
    Methods to move User Batch items to Common Data.
    
    Replace the (b:Batch {id:...}) -[o:OWNS]-> (x)
                relations with given Batch id
    with        (s:Audition {id:...}) -[:PASSED]-> (x)
                with same id
    
    The Audition node should include
    - id = b.id    User Batch id
    - user         käyttäjä
    - admin        the user who executed the transfer
    - timestamp    viimeisin muutosaika
    - 
    #Todo: Make decisions, which items should be moved, merged or left alone
    '''

    def __init__(self):
        '''
        Constructor
        '''
        pass

    def move_whole_batch(self, batch_id, user, auditor):
        '''
        Move all Batch elements which are supplemented by given user to Audition.

        batch_id    active Batch
        user        owner of the Batch
        auditor    active auditor user id

        '''
        relationships_created = 0
        nodes_created = 0
        new_relationships = -1
        moved_nodes = {}
        text = ""

        with shareds.driver.session() as session:
            try:
                tx = session.begin_transaction()
                # while new_relationships != 0: ?
                result = tx.run(Cypher_audit.copy_batch_to_audition, 
                                user=user, batch=batch_id, oper=auditor)
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
                    text += ' ' + node.get('id','-')
                    if label in moved_nodes:
                        moved_nodes[label] += 1
                    else:
                        moved_nodes[label] = 1

                logger.info(f"-moved {text[:500]} ...")
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
