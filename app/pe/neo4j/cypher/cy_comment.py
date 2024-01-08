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

# Write Topic and Comment data

    # New Topic to any object (should not be a Topic or Comment)
    create_topic = """
MATCH (obj)  WHERE id(obj) = $attr.object_id 
MATCH (u:UserProfile)   WHERE u.username = $attr.username
CREATE (obj) -[:COMMENT] -> (c:Topic) <-[:COMMENTED]- (u)
    SET c.text = $attr.text
    SET c.title = $attr.title
    SET c.timestamp = timestamp()
RETURN c AS comment, labels(obj)[0] AS obj_type"""
    # New Comment to a Topic or Comment
    create_comment = """
MATCH (obj)  WHERE id(obj) = $attr.object_id
MATCH (u:UserProfile)   WHERE u.username = $attr.username
CREATE (obj:Topic) -[:COMMENT] -> (c:Comment) <-[:COMMENTED]- (u)
    SET c.text = $attr.text
    SET c.title = $attr.title
    SET c.timestamp = timestamp()
RETURN c AS comment, labels(obj)[0] AS obj_type"""

# Read Comment data

    fetch_obj_comments = """
MATCH (p) -[:COMMENT] -> (c) <-[:COMMENTED]- (u:UserProfile)
    WHERE id(p) = $iid AND c.timestamp <= $start
RETURN c AS comment, u.username AS commenter 
    ORDER BY c.timestamp DESC LIMIT 5"""

#     # Topic list for objects with count limit
#     get_topics = """
# MATCH (root) --> (o) -[:COMMENT]-> (c)  <-[:COMMENTED]- (u:UserProfile)
# OPTIONAL MATCH repl = ( (c) -[:COMMENT*]-> () )
# RETURN o, c, u.username as commenter, 
#     coalesce(length(repl),0) AS count,
#     root
# ORDER BY c.timestamp desc LIMIT $limit"""

    # Topic list including 1) batch object comments + 2) root comments
    # returning same fields
    get_topics = """
// 1. Batch object comments
MATCH (root) --> (o) -[:COMMENT]-> (c)  <-[:COMMENTED]- (u:UserProfile)
    OPTIONAL MATCH repl = ( (c) -[:COMMENT*]-> () )
//WITH root, COLLECT(DISTINCT [o, c, u.username, length(repl)]) AS rows
  //WITH root, rows AS all_rows
  //    UNWIND all_rows AS row
WITH root, o, c, u.username AS commenter, length(repl) AS count
    RETURN o, c, commenter, COALESCE(count,0) AS count, root
        ORDER BY c.timestamp DESC
        LIMIT $limit"""

    get_topics_for_root = """
// 2. Comments to Root self
MATCH (root) -[:COMMENT]-> (c1)  <-[:COMMENTED]- (u1:UserProfile)
    OPTIONAL MATCH repl1 = ( (c1) -[:COMMENT*]-> () )
// 3. Combined
  //WITH root, COLLECT(DISTINCT [null, c1, u1.username, length(repl1)]) AS rows_root
  //    UNWIND rows_root AS row
WITH root, null AS o, c1 AS c, u1.username AS commenter, length(repl1) AS count
    RETURN o, c, commenter, COALESCE(count,0) AS count, root
        ORDER BY c.timestamp DESC
        LIMIT $limit"""
