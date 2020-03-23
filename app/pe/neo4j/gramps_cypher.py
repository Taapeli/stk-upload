'''
Database write clauses using Gramps handle

Created on 23.3.2020

@author: jm
'''

class CypherObjectWHandle():

    link_media = """
MATCH (e) WHERE ID(e) = $root_id
MATCH (m:Media  {handle: $m_handle})
  CREATE (e) -[r:MEDIA]-> (m)
    SET r = $r_attr"""

