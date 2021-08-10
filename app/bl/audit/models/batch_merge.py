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

"""
Created on 5.12.2019

@author: jm
"""
import shareds
from bl.root import State
from pe.neo4j.cypher.cy_batch_audit import CypherAudit

import logging

logger = logging.getLogger("stkserver")


class Batch_merge:
    """
    Methods to move a User Batch (Root node) to Common data.
    """

    def move_whole_batch(self, batch_id, user, auditor):
        """
        :param:    batch_id    active Batch
        :param:    user        owner of the Batch
        :param:    auditor     active auditor user id

        """
        with shareds.driver.session() as session:
            result = session.run(
                CypherAudit.copy_batch_to_audit,
                user=user,
                batch=batch_id,
                oper=auditor,
                state_candidate=State.ROOT_CANDIDATE,
                state_auditing=State.ROOT_AUDITING,
                state_for_audit=State.ROOT_FOR_AUDIT
            ).single()
            logger.info(f"Batch_merge.move_whole_batch: {batch_id}")
            print(f"Batch_merge.move_whole_batch: {batch_id}")
            #print(f"Batch_merge.move_whole_batch: {batch_id}; result={result}")
            return result
