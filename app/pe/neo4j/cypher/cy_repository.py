'''
Created on 1.6.2021

@author: jm
'''

class CypherRepository:
    """ For Repository class """

    # Find the batch like '2019-02-24.006' and connect new Repository to that Batch
    create_in_batch = """
MATCH (u:Root {id:$bid})
CREATE (u) -[:OBJ_OTHER]-> (a:Repository) 
    SET a = $r_attr
RETURN ID(a) as uniq_id"""

    get_repository_sources_iid = """
MATCH (root:Root) -[:OBJ_SOURCE]-> (s:Source) -[r:REPOSITORY]-> (repo:Repository) 
    WHERE repo.iid = $iid
WITH root, repo, r, s ORDER BY repo.rname, s.stitle //LIMIT 20
RETURN root, repo, 
    COLLECT(DISTINCT [s, r.medium]) AS sources"""