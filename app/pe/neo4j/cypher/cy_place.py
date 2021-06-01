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
//  WITH place, name, COLLECT(DISTINCT pn) AS names, COUNT(ref) AS uses
        OPTIONAL MATCH (place) -[:IS_INSIDE]-> (up:Place) -[:NAME]-> (upn:Place_name)
        OPTIONAL MATCH (place) <-[:IS_INSIDE]- (do:Place) -[:NAME]-> (don:Place_name)
        RETURN place, name, COUNT(DISTINCT ref) AS uses,
            COLLECT(DISTINCT pn) AS names,
            COLLECT(DISTINCT [ID(up), up.uuid, up.type, upn.name, upn.lang]) AS upper,
            COLLECT(DISTINCT [ID(do), do.uuid, do.type, don.name, don.lang]) AS lower
    ORDER BY name.name"""

    get_common_name_hierarchies = """
MATCH () -[:PASSED]-> (place:Place) -[:NAME_LANG {lang:$lang}]-> (name:Place_name)
    WHERE name.name >= $fw
WITH place, name ORDER BY name.name LIMIT  $limit
    OPTIONAL MATCH (place) <-[:PLACE]- (ref)
""" + _get_name_hierarchies_tail

    get_my_name_hierarchies = """
MATCH (b:Batch) -[:OWNS]-> (place:Place) -[:NAME_LANG {lang:$lang}]-> (name:Place_name)
    WHERE b.user = $user AND name.name >= $fw
WITH place, name ORDER BY name.name LIMIT $limit
    OPTIONAL MATCH (place) <-[:PLACE]- (ref) <-[*2]- (b)
        WHERE b.user = $user
""" + _get_name_hierarchies_tail

# Default language names update with $place_id, $fi_id, $sv_id
    link_name_lang = """
MATCH (fi:Place_name) <-[:NAME]- (place:Place),
    (place) -[:NAME]-> (sv:Place_name)  
    WHERE ID(place) = $place_id AND ID(fi) = $fi_id AND ID(sv) = $sv_id
OPTIONAL MATCH (place) -[r:NAME_LANG]-> ()
    DELETE r
MERGE (place) -[:NAME_LANG {lang:'fi'}]-> (fi)
MERGE (place) -[:NAME_LANG {lang:'sv'}]-> (sv)
RETURN DISTINCT ID(place) AS pl, ID(fi) AS fi, ID(sv) AS sv"""

# Default language names update with $place_id, $fi_id; sv_id is the same
    link_name_lang_single = """
MATCH (n:Place_name) <-[:NAME]- (place:Place)  
    WHERE ID(place) = $place_id AND ID(n) = $fi_id
OPTIONAL MATCH (place) -[r:NAME_LANG]-> ()
    DELETE r
MERGE (place) -[:NAME_LANG {lang:'fi'}]-> (n)
MERGE (place) -[:NAME_LANG {lang:'sv'}]-> (n)
RETURN DISTINCT ID(place) AS pl, ID(n) AS fi, ID(n) AS sv"""

# For place page
    _get_w_names_notes_tail = """
OPTIONAL MATCH (place) -[:NAME_LANG {lang:$lang}]-> (name:Place_name)
WITH place, name
    OPTIONAL MATCH (place) -[:NAME]-> (n:Place_name) 
        WHERE name is null or not n = name
    OPTIONAL MATCH (place) -[nr:NOTE]-> (note:Note)
    OPTIONAL MATCH (place) -[mr:MEDIA]-> (media:Media)
RETURN place, name,
    COLLECT(DISTINCT n) AS names,
    COLLECT (DISTINCT note) AS notes,
    COLLECT (DISTINCT media) AS medias"""
    get_common_w_names_notes = """
MATCH () -[:PASSED]-> (place:Place)
    WHERE place.uuid=$uuid""" + _get_w_names_notes_tail
    get_my_w_names_notes = """
MATCH (prof:UserProfile) -[:HAS_LOADED]-> (:Batch) -[:OWNS]-> (place:Place)
    WHERE prof.username = $user AND place.uuid=$uuid""" + _get_w_names_notes_tail

    # Result indi is a Person or Family
    get_person_family_events = """
MATCH (e:Event) -[:PLACE]-> (l:Place)
    WHERE ID(l) = $locid
WITH e,l
    MATCH (indi) -[r]-> (e)
    OPTIONAL MATCH (indi) -[:NAME]-> (n)
RETURN indi, r.role AS role, COLLECT(DISTINCT n) AS names, e AS event
ORDER BY e.date1"""
    get_person_events = """
