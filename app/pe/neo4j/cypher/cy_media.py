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
Created on 16.1.2021

@author: jm
'''

class CypherMedia():


# Read Media data

    get_media_by_uuid = """
MATCH (root) -[:OBJ_OTHER]-> (media:Media {uuid:$uuid}) <-[r:MEDIA]- (ref)
OPTIONAL MATCH (ref) <-[:EVENT]- (ref2)
RETURN media, PROPERTIES(r) AS prop, ref, ref2"""

    get_all = "MATCH (o:Media) RETURN o"

    # Media list by description with count limit
    get_media_list = """
MATCH (root) -[:OBJ_OTHER]-> (o:Media) <- [r:MEDIA] - ()
WHERE o.description >= $start_name
RETURN o, case root.original_user when null then root.user else root.original_user end as credit, root.id as batch_id, COUNT(r) AS count
    ORDER BY o.description LIMIT $limit"""


# Write Media data

    # Find a batch like '2019-02-24.006' and connect new Media object to that Batch
    create_in_batch = """
MATCH (u:Batch {id:$bid})
MERGE (u) -[:OWNS]-> (a:Media {uuid:$uuid})
    SET a += $m_attr
RETURN ID(a) as uniq_id"""

