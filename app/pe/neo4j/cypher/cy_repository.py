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
    SET a = $r_attr"""
#!RETURN ID(a) as iid"""

    r_link_notes = """
MATCH (n:Note {handle: $hlinks})
WITH n
  MATCH (r:Repository {handle: $handle})
  CREATE (r) -[:NOTE]-> (n)
RETURN COUNT(DISTINCT n) AS cnt"""

    get_repositories = """
MATCH (root) -[:OBJ_OTHER]-> (rep:Repository)
    OPTIONAL MATCH (rep) -[:NOTE]-> (note)
    OPTIONAL MATCH (rep) <-[r:REPOSITORY]- (s:Source)
RETURN root, rep as repository, collect(DISTINCT note) as notes, 
       collect(DISTINCT r.medium) as mediums,
       //collect(DISTINCT s) as sources,
       COUNT(s) AS source_cnt 
ORDER BY toUpper(rep.rname)"""

    get_repository_sources_iid = """
MATCH (root:Root) -[:OBJ_SOURCE]-> (s:Source) -[r:REPOSITORY]-> (repo:Repository) 
    WHERE repo.iid = $iid
OPTIONAL MATCH (c:Citation) -[cr:SOURCE]-> (s)
OPTIONAL MATCH (repo) -[:NOTE]-> (n)
WITH root, repo, r, s, n, COUNT(cr) AS citas 
    ORDER BY repo.rname, s.stitle
RETURN root, repo,
    COLLECT(DISTINCT [s, r.medium, citas]) AS sources,
    COLLECT(DISTINCT (n)) AS notes"""