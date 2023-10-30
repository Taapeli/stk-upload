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
Created on 5.3.2020

@author: jm
'''
class CypherSource():
    """ Cypher clauses for Source data access.
    """

    # ------------------------ Cypher fragments ------------------------

    get_sources = """
MATCH (root) -[:OBJ_SOURCE]-> (s:Source)
    OPTIONAL MATCH (s) -[:NOTE]-> (note)
    OPTIONAL MATCH (s) -[r:REPOSITORY]-> (rep:Repository)
    OPTIONAL MATCH (c:Citation) -[:SOURCE]-> (s)
    OPTIONAL MATCH (c) <-[:CITATION]- (citator)
RETURN root, s as source, collect(DISTINCT note) as notes, 
       collect(DISTINCT [r.medium, rep]) as repositories,
       COUNT(c) AS cit_cnt, COUNT(citator) AS ref_cnt 
ORDER BY toUpper(s.stitle)"""

    get_sources_with_selections = """
MATCH (root) -[:OBJ_SOURCE]-> (s:Source)
    WHERE tolower(s.stitle) CONTAINS $key1 OR s.stitle CONTAINS $key2 
WITH root, s ORDER BY toUpper(s.stitle)
    OPTIONAL MATCH (s) -[:NOTE]-> (note)
    OPTIONAL MATCH (s) -[r:REPOSITORY]-> (rep:Repository)
    OPTIONAL MATCH (c:Citation) -[:SOURCE]-> (s)
    OPTIONAL MATCH (c) <-[:CITATION]- (citator)
RETURN root, s as source, collect(DISTINCT note) as notes, 
       collect(DISTINCT [r.medium, rep]) as repositories,
       COUNT(c) AS cit_cnt, COUNT(citator) AS ref_cnt 
ORDER BY toUpper(s.stitle)"""

    get_source_iid = """
MATCH (root) -[:OBJ_SOURCE]-> (s:Source{iid:$iid})
WITH root, s
    OPTIONAL MATCH (s) -[r:REPOSITORY]-> (rep:Repository)
    OPTIONAL MATCH (s) -[:NOTE]-> (n)
RETURN root, s AS source, 
    COLLECT(DISTINCT n) AS notes,
    COLLECT(DISTINCT [r.medium,rep]) AS reps
    ORDER BY source.stitle"""

    get_citators_of_source = """
match (s) <-[:SOURCE]- (c:Citation) where id(s)=$uniq_id
match (c) <-[:CITATION]- (x)
with c,x
    optional match (c) -[:NOTE]-> (n:Note)
    optional match (x) <-[re:EVENT|NAME|MEDIA]- (pe)
return c as citation, collect(distinct n) as notes, x as near,
    collect(distinct [pe, re.role]) as far
order by c.id, x.id"""

    # ---------------- Citations for different object ------------------

    # 1) cypher_prefix for different objects
    media_prefix = "MATCH (a:Media {iid:$iid}) "
    # 2) common read clauses
    get_obj_source_notes = """
MATCH (a) -[:CITATION]-> (cita:Citation) -[:SOURCE]-> (sour:Source)
OPTIONAL MATCH (sour) -[:REPOSITORY]-> (repo:Repository)
OPTIONAL MATCH (cita) -[:NOTE]-> (c_note:Note)
OPTIONAL MATCH (sour) -[:NOTE]-> (s_note:Note)
RETURN //root, a,
    cita, sour, repo,
    COLLECT(DISTINCT s_note) AS source_notes,
    COLLECT(DISTINCT c_note) AS citation_notes
"""

    # ------------------------ Cypher clauses ------------------------

    get_citation_sources_repositories = """
MATCH (cita:Citation) -[:SOURCE]-> (source:Source)
    WHERE ID(cita) IN $uid_list
OPTIONAL MATCH (source) -[rel:REPOSITORY]-> (repo:Repository)
RETURN ID(cita) AS uniq_id, source, properties(rel) as rel, repo"""

    source_fulltext_search = """
CALL db.index.fulltext.queryNodes("sourcetitle",$searchtext) 
    YIELD node as source, score
WITH source,score
    ORDER by score desc LIMIT $limit

MATCH (root:Root {state:$state}) -[:OBJ_SOURCE]-> (source)
RETURN DISTINCT source, score"""


    # --- Cypher by handle ----

    create_to_batch = """
MATCH (b:Root {id: $batch_id})
MERGE (b) -[r:OBJ_SOURCE]-> (s:Source {handle: $s_attr.handle}) 
    SET s = $s_attr
RETURN ID(s) as uniq_id"""

    s_link_note = """
MATCH (n:Source {handle:$handle})
MATCH (m:Note {handle:$hlink})
CREATE (n) -[r:NOTE]-> (m)"""
# MATCH (n:Source {handle:$handle})
# MATCH (m:Note {handle:$hlink})
# CREATE (n) -[r:NOTE]-> (m)"""

    link_repository = """
MATCH (n:Source) WHERE n.handle=$handle
MATCH (m:Repository) WHERE m.handle=$hlink
MERGE (n) -[r:REPOSITORY {medium:$medium}]-> (m)"""

