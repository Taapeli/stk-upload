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
from bl.batch import BatchUpdater

"""
Created on 5.12.2019

@author: jm
"""
import shareds
from bl.base import Status
from .cypher_audit import Cypher_audit

from flask_babelex import _
from flask import flash

import logging

logger = logging.getLogger("stkserver")


class Batch_merge:
    """
    Methods to move User Batch items to Common data.

    Replace the (b:Batch {id:...}) -[o:OWNS]-> (x)
                relations with given Batch id
    with        (s:Audit {id:...}) -[:PASSED]-> (x)
                with same id
    end create  (b) -[:AFTER_AUDIT]-> (s).
    
    The b.status is updated.
    #Todo Set also Audit.status

    The Audit node has
    - id = b.id    User Batch id
    - user         käyttäjä
    - auditor      the user who executed the transfer
    - timestamp    viimeisin muutosaika
    """

    def move_whole_batch(self, batch_id, user, auditor):
        """
        Move all Batch elements which are supplemented by given user to Audit.

        :param:    batch_id    active Batch
        :param:    user        owner of the Batch
        :param:    auditor    active auditor user id

        """
        from bl.batch import Batch

        relationships_created = 0
        label_sets = [  # Grouped for decent size chunks in logical order
            ["Note"],
            ["Repository", "Media"],
            ["Place", "Place_name"],
            ["Source", "Citation"],
            ["Event"],
            ["Person", "Name"],
            ["Family"],
        ]

        try:
            with shareds.driver.session() as session:
                for labels in label_sets:
                    # with session.begin_transaction() as tx:
                    tx = session.begin_transaction()
                    count = 0
                    result = tx.run(
                        Cypher_audit.copy_batch_to_audit,
                        user=user,
                        batch=batch_id,
                        oper=auditor,
                        labels=labels,
                    )
                    for record in result:
                        count = record["count"]
                    # count = result.single().value(0)
                    print(f"Batch_merge.move_whole_batch {labels} {count}")
                    if count:
                        relationships_created += count
                    logger.debug(
                        f"Batch_merge.move_whole_batch: moved {count} nodes of type {labels}"
                    )
                    tx.commit()

            # Mark as complete candidate material
            with BatchUpdater('update') as service:
                res = service.batch_get_one(user, batch_id)
                # returns {"status":Status.OK, "item":batch}
                if Status.has_failed(res):
                    return res
                service.batch = res.get('item')
                res = service.batch_mark_status(Batch.BATCH_FOR_AUDIT)
                if Status.has_failed(res):
                    msg = res['statustext']
                    print(f"Batch_merge.move_whole_batch: {msg}")
                    flash(msg, "flash_error")
                    logger.error(msg)
                    return msg


        except Exception as e:
            msg = f"Only {relationships_created} objects moved: {e.__class__.__name__} {e}"
            print(f"Batch_merge.move_whole_batch: {msg}")
            flash(msg, "flash_error")
            logger.error(f"{msg} {e.__class__.__name__} {e}")
            return msg

        msg = _("moved %(new_rel)s objects to ", new_rel=relationships_created)
        msg += _("Common data set")

        logger.info(f"Batch_merge.move_whole_batch: n={relationships_created}")
        flash(_("Transfer succeeded: ") + msg)
        return msg
