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
'''
Created on 25.5.2021

@author: jm
'''

class CypherCitation():
    """ For creating Citation object from Gramps data. """

    # Create Citation node and link (Batch) --> (Citation)
    create_to_batch = """
MATCH (b:Root {id: $batch_id})
MERGE (b) -[r:OBJ_OTHER]-> (c:Citation {handle: $c_attr.handle}) 
    SET c = $c_attr"""
#! RETURN ID(c) as uniq_id"""

#! For each Note, Citation --> USE CypherObjectWHandle.link_item("Citation", "Note")
#
#!    link_source = """
# MATCH (n:Citation {handle: $handle})
# MATCH (m:Source   {handle: $hlink})
# MERGE (n) -[r:SOURCE]-> (m)"""
#     # Create Note node and link (Citation) --> (Note)
#     c_link_note = """
# MATCH (n:Citation {handle: $handle})
# MATCH (m:Note     {handle: $hlink})
# CREATE (n) -[r:NOTE]-> (m)"""


