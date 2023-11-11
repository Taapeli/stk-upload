'''
Created on 21.5.2021

@author: jm
'''

class CypherNote():
    """ A Note is added to given batch and optionally parent node 
    """

    # Find given Root node and connect Note in that Batch
    create_in_batch = """
MATCH (u:Root {id:$bid})
CREATE (u) -[:OBJ_OTHER]-> (n:Note) 
    SET n = $n_attr
    SET n.change = timestamp()
RETURN ID(n)"""

    # Find a known parent node with iid and connect a new Note to it
    create_in_batch_as_leaf = """
MATCH (a) WHERE a.iid = $parent_id
MATCH (u:Root {id:$bid})
    CREATE (u) -[:OBJ_OTHER]-> (n:Note) 
    CREATE (a) -[:NOTE]-> (n)
    SET n = $n_attr
    SET n.change = timestamp()
RETURN ID(n)"""

