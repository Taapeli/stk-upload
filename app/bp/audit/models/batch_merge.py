#   Isotammi Genealogical Service for combining multiple researchers' results.
#   Created in co-operation with the Genealogical Society of Finland.
#
#   Copyright (C) 2016-2021  Juha Mäkeläinen, Jorma Haapasalo, Kari Kujansuu, 
#                            Timo Nallikari, Pekka Valta
#
#   This program is free software: you can redistribute it and/or modify
#   it under the terms of the GNU General Public License as published by
#   the Free Software Foundation, either version 2 of the License, or
#   (at your option) any later version.
#
#   This program is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU General Public License for more details.
#
#   You should have received a copy of the GNU General Public License
#   along with this program.  If not, see <http://www.gnu.org/licenses/>.

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
        #new_relationships = -1
        #nodes_created = 0
        #moved_nodes = 0
        label_sets = [  # Grouped for decent size chunks in logical order
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
                    #with session.begin_transaction() as tx:
                    tx = session.begin_transaction()
                    count = 0 
                    result = tx.run(Cypher_audit.copy_batch_to_audit, 
                                    user=user, batch=batch_id, oper=auditor,
                                    labels=labels)
                    for record in result:
                        count = record['count']
                    #count = result.single().value(0)
                    print(f'Batch_merge.move_whole_batch {labels} {count}')
                    if count:
                        relationships_created += count
                    logger.debug(f"Batch_merge.move_whole_batch: moved {count} nodes of type {labels}")
                    tx.commit()

        except Exception as e:
            msg = f'Only {relationships_created} objects moved: {e.__class__.__name__} {e}'
            print(f'Batch_merge.move_whole_batch: {msg}')
            flash(msg, "flash_error")
            logger.error(f'{msg} {e.__class__.__name__} {e}')
            return msg

        msg = _("moved %(new_rel)s objects to ", new_rel=relationships_created)
        msg += _("Common data set")

        logger.info(f"Batch_merge.move_whole_batch: n={relationships_created}")
        flash(_("Transfer succeeded: ") + msg)
        return msg
