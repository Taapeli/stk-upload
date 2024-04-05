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

#
# Reading and updating Neo4j database
#
# 12.2.2018 - 16.5.2020 / JMä
#

class CypherFamily():
    '''
    Cypher clauses for reading and creating Families
    '''

# ----- Get Family node by iid

    get_family_iid = '''
MATCH (root) -[r:OBJ_FAMILY]-> (f:Family {iid:$f_id}) 
RETURN f, root'''

    get_family_parents = """
MATCH (f:Family {iid:$fuid}) -[r:PARENT]-> (pp:Person)
    OPTIONAL MATCH (pp) -[:NAME]-> (np:Name {order:0}) 
    OPTIONAL MATCH (pp) -[:EVENT]-> (pbe:Event {type:"Birth"})
    OPTIONAL MATCH (pp) -[:EVENT]-> (pde:Event {type:"Death"})
RETURN r.role AS role, pp AS person, np AS name, pbe AS birth, pde AS death"""

    get_family_children = """
MATCH (f:Family {iid:$fuid})
OPTIONAL MATCH (f) -[:CHILD]- (pc:Person) 
    OPTIONAL MATCH (pc) -[:NAME]-> (nc:Name {order:0}) 
    OPTIONAL MATCH (pc) -[:EVENT]-> (cbe:Event {type:"Birth"})
    OPTIONAL MATCH (pc) -[:EVENT]-> (cde:Event {type:"Death"})
RETURN pc AS person, nc AS name, cbe AS birth, cde AS death
    ORDER BY cbe.date1"""

#     get_family_events = """
# MATCH (f:Family) -[:EVENT]-> (fe:Event) WHERE ID(f) = $fuid
# OPTIONAL MATCH (fe) -[:PLACE]-> (fep:Place)
# RETURN fe as event, fep AS place"""

    get_events_w_places = """
MATCH (x:Family {iid:$fuid}) -[:EVENT]-> (e:Event)
OPTIONAL MATCH (e) -[:PLACE]-> (pl:Place)
OPTIONAL MATCH (pl) -[:NAME]-> (pn:Place_name)
OPTIONAL MATCH (pl) -[ri:IS_INSIDE]-> (pi:Place)
OPTIONAL MATCH (pi) -[NAME]-> (pin:Place_name)
WITH e AS event, pl AS place, COLLECT(DISTINCT pn) AS names,
    pi, ri, COLLECT(DISTINCT pin) AS in_names
RETURN event, place, names,
    COLLECT(DISTINCT [pi, ri, in_names]) AS inside"""

    get_family_sources = """
MATCH (f:Family) -[:CITATION]-> (c:Citation)  WHERE f.iid in $id_list
    OPTIONAL MATCH (c) -[:SOURCE]-> (s:Source)-[:REPOSITORY]-> (re:Repository)
RETURN f.iid AS src_id,
    re AS repository, s AS source, c AS citation"""

    get_family_notes = """
MATCH (f:Family) -[:NOTE]- (note:Note) WHERE f.iid in $id_list
    OPTIONAL MATCH (f) 
RETURN f.iid AS src_id, note"""

    get_dates_parents = """
MATCH (family:Family {iid: $id})
OPTIONAL MATCH (family)-[:PARENT {role:"father"}]-(father:Person)
OPTIONAL MATCH (father)-[:EVENT]-(father_death:Event {type:"Death"})
OPTIONAL MATCH (family)-[:PARENT {role:"mother"}]-(mother:Person)
OPTIONAL MATCH (mother)-[:EVENT]-(mother_death:Event {type:"Death"})
OPTIONAL MATCH (family)-[:EVENT]-(event:Event) WHERE event.type="Marriage"
OPTIONAL MATCH (family)-[:EVENT]-(divorce_event:Event {type:"Divorce"})
RETURN father.sortname AS father_sortname, father_death.date1 AS father_death_date,
       mother.sortname AS mother_sortname, mother_death.date1 AS mother_death_date,
       event.date1 AS marriage_date, divorce_event.date1 AS divorce_date"""

    get_person_families = """
MATCH (p:Person {iid:$p_iid}) <-- (family:Family)
MATCH (family) -[r]-> (person:Person)
OPTIONAL MATCH (person) -[:EVENT]-> (birth:Event {type:'Birth'}) 
RETURN family, TYPE(r) AS type, r.role AS role, person, birth 
ORDER BY family, person.birth_high"""


# ----- Family data for families page

    get_families_by_father = """
MATCH (root) -[:OBJ_FAMILY]-> (f:Family)
    WHERE f.father_sortname>=$fw
OPTIONAL MATCH (f) -[r:PARENT]-> (pp:Person)
OPTIONAL MATCH (pp) -[:NAME]-> (np:Name {order:0}) 
OPTIONAL MATCH (f) -[:CHILD]-> (pc:Person) 
OPTIONAL MATCH (f) -[:EVENT]-> (:Event {type:"Marriage"})-[:PLACE]->(p:Place)
RETURN f, p.pname AS marriage_place,
    COLLECT([r.role, pp, np]) AS parent, 
    COLLECT(DISTINCT pc) AS child, 
    COUNT(DISTINCT pc) AS no_of_children 
    ORDER BY f.father_sortname LIMIT $limit"""

    get_families_by_mother = get_families_by_father.replace("father", "mother")

# ----- Family load in Batch

    create_to_batch = """
MATCH (b:Root {id: $batch_id})
MERGE (b) -[r:OBJ_FAMILY]-> (f:Family {handle: $f_attr.handle}) 
    SET f = $f_attr"""
#!RETURN f.iid as iid"""

    link_parent = """
MATCH (n:Family {handle:$f_handle})
MATCH (m:Person {handle:$p_handle})
MERGE (n) -[r:PARENT {role:$role}]-> (m)"""

    link_event = """
MATCH (n:Family {handle:$f_handle})
MATCH (m:Event {handle:$e_handle})
MERGE (n)-[r:EVENT]->(m)
    SET r.role = $role"""

    link_child = """
MATCH (n:Family {handle:$f_handle})
MATCH (m:Person {handle:$p_handle})
MERGE (n)-[r:CHILD]->(m)"""

    set_dates_sortname = """
MATCH (family:Family {iid: $id})
SET family += $f_attr"""

