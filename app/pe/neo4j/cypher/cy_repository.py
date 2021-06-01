'''
Created on 1.6.2021

@author: jm
'''

class CypherRepository:
    """ For Repository class """

    # Find the batch like '2019-02-24.006' and connect new Repository to that Batch
    create_in_batch = """
MATCH (u:Batch {id:$bid})
CREATE (u) -[:OWNS]-> (a:Repository) 
    SET a = $r_attr
RETURN ID(a) as uniq_id"""
