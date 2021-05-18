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
Created on 27.1.2020

@author: JMä
"""


class Cypher_audit:
    """
    Cypher clauses for auditor.
    """

    copy_batch_to_audit = """
MATCH (u:UserProfile {username:'_Stk_'})
MERGE (u) -[:HAS_ACCESS]-> (audit:Audit {id:$batch, user:$user, auditor:$oper})
    SET audit.timestamp = timestamp()
WITH audit
    MATCH (batch:Batch {id:$batch})
    MERGE (batch) -[:AFTER_AUDIT]-> (audit)
    WITH batch, audit
        MATCH (batch) -[owns:OWNS]-> (x)
            WHERE labels(x)[0] in $labels
        WITH batch, audit, owns, x //LIMIT 2
            DELETE owns
            CREATE (audit) -[:PASSED]-> (x)
            RETURN count(x) AS count //audit,x
"""


# MATCH (u:UserProfile {username:'_Stk_'})
# MERGE (u) -[:HAS_ACCESS]-> (audit:Audit {id:$batch, user:$user, auditor:$oper})
#     SET audit.timestamp = timestamp()
# WITH audit
#     MATCH (b:Batch {id:$batch})
#     MERGE (b) -[:AFTER_AUDIT]-> (audit)
#     WITH audit
#         MATCH (b:Batch {id:$batch}) -[o:OWNS|OWNS_OTHER]-> (x)
#             WHERE labels(x)[0] in $labels
#         WITH audit, o, b, x //LIMIT $limit
#             DELETE o
#             CREATE (audit) -[:PASSED]-> (x)
#             RETURN count(x)'''
