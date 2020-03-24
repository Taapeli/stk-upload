'''
Database write clauses using Gramps handle.

    In the link_* methods, the referred targets must be created before linking them.

Created on 23.3.2020

@author: jm
'''

class CypherObjectWHandle():

    link_media = """
MATCH (e) WHERE ID(e) = $root_id
MATCH (m:Media  {handle: $handle})
  CREATE (e) -[r:MEDIA]-> (m)
    SET r = $r_attr
RETURN ID(m) AS uniq_id"""

    link_note = """
MATCH (e) WHERE ID(e) = $root_id
MATCH (m:Note  {handle: $handle})
  CREATE (e) -[r:NOTE]-> (m)"""

    link_citation = """
MATCH (e) WHERE ID(e) = $root_id
MATCH (m:Citation  {handle: $handle})
  CREATE (e) -[r:CITATION]-> (m)"""

