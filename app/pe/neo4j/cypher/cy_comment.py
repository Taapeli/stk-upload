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
Created on 19.5.2021

@author: jormah
'''

class CypherComment():


# Read Comment data

    # Comment list by description with count limit
    read_approved_comments = """
MATCH (prof) -[:PASSED]-> (o) - [r:COMMENT] -> () 
WHERE prof.id >= $start_name 
RETURN labels(o) as label, o, prof.user as credit, prof.id as batch_id, COUNT(r) AS count
    ORDER BY batch_id, label LIMIT $limit"""

    read_my_comments = """
MATCH (u:UserProfile {username:$user}) -[:HAS_ACCESS]-> (b:Batch)
    -[owner:OWNS]-> (o) - [r:COMMENT] -> ()
WHERE b.id >= $start_name
RETURN labels(o) as label, o, b.user as credit, b.id as batch_id, COUNT(r) AS count
    ORDER BY batch_id, label LIMIT $limit"""


