#   Isotammi Geneological Service for combining multiple researchers' results.
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

