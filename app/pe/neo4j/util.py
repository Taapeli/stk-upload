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
import base32_lib as base32
from bl.base import IsotammiException
from bl.material import Material
import shareds
LOG_CYPHER = shareds.app.config.get("LOG_CYPHER", False) if shareds.app else False

cypher_user_prefix = """
    MATCH (prof:UserProfile{username:$username}) 
        -[:HAS_ACCESS|:DOES_AUDIT]-> (root:Root)
    WITH root
"""

cypher_material_prefix = """
    MATCH (root:Root {material:$material_type, state:$state})
"""

cypher_common_batch_prefix = """
    MATCH (root:Root{material:$material_type, id:$batch_id})
"""

cypher_user_batch_prefix = """
    MATCH (prof:UserProfile{username:$username})
        -[:HAS_ACCESS|:DOES_AUDIT]-> (root:Root{id:$batch_id})
"""

cypher_block_of_iids = """
MERGE (a:iid {id:$iid_mark})
    ON CREATE SET a.counter = $iid_count
    ON MATCH SET a.counter = a.counter + $iid_count
RETURN a.counter - $iid_count AS new_iid"""


def run_cypher(session, cypher:str, username:str, material:Material, **kwargs):
    """
    Runs the given Cypher query returning only the appropriate/allowed objects.

    1) if username is given, then return objects from all 
       different materials that the user has access to
    2) if username is None or empty, the return objects only from the 
       Accepted material of type kwargs["material_type"]
    
    The cypher query should access all other nodes through the node (root). 
    For example

        cypher = "match (root) -[:OBJ_PERSON]-> (p:Person) ..."

    """
    if username:
        # By username
        full_cypher = cypher_user_prefix + cypher
    else:
        # By material type
        full_cypher = cypher_material_prefix + cypher
        if not isinstance(material, Material):
            raise IsotammiException("pe.neo4j.util.run_cypher: invalid material")

    return session.run(full_cypher, username=username, 
                       material_type=material.m_type,
                       state=material.state,
                       **kwargs)


def run_cypher_batch(session, cypher, username, material, **kwargs):
    """
    Runs the given Cypher query returning only the appropriate/allowed objects
    of given batch.

    1) if username is given, then return objects from all 
       candidate materials that the user has access to
    2) if username is None or empty, the return objects only from the 
       Accepted material of material_type
    
    The cypher query should access all other nodes through the node (root). 
    For example

        cypher = "match (root) -[:OBJ_PERSON]-> (p:Person) ..."

    """
    cypher_prefix = kwargs.get("cypher_prefix", "")
    if not username:
        if material.batch_id:
            # Single common material
            full_cypher = cypher_prefix + cypher_common_batch_prefix + cypher
        else:
            # Materials by material_type
            full_cypher = cypher_prefix + cypher_material_prefix + cypher
    else:
        # By username and batch_id
        full_cypher = cypher_prefix + cypher_user_batch_prefix + cypher
    if not isinstance(material, Material):
        raise IsotammiException("pe.neo4j.util.run_cypher_batch: invalid material")

    if LOG_CYPHER:
        print("----------- pe.neo4j.util.run_cypher_batch -------------")
        print("// 1. You may copy this to cypher console to set parameters:")
        if username:
            print(f":param username => {username!r};")
        print(f":param batch_id => {material.batch_id!r};")
        print(f":param material_type => {material.m_type!r};")
        print(f":param state => {material.state!r};")
        for key, value in kwargs.items():
            print (f":param   {key} => {value!r};")
        print("// 2. Copy to cypher console to run command:")
        print(full_cypher)
        print("-----------")
    return session.run(full_cypher,
                       username=username, 
                       batch_id=material.batch_id, 
                       material_type=material.m_type,
                       state=material.state,
                       **kwargs)

def dict_root_node(root_node, select="min"):
    """ Create minimal root_dict from record["root"]

        Used in macro.all_obj_ids
    """

    dic = {'material': root_node["material"], 
            'root_state': root_node["state"], 
            'root_user': root_node["user"], 
            'batch_id': root_node["id"]}
    if select == "more":
        dic["description"] = root_node["description"]
        dic["timestamp"] = root_node["timestamp"]
        dic["xmlname"] = root_node["xmlname"]
        #ic["state"] = root_node["state"]
        dic["file"] = root_node["file"]
    return dic


