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
MATCH (stk_user:UserProfile {username:'_Stk_'})
MATCH (target:Root {id:$batch, user:$user, state:$state_candidate})
MATCH (original_user:UserProfile{username:$user}) -[original_access:HAS_ACCESS]-> (target)
DELETE original_access
MERGE (stk_user) -[:HAS_ACCESS]-> (target)
    SET target.auditor = $oper
    SET target.timestamp = timestamp()
    SET target.state = $state_auditing
CREATE (new_root:Root {id:$batch})
    SET new_root.user = $user
    SET new_root.file = target.file
    SET new_root.material = target.material
    SET new_root.state = $state_for_audit
MERGE (new_root) -[:AFTER_AUDIT]-> (target)        
MERGE (original_user) -[:HAS_ACCESS]-> (new_root)
return *        
"""
