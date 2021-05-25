'''
Created on 21.5.2021

@author: jm
'''

class CypherNote():
    """ A Note is added to given batch or parent node 
    
        # MATCH (u:Batch {id:$bid}) -[*]-> (a {handle:$parent_handle})
    """

    # Find the batch like '2019-02-24.006' and connect Note in that Batch
    create_in_batch = """
MATCH (u:Batch {id:$bid})
CREATE (u) -[:OWNS]-> (n:Note) 
    SET n = $n_attr
RETURN ID(n)"""

    # Find a known parent node with uniq_id and connect a new Note to it
    create_in_batch_as_leaf = """
MATCH (a) WHERE ID(a) = $parent_id
CREATE (a) -[:NOTE]-> (n:Note) 
    SET n = $n_attr
RETURN ID(n)"""

