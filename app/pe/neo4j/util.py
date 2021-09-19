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
from pprint import pprint

cypher_prefix = """
    MATCH (prof:UserProfile{username:$username}) -[:HAS_ACCESS]-> (root:Root)
    WITH root
""" 

cypher_common_prefix = """
    MATCH (root:Root {state:"Accepted"})
    WITH root
""" 

cypher_batch_prefix = """
    MATCH (prof:UserProfile{username:$username}) -[:HAS_ACCESS]-> (root:Root{id:$batch_id})
    WITH root
""" 

def run_cypher( session, cypher, username, **kwargs):
    """
    Runs the given Cypher query so that only the appropriate/allowed objects are returned:
    1) if username is not None or empty, then return objects from all candidate materials that the
       user has access to
    2) if username is None or empty, the return objects only from the common material
    
    The cypher query should access all other nodes through the node (root). For example
        cypher = "match (root) -[:OBJ_PERSON]-> (p:Person) ..."

    """
    if username:
        cypher2 = cypher_prefix + cypher
    else:
        cypher2 = cypher_common_prefix + cypher
    return session.run(cypher2, 
               username=username,  
               **kwargs)

def run_cypher2( session, cypher, username, batch_id, **kwargs):
    """
    Runs the given Cypher query so that only the appropriate/allowed objects are returned:
    1) if username is not None or empty, then return objects from all candidate materials that the
       user has access to
    2) if username is None or empty, the return objects only from the common material
    
    The cypher query should access all other nodes through the node (root). For example
        cypher = "match (root) -[:OBJ_PERSON]-> (p:Person) ..."
    
    """
    if not username:
        username = '_Stk_'
        cypher2 = cypher_common_prefix + cypher
    else:
        cypher2 = cypher_batch_prefix + cypher
    if False:
        print("----------- run_cypher2 -------------")
        print(cypher2)
        pprint(locals())
    return session.run(cypher2, 
               username=username,  
               batch_id=batch_id,
               **kwargs)
