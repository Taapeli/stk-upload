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
Created on 12.3.2020

@author: jm
'''

class CypherPlace():
    '''
    Neo4j Cypher clases for Place objects
    '''

    _get_name_hierarchies_tail = """
    OPTIONAL MATCH (place) -[:NAME]-> (pn:Place_name)
        WHERE NOT pn = name
        OPTIONAL MATCH (place) -[:IS_INSIDE]-> (up:Place) -[:NAME]-> (upn:Place_name)
        OPTIONAL MATCH (place) <-[:IS_INSIDE]- (do:Place) -[:NAME]-> (don:Place_name)
        RETURN root, place, name, COUNT(DISTINCT ref) AS uses,
            COLLECT(DISTINCT pn) AS names,
            COLLECT(DISTINCT [-1, up.iid, up.type, upn.name, upn.lang]) AS upper,
            COLLECT(DISTINCT [-2, do.iid, do.type, don.name, don.lang]) AS lower
    ORDER BY name.name""" #TODO Remove -1, -2

    get_name_hierarchies = """
MATCH (root) -[:OBJ_PLACE]-> (place:Place) -[:NAME_LANG {lang:$lang}]-> (name:Place_name)
    WHERE name.name >= $fw
WITH root, place, name ORDER BY name.name LIMIT $limit
    OPTIONAL MATCH (place) <-[:PLACE]- (ref)
""" + _get_name_hierarchies_tail

# Default language names update with $place_id, $fi_id, $sv_id
    link_name_lang = """
MATCH (place:Place) -[:NAME]-> (fi:Place_name),
    (place) -[:NAME]-> (sv:Place_name)  
    WHERE place.iid = $place_id AND fi.iid = $fi_id AND sv.iid = $sv_id
OPTIONAL MATCH (place) -[r:NAME_LANG]-> ()
    DELETE r
MERGE (place) -[:NAME_LANG {lang:'fi'}]-> (fi)
MERGE (place) -[:NAME_LANG {lang:'sv'}]-> (sv)
RETURN DISTINCT place.iid AS pl, fi.iid AS fi, sv.iid AS sv"""

# Default language names update with $place_id, $fi_id; sv_id is the same
    link_name_lang_single = """
MATCH (n:Place_name) <-[:NAME]- (place:Place)  
    WHERE place.iid = $place_id AND n.iid = $fi_id
OPTIONAL MATCH (place) -[r:NAME_LANG]-> ()
    DELETE r
MERGE (place) -[:NAME_LANG {lang:'fi'}]-> (n)
MERGE (place) -[:NAME_LANG {lang:'sv'}]-> (n)
RETURN DISTINCT place.iid AS pl, n.iid AS fi, n.iid AS sv"""

# For place page
    get_w_citas_names_notes = """
MATCH  (root) -[:OBJ_PLACE]-> (place:Place {iid:$iid})
OPTIONAL MATCH (place) -[:NAME_LANG {lang:$lang}]-> (name:Place_name)
WITH root, place, name
    OPTIONAL MATCH (place) -[:NAME]-> (n:Place_name) 
        WHERE name is null or not n = name
    OPTIONAL MATCH (place) -[nr:NOTE]-> (note:Note)
    OPTIONAL MATCH (place) -[mr:MEDIA]-> (media:Media)
    OPTIONAL MATCH (place) -[cr:CITATION]-> (cita:Citation)
RETURN root, place, name,
    COLLECT(DISTINCT n) AS names,
    COLLECT (DISTINCT note) AS notes,
    COLLECT (DISTINCT media) AS medias,
    COLLECT (DISTINCT cita) AS citas"""

    get_notes_for_citas = """
MATCH (root) -[:OBJ_OTHER]-> (cita) -[:NOTE]-> (note:Note)
    WHERE cita.iid in $citas
RETURN cita.iid AS cid, note"""

    # Result indi is a Person or Family
    get_place_events = """
MATCH (e:Event) -[:PLACE]-> (l:Place {iid: $locid})
WITH e,l
    MATCH (indi) -[r]-> (e)
    OPTIONAL MATCH (indi) -[:NAME]-> (n)
RETURN indi, r.role AS role, COLLECT(DISTINCT n) AS names, e AS event
ORDER BY e.date1"""
    get_person_events = """
MATCH (p:Person) -[r:EVENT]-> (e:Event) -[:PLACE]-> (l:Place {iid: $locid})
    MATCH (p) --> (n:Name)
    OPTIONAL MATCH (p) -[:F
WITH p, r, e, l, n ORDER BY n.order
RETURN p AS person, r.role AS role,
    COLLECT(n) AS names, e AS event
ORDER BY e.date1"""

    # Queries for Place page hierarchy
    read_pl_hierarchy = """
MATCH x= (p:Place {iid: $locid})<-[:IS_INSIDE*]-(i:Place)
    WITH NODES(x) AS nodes, relationships(x) AS r
    RETURN nodes, SIZE(r) AS lv, r
    UNION
MATCH x= (p:Place {iid: $locid})-[:IS_INSIDE*]->(i:Place)
    WITH NODES(x) AS nodes, relationships(x) AS r
    RETURN nodes, SIZE(r)*-1 AS lv, r
"""
    # Query for single Place without hierarchy
    root_query = """
MATCH (p:Place {iid: $locid})
RETURN p.type AS type, p.iid AS iid, p.pname AS name
"""
    # Query to get names for a Place with $locid, $lang
    read_pl_names="""
MATCH (place:Place {iid: $locid})
OPTIONAL MATCH (place) -[:NAME_LANG {lang:$lang}]-> (name:Place_name)
WITH place, name
    OPTIONAL MATCH (place) -[:NAME]-> (n:Place_name) 
        WHERE name is null or not n = name
RETURN name, COLLECT(n) AS names LIMIT 15
"""

#-------- Save to Batch -------------

    # Find the batch like '2019-02-24.006' and connect new object to that Batch
    create = """
MATCH (u:Root {id:$batch_id})
CREATE (new_pl:Place)
    SET new_pl = $p_attr
CREATE (u) -[:OBJ_PLACE]-> (new_pl)"""
#! RETURN ID(new_pl) AS uniq_id"""

    # Set properties for an existing Place and connect it to Batch
    # Set properties for an Place matching handle and connect it to Batch
    complete_handle = """
MATCH (u:Root {id:$batch_id})
MATCH (pl:Place {handle: $p_handle})
    SET pl += $p_attr
CREATE (u) -[:OBJ_PLACE]-> (pl)"""

    add_name = """
MATCH (pl:Place {iid: $pid})
CREATE (pl) -[r:NAME {order:$order}]-> (n:Place_name)
    SET n = $n_attr"""
#! RETURN ID(n) AS uniq_id"""

    # Link to a known upper Place
#     link_hier_iid = """
# MATCH (pl:Place {iid: $plid})
# MATCH (up:Place {iid: $up_id})
# MERGE (pl) -[r:IS_INSIDE]-> (up)
#     SET r = $r_attr"""
    link_hier_handle = """
MATCH (pl:Place {handle: $p_handle})
MATCH (up:Place {handle: $up_handle})
MERGE (pl) -[r:IS_INSIDE]-> (up)
    SET r = $r_attr
RETURN up.iid AS iid"""

    # Link to a new dummy upper Place
    link_create_hier_handle = """
MATCH (pl:Place {handle: $p_handle})
CREATE (new_pl:Place)
    SET new_pl.handle = $up_handle
CREATE (pl) -[r:IS_INSIDE]-> (new_pl)
    SET r = $r_attr
RETURN new_pl.iid AS iid"""

    add_urls = """
MATCH (u:Root {id:$batch_id})
CREATE (u) -[:OBJ_OTHER]-> (n:Note) 
    SET n = $n_attr
WITH n
    MATCH (pl:Place {iid: $pid})
    MERGE (pl) -[r:NOTE]-> (n)"""

    pl_link_note = """
MATCH (n:Place {handle:$handle})
MATCH (m:Note {handle:$hlink})
CREATE (n) -[r:NOTE]-> (m)"""
# MATCH (pl:Place {iid: $pid})
# MATCH (n:Note)  WHERE n.handle=$hlink
# CREATE (pl) -[r:NOTE]-> (n)"""

    link_media = """
MATCH (p:Place {handle: $p_handle})
MATCH (m:Media  {handle: $m_handle})
  CREATE (p) -[r:MEDIA]-> (m)
    SET r = $r_attr"""

class CypherPlaceStats:
    get_place_list = """
match (root) -[:OBJ_PLACE]-> (p:Place)
optional match (p) <-[:IS_INSIDE*]- (p2:Place)
return p as place, count(p2) as count
    order by count desc
    limit $count"""

    get_place_list_for_place_data = """
match (root) -[:OBJ_PLACE]-> (p:Place) <-[:IS_INSIDE*]- (p2:Place)
return p as place, count(p2) as count 
    order by count desc
    limit $count
"""
    get_citated_places_for_place_data = """
match (root) -[:OBJ_PLACE]-> (p:Place) 
    optional match (p) -[:CITATION]-> (c:Citation)
    optional match (p) <-[:IS_INSIDE]- (p2:Place)
return p.iid, p2.pname, p.pname, count(c) as count 
    order by count desc
    limit $count
"""

class CypherPlaceMerge:

    delete_namelinks = """
MATCH (node) -[r:NAME_LANG]-> (pn)
WHERE ID(node) = $id
DELETE r"""
#TODO: Obsolete key ID()

    merge_places = """
MATCH (p1:Place {iid: $id1})
MATCH (p2:Place {iid: $id2})
CALL apoc.refactor.mergeNodes([p1,p2],
    {properties:'discard',mergeRels:true})
YIELD node
WITH node
MATCH (node) -[r2:NAME]-> (pn2)
RETURN node, collect(pn2) AS names"""

