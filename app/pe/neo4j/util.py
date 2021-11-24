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

# blacked 15.11.2021/JMä
from pprint import pprint
import base32_lib as base32

cypher_prefix = """
    MATCH (prof:UserProfile{username:$username}) 
        -[:HAS_ACCESS|:DOES_AUDIT]-> (root:Root)
    WITH root
"""

cypher_common_prefix = """
    MATCH (root:Root {state:"Accepted"})
"""

cypher_batch_prefix = """
    MATCH (prof:UserProfile{username:$username})
        -[:HAS_ACCESS|:DOES_AUDIT]-> (root:Root{id:$batch_id})
"""

cypher_new_iid = """
MERGE (a:Isotammi_id {id:$id_type})
    ON CREATE SET a.counter = 1
    ON MATCH SET a.counter = a.counter + 1
RETURN a.counter AS n_Isotammi_id"""


def run_cypher(session, cypher, username, **kwargs):
    """
    Runs the given Cypher query returning only the appropriate/allowed objects.

    1) if username is not None or empty, then return objects from all 
       candidate materials that the user has access to
    2) if username is None or empty, the return objects only from the 
       Accepted material
    
    The cypher query should access all other nodes through the node (root). 
    For example

        cypher = "match (root) -[:OBJ_PERSON]-> (p:Person) ..."

    """
    if username:
        full_cypher = cypher_prefix + cypher
    else:
        full_cypher = cypher_common_prefix + cypher
    return session.run(full_cypher, username=username, **kwargs)


def run_cypher_batch(session, cypher, username, batch_id, **kwargs):
    """
    Runs the given Cypher query returning only the appropriate/allowed objects
    of given batch.

    1) if username is given, then return objects from all 
       candidate materials that the user has access to
    2) if username is None or empty, the return objects only from the 
       Accepted material
    
    The cypher query should access all other nodes through the node (root). 
    For example

        cypher = "match (root) -[:OBJ_PERSON]-> (p:Person) ..."

    """
    cypher_prefix = kwargs.get("cypher_prefix", "")
    if not username:
        full_cypher = cypher_prefix + cypher_common_prefix + cypher
    else:
        full_cypher = cypher_prefix + cypher_batch_prefix + cypher
    if False:
        print("----------- run_cypher_batch -------------")
        print(full_cypher)
        pprint(locals())
    return session.run(full_cypher, username=username, batch_id=batch_id, **kwargs)


def new_isotammi_id(session, obj_name: str):  # obj_type_letter):
    """ Creates new unique isotammi_id keys when creating objects. 
    """

    def iid_groupper(id_str):
        """Inserts a hyphen into the id string.

         Examples: H-1, H-1234, H1-2345, H1234-5678
        """
        return (
            id_str[: max(1, len(id_str) - 4)] + "-" + id_str[max(1, len(id_str) - 4) :]
        )

    if obj_name.startswith("Person"):
        id_type = "H"
    else:
        id_type = obj_name[:1]
    result = session.run(cypher_new_iid, id_type=id_type)
    n_iid = result.single()[0]
    isotammi_id = iid_groupper(id_type + base32.encode(n_iid, checksum=False))

    print(f"new_isotammi_id: {n_iid} -> {isotammi_id}")
    return isotammi_id
