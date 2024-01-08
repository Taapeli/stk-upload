'''
Created on 21.5.2021

@author: jm
'''
from ..util import label_by_iid

class CypherNote():
    """ A Note is added to given batch and optionally parent node 
    """

    # Find given Root node and connect Note in that Batch
    create_in_batch = """
MATCH (u:Root {id:$bid})
CREATE (u) -[:OBJ_OTHER]-> (n:Note) 
    SET n = $n_attr
    SET n.change = timestamp()"""


    @staticmethod
    def create_in_batch_as_leaf(src_iid: str) -> str:
        """ A Note is added to given batch and parent node.
        
            Clause for finding a given parent node with iid and 
            connect a new Note to it.

            Example:
                query = CypherNote.link_in_batch_as_leaf(iid)
                tx.run(query, bid=batch_id, parent_id=iid, n_attr=attr)
        """
        src_label = label_by_iid(src_iid)
        query = f"""
MATCH (u:Root {{id:$bid}})
MATCH (a:{src_label} {{iid:$parent_id}})
    CREATE (u) -[:OBJ_OTHER]-> (n:Note) 
    CREATE (a) -[:NOTE]-> (n)
    SET n = $n_attr
    SET n.change = timestamp()"""
        #print("#! link_in_batch_as_leaf:"+query.replace("\n","  "))
        return query

