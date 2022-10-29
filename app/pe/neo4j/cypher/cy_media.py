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

    get_media_by_iid = """
MATCH (root) -[:OBJ_OTHER]-> (media:Media {iid:$iid}) <-[r:MEDIA]- (ref)
OPTIONAL MATCH (ref) <-[:EVENT]- (eref)
RETURN root, media, PROPERTIES(r) AS prop, ref, eref"""

    get_all = "MATCH (o:Media) RETURN o"

    # Media list by description with count limit
    get_media_list = """
MATCH (root) -[:OBJ_OTHER]-> (o:Media) <- [:MEDIA] - (r)
    WHERE TOUPPER(o.description) >= $start_name
RETURN root, o, COUNT(DISTINCT r) AS count
    ORDER BY TOUPPER(o.description) LIMIT $limit"""


# Write Media data

    # Find a batch like '2019-02-24.006' and connect new Media object to that Batch
    create_in_batch = """
MATCH (u:Root {id:$bid})
MERGE (u) -[:OBJ_OTHER]-> (a:Media {iid:$iid})
    SET a += $m_attr
RETURN ID(a) as uniq_id"""