MATCH (p:Person) -[r:EVENT]-> (e:Event) -[:PLACE]-> (l:Place)
    WHERE ID(l) = $locid
    MATCH (p) --> (n:Name)
    OPTIONAL MATCH (p) -[:F
WITH p, r, e, l, n ORDER BY n.order
RETURN p AS person, r.role AS role,
    COLLECT(n) AS names, e AS event
ORDER BY e.date1"""

    # Queries for Place page hierarchy
    read_pl_hierarchy = """
MATCH x= (p:Place)<-[:IS_INSIDE*]-(i:Place) WHERE ID(p) = $locid
    WITH NODES(x) AS nodes, relationships(x) AS r
    RETURN nodes, SIZE(r) AS lv, r
    UNION
MATCH x= (p:Place)-[:IS_INSIDE*]->(i:Place) WHERE ID(p) = $locid
    WITH NODES(x) AS nodes, relationships(x) AS r
    RETURN nodes, SIZE(r)*-1 AS lv, r
"""
    # Query for single Place without hierarchy
    root_query = """
MATCH (p:Place) WHERE ID(p) = $locid
RETURN p.type AS type, p.uuid AS uuid, p.pname AS name
"""
    # Query to get names for a Place with $locid, $lang
    read_pl_names="""
MATCH (place:Place) WHERE ID(place) = $locid
OPTIONAL MATCH (place) -[:NAME_LANG {lang:$lang}]-> (name:Place_name)
WITH place, name
    OPTIONAL MATCH (place) -[:NAME]-> (n:Place_name) 
        WHERE name is null or not n = name
RETURN name, COLLECT(n) AS names LIMIT 15
"""

#-------- Save to Batch -------------

    # Find the batch like '2019-02-24.006' and connect new object to that Batch
    create = """
MATCH (u:Batch {id:$batch_id})
CREATE (new_pl:Place)
    SET new_pl = $p_attr
CREATE (u) -[:OWNS]-> (new_pl) 
RETURN ID(new_pl) AS uniq_id"""

    # Set properties for an existing Place and connect it to Batch
    complete = """
MATCH (u:Batch {id:$batch_id})
MATCH (pl:Place) WHERE ID(pl) = $plid
    SET pl += $p_attr
CREATE (u) -[:OWNS]-> (pl)"""

    add_name = """
MATCH (pl:Place) WHERE ID(pl) = $pid
CREATE (pl) -[r:NAME {order:$order}]-> (n:Place_name)
    SET n = $n_attr
RETURN ID(n) AS uniq_id"""

    # Link to a known upper Place
    link_hier = """
MATCH (pl:Place) WHERE ID(pl) = $plid
MATCH (up:Place) WHERE ID(up) = $up_id
MERGE (pl) -[r:IS_INSIDE]-> (up)
    SET r = $r_attr"""

    # Link to a new dummy upper Place
    link_create_hier = """
MATCH (pl:Place) WHERE ID(pl) = $plid
CREATE (new_pl:Place)
    SET new_pl.handle = $up_handle
CREATE (pl) -[r:IS_INSIDE]-> (new_pl)
    SET r = $r_attr
RETURN ID(new_pl) AS uniq_id"""

    add_urls = """
MATCH (u:Batch {id:$batch_id})
CREATE (u) -[:OWNS]-> (n:Note) 
    SET n = $n_attr
WITH n
    MATCH (pl:Place) WHERE ID(pl) = $pid
    MERGE (pl) -[r:NOTE]-> (n)"""

    link_note = """
MATCH (pl:Place) WHERE ID(pl) = $pid
MATCH (n:Note)  WHERE n.handle=$hlink
CREATE (pl) -[r:NOTE]-> (n)"""

    link_media = """
MATCH (p:Place {handle: $p_handle})
MATCH (m:Media  {handle: $m_handle})
  CREATE (p) -[r:MEDIA]-> (m)
    SET r = $r_attr"""

class CypherPlaceStats:
    get_place_list_by_username = """
match (b:Batch{user:$username}) -[:OWNS]-> (e:Event) -[:PLACE]-> (p:Place) 
return p as place, count(p) as count
order by count desc
limit $count
"""

    get_place_list_common = """
match () -[:PASSED]-> (e:Event) -[:PLACE]-> (p:Place) 
return p as place, count(p) as count
order by count desc
limit $count
"""

class CypherPlaceMerge:

    delete_namelinks = """
MATCH (node) -[r:NAME_LANG]-> (pn)
WHERE ID(node) = $id
DELETE r"""

    merge_places = """
MATCH (p1:Place)        WHERE ID(p1) = $id1 
MATCH (p2:Place)        WHERE ID(p2) = $id2
CALL apoc.refactor.mergeNodes([p1,p2],
    {properties:'discard',mergeRels:true})
YIELD node
WITH node
MATCH (node) -[r2:NAME]-> (pn2)
RETURN node, collect(pn2) AS names"""

