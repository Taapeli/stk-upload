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
    with        (s:Audit {id:...}) -[:PASSED]-> (x)
                with same id
    
    The Audit node should include
    - id = b.id    User Batch id
    - user         käyttäjä
    - auditor      the user who executed the transfer
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
        Move all Batch elements which are supplemented by given user to Audit.

        batch_id    active Batch
        user        owner of the Batch
        auditor    active auditor user id

        '''
        relationships_created = 0
        nodes_created = 0
        new_relationships = -1
        moved_nodes = 0
        label_sets = [  # Grouped to not too big chunks in logical order
                ["Note"],
                ["Repository", "Media"],
                ["Place", "Place_name"],
                ["Source", "Citation"],
                ["Event"],
                ["Person", "Name"],
                ["Family"]
            ]

        try:
            with shareds.driver.session() as session:
                for labels in label_sets:
                    tx = session.begin_transaction()
                    # while new_relationships != 0: ?
                    result = tx.run(Cypher_audit.copy_batch_to_audit, 
                                    user=user, batch=batch_id, oper=auditor,
                                    labels=labels)
                    counters = result.summary().counters
                    #print(counters)
                    new_relationships = counters.relationships_created
                    relationships_created += new_relationships
                    nodes_created += counters.nodes_created
                    record = result.single()
                    # <Record x=<Node id=318538 labels={'Place'} 
                    #    properties={'id': 'P0294', 'type': 'Farm', 
                    #        'uuid': '2d93295ef606433a8e339967e50bf6b0', 'pname': 'Sottungsby', 
                    #        'change': 1495632125}>>
                    cnt = record[0]
                    moved_nodes += cnt
                    logger.debug(f"Batch_merge.move_whole_batch: moved {cnt} nodes of type {labels}")
                    tx.commit()

        except Exception as e:
            msg = _("No objects transferred: ") + str(e)
            flash(msg, "flash_error")
            logger.error(msg++e.message)
            return msg

        msg = _("moved %(new_rel)s objects to ", new_rel=relationships_created)
        if nodes_created: msg += _("a new Common data set")
        else:             msg += _("Common data set")

        logger.info(f"Batch_merge.move_whole_batch: n={moved_nodes}")
        flash(_("Transfer succeeded: ") + msg)
        return msg