def relation_type_by_label(label: str) -> str:
    """ Find relation type by Node label.
    """
    types = {"Citation":"CITATION", 
        "Event":"EVENT", 
        "Media":"MEDIA", 
        "Name":"NAME", 
        "Note":"NOTE", 
        # "Person": "CHILD",
        # "Person": "PARENT",
        # "Place": "IS_INSIDE",
        "Place":"PLACE", 
        "Place_name":"NAME", 
        # "Place_name": "NAME_LANG",
        "Repository":"REPOSITORY", 
        "Source":"SOURCE"}
    link_type = types.get(label)
    if link_type is None:
        #print (f"// No matching relation type for {label}")
        raise (IsotammiException, f"No matching relation type for {label}")

    return link_type

def label_by_iid(iid: str) -> str:
    """ Find Node label by IsotammiId.
    """
    labels = {
        "C": "Citation", 
        "E": "Event", 
        "M": "Media", 
        "AN":"Name", 
        "N": "Note", 
        "H": "Person",
        "P": "Place", 
        "AP":"Place_name", 
        "R": "Repository", 
        "S": "Source"}
    if iid:
        a = iid[0]
        if a == "A":
            a = iid[0:1]    #  "AP" (Place) or "AI" (Person)
    else:
        a ="*"
    label = labels.get(a)
    if label is None:
        #print (f"// No matching relation type for {dst_label}")
        raise IsotammiException("No matching label for " + iid)

    return label


class IidGenerator:
    """
    Generating a sequences of unique IsotammiId keys by object type from the database.
    
    @see: https://stackoverflow.com/questions/42983569/how-to-write-a-generator-class

    Usage:
    - a = IidGenerator(tx, "People") Create an ID generator using given transaction
    - a.reserve(100)                 Allocates given number of keys
    - key = a.get_one()              Get next key
    """
    def __init__(self, session, obj_name: str):
        """
        Create an object with a reservation of 'id_count' ID values from the
        database counter for the type of 'obj_name'.
        
        Isotammi_id or iid consist of object type mark (1-2 letters) and
        running index grouped by hyphens.
        
        The keys are reserved in greater bunches not to lock database
        every time a new key is needed.
        
        @See: pe.neo4j.util.label_by_iid, bl.base.NodeObject.label
        """
        self.iid_mark = "H" if obj_name.startswith("Pe") else obj_name[:1]
        self.session = session
        self.n_iid = 0
        self.max_iid = 0

    def reserve(self, iid_count: int):
        """
        Create or update an object with a reservation of 'id_count' ID values
        from the database counter for the type of 'obj_name'.
        """
        result = self.session.run(cypher_block_of_iids, 
                                  iid_mark=self.iid_mark, 
                                  iid_count = iid_count)
        self.n_iid = result.single()[0]
        self.max_iid = self.n_iid + iid_count - 1

    def get_one(self) -> str:
        """
        Yield the next Isotammi ID properly formatted.
        """

        if self.n_iid > self.max_iid:
            raise IsotammiException("Whole chunk of allocated Isotammi IDs already used."
                                    f" {self.n_iid} > {self.max_iid}")

        iid = self._format_iid(self.iid_mark, self.n_iid)
        self.n_iid += 1

##        print(f"new_isotammi_id: {self.n_iid} -> {iid}")
        return iid

    def _format_iid(self, mark:str, n_val: str) -> str:
        """
        Inserts a hyphen into the id string.
        Examples: H-1, H-1234, H1-2345, H1234-5678
        """
        val = base32.encode(n_val, checksum=False)
        l_val = len(val)
        if l_val == 0:
            #print(f"0) {mark}-{val}")
            return "FAIL"
        x = ""
        while len(val) > 4:
            x = x + "-" + val[-4:]
            val = val[:-4]
            #print(f"2) {mark}{val}{x} | {val=},{x=}")
        #print(f"1) {mark}-{val}{x}")
        if l_val <= 4:
            return mark + "-" + val
        return mark + val + x


if __name__ == "__main__":
    print("Testing Iid value formatting")
    my = IidGenerator(0, "Person")
    for n in range(10):
        val = 40**n
        print(f'\t{val!r} = tulos {my._format_iid("H", val)!r}')
    print("done")

