# Cypher clauses for models.gen module
#
# Reading and updating Neo4j database
#
# See also: gramps.cypher_gramps for updates from Gramps xml file
#
# 12.2.2018 / JMä


class Cypher_note():
    '''
    Cypher clases for creating and accessing Notes
    '''

    get_person_notes = '''
match (p) -[:NOTE]-> (n:Note) where id(p) = $pid 
    return id(p) as p_id, null as e_id, id(n) as n_id, n
union
match (p) -[:EVENT]-> (e:Event) -[:NOTE]-> (n:Note) where id(p) = $pid 
    return id(p) as p_id, id(e) as e_id, id(n) as n_id, n'''

    get_by_ids = """
MATCH (n:Note)    WHERE ID(n) in $nid
RETURN ID(n) AS uniq_id, n"""


class Cypher_person():
    '''
    Cypher clases for creating and accessing Places
    '''
# For Person_pg v3
    get_person = """MATCH (root) -[r:OWNS|PASSED]-> (p:Person {uuid:$uuid}) 
RETURN p, type(r) AS root_type, root"""
#     get_by_user = """
# MATCH (b:UserProfile {username:$user}) -[:HAS_LOADED]-> (batch:Batch)
#        -[:OWNS]-> (p:Person {uuid:$uuid})
# RETURN p, batch"""
#     get_public = """MATCH (root) -[:PASSED]-> (p:Person {uuid:$uuid}) 
# RETURN p, root"""
    get_names_events = """
MATCH (p:Person) -[rel:NAME|EVENT]-> (x) WHERE ID(p) = $uid
RETURN rel, x ORDER BY x.order"""
    get_families = """
MATCH (p:Person) <-[rel:CHILD|PARENT]- (f:Family) WHERE ID(p) = $uid
OPTIONAL MATCH (f) -[:EVENT]-> (fe:Event)
OPTIONAL MATCH (f) -[mr:CHILD|PARENT]-> (m:Person) -[:NAME]-> (n:Name {order:0})
OPTIONAL MATCH (m) -[:EVENT]-> (me:Event {type:"Birth"})
RETURN rel, f AS family, COLLECT(distinct fe) AS events, 
    COLLECT(distinct [mr, m, n, me]) AS members
    ORDER BY family.date1"""
    get_places = """
MATCH (x) -[:PLACE]-> (pl:Place)
    WHERE ID(x) IN $uid_list
OPTIONAL MATCH (pl) -[:NAME]-> (pn:Place_name)
OPTIONAL MATCH (pl) -[ri:IS_INSIDE]-> (pi:Place)
OPTIONAL MATCH (pi) -[:NAME]-> (pin:Place_name)
RETURN LABELS(x)[0] AS label, ID(x) AS uniq_id, 
    pl, COLLECT(DISTINCT pn) AS pnames,
    pi, COLLECT(DISTINCT pin) AS pinames"""
    get_citation_note_media = """
MATCH (x) -[r:CITATION|NOTE|MEDIA]-> (y)
    WHERE ID(x) IN $uid_list
RETURN LABELS(x)[0] AS label, ID(x) AS uniq_id, r, y"""
    #        (c) --> (s:Source) --> (r:Repository)

#For Person_pg v2
    all_nodes_query_w_apoc="""
MATCH (p:Person {uuid:$uuid})
CALL apoc.path.subgraphAll(p, {maxLevel:4, 
        relationshipFilter: 'EVENT>|NAME>|PLACE>|CITATION>|SOURCE>|REPOSITORY>|NOTE>|MEDIA|HIERARCHY>|<CHILD|<PARENT'}) 
    YIELD nodes, relationships
RETURN extract(x IN relationships | 
        [id(startnode(x)), type(x), properties(x), id(endnode(x))]) as relations,
        extract(x in nodes | x) as nodelist"""
#     #TODO Obsolete
    all_nodes_uniq_id_query_w_apoc="""
MATCH (p:Person) WHERE id(p) = $uniq_id
CALL apoc.path.subgraphAll(p, {maxLevel:4, 
        relationshipFilter: 'EVENT>|NAME>|PLACE>|CITATION>|SOURCE>|REPOSITORY>|NOTE>|MEDIA|HIERARCHY>|<CHILD|<PARENT'}) 
    YIELD nodes, relationships
RETURN extract(x IN relationships | 
        [id(startnode(x)), type(x), properties(x), id(endnode(x))]) as relations,
        extract(x in nodes | x) as nodelist"""

# Ver 0.2 Person lists with names and events
    read_my_persons_with_events_starting_name = """
MATCH (prof:UserProfile) -[:HAS_LOADED]-> (b:Batch) -[:OWNS]-> (p:Person)
    WHERE prof.username = $user AND p.sortname >= $start_name
WITH p ORDER BY p.sortname LIMIT $limit
    MATCH (p:Person) -[:NAME]-> (n:Name)
    OPTIONAL MATCH (p) -[re:EVENT]-> (e:Event)
    OPTIONAL MATCH (p) <-[:PARENT|MOTHER|FATHER]- (f:Family) -[rf:EVENT]-> (fe:Event)
WITH p, n, re.role as role, e, f.rel_type as rel, fe  ORDER BY p.sortname, n.order
    OPTIONAL MATCH (e) -[:PLACE]-> (pl:Place)
    OPTIONAL MATCH (fe) -[:PLACE]-> (fpl:Place)
RETURN p as person, 
    COLLECT(distinct n) AS names,
    COLLECT(distinct [e, pl.pname, role]) + COLLECT(distinct [fe, fpl.pname, rel]) AS events 
    ORDER BY person.sortname"""

# Common data
    read_approved_persons_with_events_starting_name = """
MATCH () -[:PASSED]-> (p:Person)
    WHERE p.sortname >= $start_name
WITH p //, COLLECT(DISTINCT b.user) as owners
ORDER BY p.sortname LIMIT $limit
    MATCH (p:Person) -[:NAME]-> (n:Name)
    OPTIONAL MATCH (p) -[re:EVENT]-> (e:Event)
    OPTIONAL MATCH (p) <-[:PARENT|MOTHER|FATHER]- (f:Family) -[rf:EVENT]-> (fe:Event)
WITH p, n, re.role as role, e, f.rel_type as rel, fe //, owners
ORDER BY p.sortname, n.order
    OPTIONAL MATCH (e) -[:PLACE]-> (pl:Place)
    OPTIONAL MATCH (fe) -[:PLACE]-> (fpl:Place)
RETURN p as person, 
    COLLECT(distinct n) as names, 
    COLLECT(distinct [e, pl.pname, role]) + COLLECT(distinct [fe, fpl.pname, rel]) AS events
    //, owners
ORDER BY person.sortname"""

#Todo: obsolete with no approved common data
    read_all_persons_with_events_starting_name = """
MATCH (b:Batch) -[:OWNS]-> (p:Person)
    WHERE p.sortname >= $start_name
WITH p, COLLECT(DISTINCT b.user) as owners
ORDER BY p.sortname LIMIT $limit
    MATCH (p:Person) -[:NAME]-> (n:Name)
    OPTIONAL MATCH (p) -[re:EVENT]-> (e:Event)
    OPTIONAL MATCH (p) <-[:PARENT|MOTHER|FATHER]- (f:Family) -[rf:EVENT]-> (fe:Event)
WITH p, n, re.role as role, e, f.rel_type as rel, fe, owners
ORDER BY p.sortname, n.order
    OPTIONAL MATCH (e) -[:PLACE]-> (pl:Place)
    OPTIONAL MATCH (fe) -[:PLACE]-> (fpl:Place)
RETURN p as person, 
    COLLECT(distinct n) as names, 
    COLLECT(distinct [e, pl.pname, role]) + COLLECT(distinct [fe, fpl.pname, rel]) AS events,
    owners
ORDER BY person.sortname"""


#Todo Fix this? Or an example only?
    read_persons_list_by_refn = """
MATCH p = (search:Refname) -[:BASENAME*0..3 {use:'surname'}]-> (person:Person)
WHERE search.name STARTS WITH 'Kottu'
WITH search, person
MATCH (person) -[:NAME]-> (name:Name)
OPTIONAL MATCH (person) <-[:BASENAME*0..3]- (refn:Refname)
WITH name, person, COLLECT(DISTINCT refn.name) AS refnames, 
    TOUPPER(LEFT(name.surname,1)) as initial
OPTIONAL MATCH (person) -[r:EVENT]-> (event:Event)
OPTIONAL MATCH (event) -[:PLACE]-> (place:Place)
RETURN CASE WHEN name.order = 0 THEN id(person) END as id, 
    name, initial, 
    person, refnames,
    CASE WHEN name.order = 0 THEN COLLECT(DISTINCT [r.role, event.id, place.pname])
    ELSE id(person)
    END AS events
ORDER BY TOUPPER(name.surname), name.firstname limit 20"""

# Ver 0.1 different person lists
#Todo Fix this: (person) <-[:REFNAME]-
    _get_events_tail = """
 OPTIONAL MATCH (batch:Batch) -[:OWNS]-> (person)
 OPTIONAL MATCH (person) -[r:EVENT]-> (event:Event)
 OPTIONAL MATCH (event) -[:PLACE]-> (place:Place)
 OPTIONAL MATCH (person) <-[:BASENAME*0..3]- (refn:Refname)
RETURN batch.user AS user, person, 
    COLLECT(DISTINCT name) AS names,
    COLLECT(DISTINCT refn.name) AS refnames,
    COLLECT(DISTINCT [r.role, event, place.pname]) AS events"""
    _get_events_surname = """, TOUPPER(LEFT(name.surname,1)) as initial 
    ORDER BY TOUPPER(names[0].surname), names[0].firstname"""
    _get_events_firstname = """, LEFT(name.firstname,1) as initial 
    ORDER BY TOUPPER(names[0].firstname), names[0].surname, names[0].suffix"""
    _get_events_patronyme = """, LEFT(name.suffix,1) as initial 
    ORDER BY TOUPPER(names[0].suffix), names[0].surname, names[0].firstname"""

    _limit_years_clause = """
WHERE person.birth_low <= $years[1]
  AND person.death_high >= $years[0]
"""

    get_events_all = "MATCH (person:Person) -[:NAME]-> (name:Name)" \
        + _limit_years_clause + _get_events_tail + _get_events_surname

    get_events_all_firstname = "MATCH (person:Person) -[:NAME]-> (name:Name)" \
        + _limit_years_clause + _get_events_tail + _get_events_firstname

    get_events_all_patronyme = "MATCH (person:Person) -[:NAME]-> (name:Name)" \
        + _limit_years_clause + _get_events_tail + _get_events_patronyme

    get_events_uniq_id = """
MATCH (person:Person) -[:NAME]-> (name:Name)
WHERE ID(person) = $id""" + _get_events_tail

    get_events_by_refname = """
MATCH path = ( (rn0:Refname {name:$name}) -[:BASENAME*0..3]- (:Refname))
WITH nodes(path) AS x UNWIND x AS rn
    MATCH (rn) -[:REFNAME]-> (person:Person) -[:NAME]-> (name:Name)
""" + _get_events_tail + _get_events_surname
#Replaced 26.4.2020
#MATCH (refn:Refname {name:$name}) -[:BASENAME*1..3]-> (person:Person) --> (name:Name) 

    # With attr={'use':rule, 'name':name}
    get_common_events_by_refname_use = """
MATCH path = ( (search:Refname) -[:BASENAME*0..3 {use:$attr.use}]- (:Refname) )
WHERE search.name STARTS WITH $attr.name
WITH search, nodes(path) AS x UNWIND x AS rn
    MATCH (rn) -[:REFNAME {use:$attr.use}]-> (person:Person) <-[:PASSED]- (batch)
    MATCH (person) -[:NAME]-> (name:Name {order:0})
WITH person, name""" + _get_events_tail + _get_events_surname
#Replaced 26.4.2020
#MATCH p = (search:Refname) -[:BASENAME*1..3 {use:$attr.use}]-> (person:Person)
#    <-[:PASSED]- (batch)

    # With attr={'use':rule, 'name':name}, user=user
    get_my_events_by_refname_use = """
MATCH path = ( (search:Refname) -[:BASENAME*0..3]- (:Refname))
    WHERE search.name STARTS WITH $attr.name
WITH nodes(path) AS x UNWIND x AS rn
    MATCH (rn) -[:REFNAME {use:$attr.use}]-> (person:Person) 
          <-[:OWNS]- (:Batch {user:$user})
    MATCH (person) -[:NAME]-> (name:Name {order:0})
WITH person, name""" + _get_events_tail + _get_events_surname

#Todo Fix this: (person) <-[:REFNAME]-
    get_both_events_by_refname_use = """
MATCH p = (search:Refname) -[:BASENAME*0..3 {use:$attr.use}]-> (person:Person)
    <-[re:OWNS|PASSED]- (b:Batch)
WHERE search.name STARTS WITH $attr.name
WITH search, person, re WHERE type(re) = "PASSED" or b.user = $user
MATCH (person) -[:NAME]-> (name:Name {order:0})
WITH person, name""" + _get_events_tail + _get_events_surname

    get_confidences_all = """
MATCH (person:Person)
OPTIONAL MATCH (person) -[:EVENT]-> (:Event) -[:CITATION]-> (c1:Citation)
OPTIONAL MATCH (person) <-[:PARENT]- (:Family) - [:EVENT] -> (:Event) -[:CITATION]-> (c2:Citation)
RETURN ID(person) AS uniq_id, COLLECT(c1.confidence) + COLLECT(c2.confidence) AS list"""

    get_confidence = """
MATCH (person:Person) WHERE ID(person)=$id
OPTIONAL MATCH (person) -[:EVENT]-> (event:Event) -[r:CITATION]-> (c1:Citation)
OPTIONAL MATCH (person) <-[:PARENT]- (:Family) - [:EVENT] -> (:Event) -[:CITATION]-> (c2:Citation)
RETURN ID(person) AS uniq_id, COLLECT(c1.confidence) + COLLECT(c2.confidence) AS list"""

    set_confidence = """
MATCH (person:Person) WHERE ID(person)=$id
SET person.confidence=$confidence"""

    set_sortname = """
MATCH (person:Person) WHERE ID(person) = $id
SET person.sortname=$key"""

#Replased by update_lifetime_estimate etc. / 2020-02-06
#     set_est_lifetimes = """
# MATCH (p:Person) -[r:EVENT]-> (e:Event)
#     WHERE id(p) IN $idlist
# WITH p, collect(e) AS events, 
#     max(e.date2) AS dmax, min(e.date1) AS dmin
# WHERE NOT (dmax IS NULL OR dmin IS NULL)
#     SET p.date1 = dmin, p.date2 = dmax, p.datetype = 19
# RETURN null"""
#     set_est_lifetimes_all = """
# MATCH (p:Person) -[r:EVENT]-> (e:Event)
# WITH p, collect(e) AS events, 
#     max(e.date2) AS dmax, min(e.date1) AS dmin
# WHERE NOT (dmax IS NULL OR dmin IS NULL)
#     SET p.date1 = dmin, p.date2 = dmax, p.datetype = 19
# RETURN null"""

    fetch_selected_for_lifetime_estimates = """
MATCH (p:Person) 
    WHERE id(p) IN $idlist
OPTIONAL MATCH (p)-[r:EVENT]-> (e:Event)
OPTIONAL MATCH (p) <-[:PARENT]- (fam1:Family)
OPTIONAL MATCH (fam1:Family) -[:CHILD]-> (c)
OPTIONAL MATCH (p) <-[:CHILD]- (fam2:Family) -[:PARENT]-> (parent)
OPTIONAL MATCH (fam1)-[r2:EVENT]-> (fam_event:Event)
RETURN p, id(p) as pid, 
    collect(distinct [e,r.role]) AS events,
    collect(distinct [fam_event,r2.role]) AS fam_events,
    collect(distinct [c,id(c)]) as children,
    collect(distinct [parent,id(parent)]) as parents
"""
    update_lifetime_estimate = """
MATCH (p:Person) 
    WHERE id(p) = $id
SET p.birth_low = $birth_low,
    p.death_low = $death_low,
    p.birth_high = $birth_high,
    p.death_high = $death_high
"""
    fetch_all_for_lifetime_estimates = """
MATCH (p:Person) 
OPTIONAL MATCH (p)-[r:EVENT]-> (e:Event)
OPTIONAL MATCH (p) <-[:PARENT]- (fam1:Family)
OPTIONAL MATCH (fam1:Family) -[:CHILD]-> (c)
OPTIONAL MATCH (p) <-[:CHILD]- (fam2:Family) -[:PARENT]-> (parent)
OPTIONAL MATCH (fam1)-[r2:EVENT]-> (fam_event:Event)
RETURN p, id(p) as pid, 
    collect(distinct [e,r.role]) AS events,
    collect(distinct [fam_event,r2.role]) AS fam_events,
    collect(distinct [c,id(c)]) as children,
    collect(distinct [parent,id(parent)]) as parents
"""

    get_by_uuid_w_names_notes = """
MATCH (b:Batch) -[:OWNS]-> (person:Person) -[r:NAME]-> (name:Name)
  WHERE person.uuid=$pid
OPTIONAL MATCH (person) -[:NOTE]-> (n:Note)
  WITH person, name, COLLECT (n) AS notes, b.user AS owner
  ORDER BY name.order
RETURN person, notes, COLLECT (name) AS names, owner"""

    get_w_names_notes = """
MATCH (b:Batch) -[:OWNS]-> (person:Person) -[r:NAME]-> (name:Name)
  WHERE ID(person)=$pid
OPTIONAL MATCH (person) -[:NOTE]-> (n:Note)
  WITH person, name, COLLECT (n) AS notes, b.user AS owner
  ORDER BY name.order
RETURN person, notes, COLLECT (name) AS names, owner"""
#Todo: MATCH (z:UserProfile) -[:READS|HAS_LOADED]-> (b:Batch) 
#      -[:OWNS]-> (person:Person) -[r:NAME]-> (name:Name)

    get_names = """
MATCH (n) <-[r:NAME]- (p:Person)
    where id(p) = $pid
RETURN id(p) as pid, n as name
ORDER BY name.order"""

    get_all_persons_names = """
MATCH (n)<-[r:NAME]-(p:Person)
RETURN ID(p) AS ID, n.firstname AS fn, n.prefix AS vn, n.surname AS sn, n.suffix AS pn,
    p.sex AS sex
ORDER BY n.order"""


class Cypher_name():
    """ 
        For Person Name class 
    """

    create_as_leaf = """
CREATE (n:Name) SET n = $n_attr
WITH n
MATCH (p:Person)    WHERE ID(p) = $parent_id
MERGE (p)-[r:NAME]->(n)
WITH n
match (c:Citation) where c.handle in $citation_handles
merge (n) -[r:CITATION]-> (c)"""


class Cypher_event():
    '''
    Cypher clases for creating and accessing Events
    '''

    get_w_place_note_citation = '''
match (e:Event) where ID(e)=$pid
    optional match (e) -[:PLACE]-> (p:Place)
    optional match (e) -[:CITATION]-> (c:Citation)
    optional match (e) -[:NOTE]-> (n:Note)
return e as event, 
    collect(distinct id(p)) as place_ref, 
    collect(distinct id(c)) as citation_ref, 
    collect(distinct id(n)) as note_ref'''

    get_participants_uniq_id = """
MATCH (event:Event) <-[r:EVENT]- (p:Person) 
    WHERE ID(event)=$pid
OPTIONAL MATCH (p) -[:NAME]-> (n:Name {order:0})
RETURN  r.role AS role, p AS person, n AS name
    ORDER BY role"""


class Cypher_family():
    '''
    Cypher clases for creating and accessing Families
    '''
    
    # from models.gen.family.read_families
    read_families_p = """
MATCH (f:Family) WHERE f.father_sortname>=$fw
OPTIONAL MATCH (f) -[r:PARENT]-> (pp:Person)
OPTIONAL MATCH (pp) -[:NAME]-> (np:Name {order:0}) 
OPTIONAL MATCH (f) -[:CHILD]-> (pc:Person) 
OPTIONAL MATCH (f) -[:EVENT]-> (:Event {type:"Marriage"})-[:PLACE]->(p:Place)
RETURN f, p.pname AS marriage_place,
    COLLECT([r.role, pp, np]) AS parent, 
    COLLECT(DISTINCT pc) AS child, 
    COUNT(DISTINCT pc) AS no_of_children 
    ORDER BY f.father_sortname LIMIT $limit"""

    read_my_families_p = """
MATCH (prof:UserProfile) -[:HAS_LOADED]-> (b:Batch) -[:OWNS]-> (f:Family)
    WHERE prof.username = $user AND f.father_sortname>=$fw
OPTIONAL MATCH (f) -[r:PARENT]-> (pp:Person)
OPTIONAL MATCH (pp) -[:NAME]-> (np:Name {order:0}) 
OPTIONAL MATCH (f) -[:CHILD]-> (pc:Person) 
OPTIONAL MATCH (f) -[:EVENT]-> (:Event {type:"Marriage"})-[:PLACE]->(p:Place)
RETURN f, p.pname AS marriage_place,
    COLLECT([r.role, pp, np]) AS parent, 
    COLLECT(DISTINCT pc) AS child, 
    COUNT(DISTINCT pc) AS no_of_children 
    ORDER BY f.father_sortname LIMIT $limit"""
    
    read_families_common_p = """
MATCH () -[:PASSED]-> (f:Family) WHERE f.father_sortname>=$fw
OPTIONAL MATCH (f) -[r:PARENT]-> (pp:Person)
OPTIONAL MATCH (pp) -[:NAME]-> (np:Name {order:0}) 
OPTIONAL MATCH (f) -[:CHILD]-> (pc:Person) 
OPTIONAL MATCH (f) -[:EVENT]-> (:Event {type:"Marriage"})-[:PLACE]->(p:Place)
RETURN f, p.pname AS marriage_place,
    COLLECT([r.role, pp, np]) AS parent, 
    COLLECT(DISTINCT pc) AS child, 
    COUNT(DISTINCT pc) AS no_of_children 
    ORDER BY f.father_sortname LIMIT $limit"""

    read_families_m = """
MATCH (f:Family) WHERE f.mother_sortname>=$fwm
OPTIONAL MATCH (f) -[r:PARENT]-> (pp:Person)
OPTIONAL MATCH (pp) -[:NAME]-> (np:Name {order:0}) 
OPTIONAL MATCH (f) -[:CHILD]- (pc:Person) 
OPTIONAL MATCH (f) -[:EVENT]-> (:Event {type:"Marriage"})-[:PLACE]->(p:Place)
RETURN f, p.pname AS marriage_place,
    COLLECT([r.role, pp, np]) AS parent, 
    COLLECT(DISTINCT pc) AS child, 
    COUNT(DISTINCT pc) AS no_of_children 
    ORDER BY f.mother_sortname LIMIT $limit"""
    
    read_my_families_m = """
MATCH (prof:UserProfile) -[:HAS_LOADED]-> (b:Batch) -[:OWNS]-> (f:Family)
    WHERE prof.username = $user AND f.mother_sortname>=$fwm
OPTIONAL MATCH (f) -[r:PARENT]-> (pp:Person)
OPTIONAL MATCH (pp) -[:NAME]-> (np:Name {order:0}) 
OPTIONAL MATCH (f) -[:CHILD]- (pc:Person) 
OPTIONAL MATCH (f) -[:EVENT]-> (:Event {type:"Marriage"})-[:PLACE]->(p:Place)
RETURN f, p.pname AS marriage_place,
    COLLECT([r.role, pp, np]) AS parent, 
    COLLECT(DISTINCT pc) AS child, 
    COUNT(DISTINCT pc) AS no_of_children 
    ORDER BY f.mother_sortname LIMIT $limit"""

    read_families_common_m = """
MATCH () -[:PASSED]-> (f:Family) WHERE f.mother_sortname>=$fwm
OPTIONAL MATCH (f) -[r:PARENT]-> (pp:Person)
OPTIONAL MATCH (pp) -[:NAME]-> (np:Name {order:0}) 
OPTIONAL MATCH (f) -[:CHILD]- (pc:Person) 
OPTIONAL MATCH (f) -[:EVENT]-> (:Event {type:"Marriage"})-[:PLACE]->(p:Place)
RETURN f, p.pname AS marriage_place,
    COLLECT([r.role, pp, np]) AS parent, 
    COLLECT(DISTINCT pc) AS child, 
    COUNT(DISTINCT pc) AS no_of_children 
    ORDER BY f.mother_sortname LIMIT $limit"""
    
    get_family_data = """
MATCH (f:Family) WHERE f.uuid=$pid
OPTIONAL MATCH (f) -[r:PARENT]-> (pp:Person)
    OPTIONAL MATCH (pp) -[:NAME]-> (np:Name {order:0}) 
    OPTIONAL MATCH (pp) -[:EVENT]-> (pbe:Event {type:"Birth"})
    OPTIONAL MATCH (pp) -[:EVENT]-> (pde:Event {type:"Death"})
OPTIONAL MATCH (f) -[:CHILD]- (pc:Person) 
    OPTIONAL MATCH (pc) -[:NAME]-> (nc:Name {order:0}) 
    OPTIONAL MATCH (pc) -[:EVENT]-> (cbe:Event {type:"Birth"})
    OPTIONAL MATCH (pc) -[:EVENT]-> (cde:Event {type:"Death"})
WITH f, r, pp, np, pbe, pde, pc, nc, cbe, cde ORDER BY cbe.date1
    OPTIONAL MATCH (f) -[:EVENT]-> (fe:Event) // {type:"Marriage"})-[:PLACE]->(p:Place)
        OPTIONAL MATCH (fe) -[:PLACE]-> (fep:Place)
    OPTIONAL MATCH (f) -[:CITATION]-> (fc:Citation) -[:SOURCE]-> (fs:Source)-[:REPOSITORY]-> (fre:Repository)
    OPTIONAL MATCH (fe) -[:CITATION]-> (c:Citation) -[:SOURCE]-> (s:Source)-[:REPOSITORY]-> (re:Repository)
    OPTIONAL MATCH (f) -[:NOTE]- (note:Note) 
RETURN f, 
    COLLECT(DISTINCT [fe, fep]) AS family_event,    //p.pname AS marriage_place,
    COLLECT(DISTINCT [r.role, pp, np, pbe, pde]) AS parent, 
    COLLECT(DISTINCT [pc, nc, cbe, cde]) AS child, 
    // COUNT(DISTINCT pc) AS no_of_children,
    COLLECT(DISTINCT [re, s, c]) + COLLECT(DISTINCT [fre, fs, fc]) AS sources,
    COLLECT(DISTINCT note) AS note"""
    
#     # Obsolete
#     read_families = """
# MATCH (f:Family) WHERE ID(f)>=$fw
# OPTIONAL MATCH (f)-[:FATHER]->(ph:Person)-[:NAME]->(nh:Name) 
# OPTIONAL MATCH (f)-[:MOTHER]-(pw:Person)-[:NAME]->(nw:Name) 
# OPTIONAL MATCH (f)-[:CHILD]-(pc:Person) 
# RETURN f, ph, nh, pw, nw, COLLECT(pc) AS child, COUNT(pc) AS no_of_children ORDER BY ID(f) LIMIT $limit"""

    # from models.gen.person_combo.Person_combo.get_family_members 
    get_persons_family_members = """
MATCH (p:Person) <-- (f:Family) -[r1]-> (m:Person) -[:NAME]-> (n:Name) 
    WHERE ID(p) = $pid
  OPTIONAL MATCH (m) -[:EVENT]-> (birth {type:'Birth'})
    WITH f.id AS family_id, ID(f) AS f_uniq_id, 
         TYPE(r1) AS role, r1.role AS parent_role,
         m.id AS m_id, ID(m) AS uniq_id, m.sex AS sex, 
         n, [birth.datetype, birth.date1, birth.date2] AS birth_date
    ORDER BY n.order
    RETURN family_id, f_uniq_id, role, parent_role,
           m_id, uniq_id, sex, birth_date,
           COLLECT(n) AS names
    ORDER BY family_id, role, birth_date
UNION
MATCH (p:Person) <-[r2]- (f:Family) 
    WHERE id(p) = $pid
  OPTIONAL MATCH (p) -[:EVENT]-> (birth {type:'Birth'})
    RETURN f.id AS family_id, ID(f) AS f_uniq_id, 
        TYPE(r2) AS role, r2.role AS parent_role,
        p.id AS m_id, ID(p) AS uniq_id, p.sex AS sex, 
        [birth.datetype, birth.date1, birth.date2] AS birth_date,
        [] AS names"""

    # from models.gen.family.Family_for_template.get_person_families_w_members
    # NOT IN USE
    get_members = '''
match (x) <-[r0]- (f:Family) where id(x) = $pid
with x, r0, f
match (f) -[r:CHILD|PARENT|FATHER|MOTHER]-> (p:Person)
    where id(x) <> id(p)
with x, r0, f, r, p
match (p) -[rn:NAME]-> (n:Name)
return f.id as f_id, f.rel_type as rel_type,  type(r0) as myrole,
    collect(distinct [id(p), type(r), p]) as members,
    collect(distinct [id(p), n, rn]) as names'''

    get_wedding_couple_names = """
MATCH (e:Event) <-[:EVENT]- (:Family) -[r:PARENT]-> (p:Person) -[:NAME]-> (n:Name)
    WHERE ID(e)=$eid
RETURN r.role AS frole, id(p) AS pid, COLLECT(n) AS names"""


    get_dates_parents = """
MATCH (family:Family) WHERE ID(family)=$id
OPTIONAL MATCH (family)-[:PARENT {role:"father"}]-(father:Person)
OPTIONAL MATCH (father)-[:EVENT]-(father_death:Event {type:"Death"})
OPTIONAL MATCH (family)-[:PARENT {role:"mother"}]-(mother:Person)
OPTIONAL MATCH (mother)-[:EVENT]-(mother_death:Event {type:"Death"})
OPTIONAL MATCH (family)-[:EVENT]-(event:Event) WHERE event.type="Marriage"
OPTIONAL MATCH (family)-[:EVENT]-(divorce_event:Event {type:"Divorce"})
RETURN father.sortname AS father_sortname, father_death.date1 AS father_death_date,
       mother.sortname AS mother_sortname, mother_death.date1 AS mother_death_date,
       event.date1 AS marriage_date, divorce_event.date1 AS divorce_date"""


#     set_dates_sortname = """
# MATCH (family:Family) WHERE ID(family) = $id
# SET family.datetype=$datetype
# SET family.date1=$date1
# SET family.date2=$date2
# SET family.father_sortname=$father_sortname
# SET family.mother_sortname=$mother_sortname"""
    set_dates_sortname = """
MATCH (family:Family) WHERE ID(family) = $id
SET family += $f_attr"""


class Cypher_place():
    '''
    Cypher clases for creating and accessing Places
    '''
    
    get_person_events = """
MATCH (p:Person) -[r:EVENT]-> (e:Event) -[:PLACE]-> (l:Place)
    WHERE id(l) = $locid
    MATCH (p) --> (n:Name)
WITH p, r, e, l, n ORDER BY n.order
RETURN p AS person, r.role AS role,
    COLLECT(n) AS names, e AS event
ORDER BY e.date1"""


    get_w_names_notes = """
MATCH (place:Place) -[:NAME]-> (n:Place_name)
    WHERE ID(place)=$place_id
OPTIONAL MATCH (place) -[nr:NOTE]-> (note:Note)
OPTIONAL MATCH (place) -[mr:MEDIA]-> (media:Media)
RETURN place, 
    COLLECT(DISTINCT n) AS names,
    COLLECT (DISTINCT note) AS notes,
    COLLECT (DISTINCT media) AS medias"""

    get_w_names_notes_uuid = """
MATCH (place:Place) -[:NAME]-> (n:Place_name)
    WHERE place.uuid=$uuid
OPTIONAL MATCH (place) -[nr:NOTE]-> (note:Note)
OPTIONAL MATCH (place) -[mr:MEDIA]-> (media:Media)
RETURN place, 
    COLLECT(DISTINCT n) AS names,
    COLLECT (DISTINCT note) AS notes,
    COLLECT (DISTINCT media) AS medias"""

    place_get_one = """
match (p:Place) where ID(p)=$pid
optional match (p) -[:NAME]-> (n:Place_name)
return p, collect(n) as names"""

    place_get_all = """
MATCH (p:Place) 
RETURN p ORDER BY p.pname"""


class Cypher_refname():
    '''
    Cypher clases for creating and accessing Refnames
    '''

    @staticmethod
    # With relation to base Refname
    def save_link(link_type):
        # link (a) -[:BASENAME|PARENTNAME]-> (b)
        # Calling Refname: (self) --> (self.refname)
        if not link_type in ("BASENAME", "PARENTNAME"):
            raise ValueError("Invalid link type {}".format(link_type))
        return """
MERGE (a:Refname {name: $a_name}) SET a = $a_attr
MERGE (b:Refname {name: $b_name})
MERGE (a )-[l:""" + link_type + """ {use:$use}]-> (b)
RETURN ID(a) AS aid, a.name AS aname, l.use AS use, ID(b) AS bid, b.name AS bname"""

    # Without relation to another Refname
    save_single = """
MERGE (a:Refname {name: $a_name}) SET a = $a_attr
RETURN ID(a) AS aid, a.name AS aname"""

    link_person_to = """
MATCH (p:Person) WHERE ID(p) = $pid
MERGE (a:Refname {name:$name})
MERGE (a) -[:REFNAME {use:$use}]-> (p)
RETURN ID(a) as rid"""

    # Get all Refnames. Returns a list of Refname objects, with referenced names,
    # reftypes and count of usages
    get_all = """
MATCH (n:Refname)
OPTIONAL MATCH (n) -[r]-> (m:Refname)
OPTIONAL MATCH (n) -[l:REFNAME]-> (p:Person)
RETURN n,
    COLLECT(DISTINCT [type(r), r.use, m]) AS r_ref,
    COLLECT(DISTINCT l.use) AS l_uses, COUNT(p) AS uses
ORDER BY n.name"""

    delete_all = "MATCH (n:Refname) DETACH DELETE n"

    set_constraint = "CREATE CONSTRAINT ON (r:Refname) ASSERT r.name IS UNIQUE"


class Cypher_citation():
    '''
    Cypher clases for creating and accessing Citations
    '''
    get_persons_citation_paths = """
match path = (p) -[*]-> (c:Citation) -[:SOURCE]-> (s:Source)
    where id(p) = $pid 
    with relationships(path) as rel, c, id(s) as source_id
return extract(x IN rel | endnode(x))  as end, source_id
    order by source_id, size(end)"""

    _cita_sour_repo_tail = """
RETURN ID(c) AS id, c.dateval AS date, c.page AS page, c.confidence AS confidence, 
   note.text AS notetext, note.url as url,
   COLLECT(DISTINCT [ID(source), source.stitle, source.sauthor, source.spubinfo, 
                     rr.medium, 
                     ID(repo), repo.rname, repo.type]) AS sources"""

    get_cita_sour_repo_all = """
MATCH (c:Citation) -[rs:SOURCE]-> (source:Source) -[rr:REPOSITORY]-> (repo:Repository)
OPTIONAL MATCH (c) -[n:NOTE]-> (note:Note)
  WITH c, rs, source, rr, repo, note 
  ORDER BY c.page, note.text""" + _cita_sour_repo_tail

    get_cita_sour_repo = """
MATCH (c:Citation) -[rs:SOURCE]-> (source:Source) -[rr:REPOSITORY]-> (repo:Repository)
    WHERE ID(c)=$uid
OPTIONAL MATCH (c) -[n:NOTE]-> (note:Note)
  WITH c, rs, source, rr, repo, note 
  ORDER BY c.page, note.text""" + _cita_sour_repo_tail


class Cypher_source():
    '''
    Cypher class for creating and accessing Sources
    '''
    get_sources_repositories = """
MATCH (c:Citation) -[:SOURCE]-> (s:Source)
    WHERE ID(c) IN $uid_list
    OPTIONAL MATCH (s) -[rel:REPOSITORY]-> (r:Repository)
RETURN LABELS(c)[0] AS label, ID(c) AS uniq_id, s, rel, r"""

#v0.4: pe.Source_cypher.SourceCypher.get_auditted_set
#     get_sources_w_notes = """
# MATCH (s:Source)
# WITH s ORDER BY toUpper(s.stitle)
#     OPTIONAL MATCH (s) -[:NOTE]-> (note)
#     OPTIONAL MATCH (s) -[r:REPOSITORY]-> (rep:Repository)
#     OPTIONAL MATCH (c:Citation) -[:SOURCE]-> (s)
#     OPTIONAL MATCH (c) <-[:CITATION]- (citator)
# RETURN ID(s) AS uniq_id, s as source, collect(DISTINCT note) as notes, 
#        collect(DISTINCT [r.medium, rep]) as repositories,
#        COUNT(c) AS cit_cnt, COUNT(citator) AS ref_cnt 
# ORDER BY toUpper(s.stitle)"""
#
#v0.4: pe.Source_cypher.SourceCypher.get_auditted_selection_set
#     get_selected_sources_w_notes = """
# MATCH (s:Source)
#         WHERE s.stitle CONTAINS $key1 OR s.stitle CONTAINS $key2 
# WITH s ORDER BY toUpper(s.stitle)
#     OPTIONAL MATCH (s) -[:NOTE]-> (note)
#     OPTIONAL MATCH (s) -[r:REPOSITORY]-> (rep:Repository)
#     OPTIONAL MATCH (c:Citation) -[:SOURCE]-> (s)
#     OPTIONAL MATCH (c) <-[:CITATION]- (citator)
# RETURN ID(s) AS uniq_id, s as source, collect(DISTINCT note) as notes, 
#        collect(DISTINCT [r.medium, rep]) as repositories,
#        COUNT(c) AS cit_cnt, COUNT(citator) AS ref_cnt 
# ORDER BY toUpper(s.stitle)"""
# 
#v0.4: pe.Source_cypher.SourceCypher.get_an_auditted_selection_set
    get_a_source_w_notes = """
MATCH (source:Source) WHERE ID(source)=$sid
    OPTIONAL MATCH (source) -[r:REPOSITORY]-> (rep:Repository)
    OPTIONAL MATCH (source) -[:NOTE]-> (n)
RETURN source, COLLECT(n) AS notes, COLLECT([r.medium,rep]) AS reps"""

    get_citators_of_source = """
match (s) <-[:SOURCE]- (c:Citation) where id(s)=$sid 
match (c) <-[:CITATION]- (x)
    optional match (c) -[:NOTE]-> (n:Note)
    optional match (s) -[:REPOSITORY]-> (r:Repository)
    optional match (x) <-[re:EVENT|NAME|MEDIA]- (p)
return id(c) as c_id, c, collect(n) as notes, re.role as role,
       labels(x)[0] as label, x, 
       coalesce(p.uuid, x.uuid) as p_uuid, 
       coalesce(p, x) as p, 
       coalesce(ID(p), ID(x)) as p_uid, labels(p)[0] as p_label, r
order by c_id, p_uuid"""


class Cypher_repository():
    '''
    Cypher clases for creating and accessing Repositories
    '''
    _get_all = "match (r:Repository) <-[rr:REPOSITORY]- (s:Source)"
    _get_one = _get_all + " where id(repository)=$rid"
    _get_tail = """
    with r, rr, s 
    order by s.stitle
    optional match (r) -[:NOTE]-> (w:Note)
return id(r) AS uniq_id, 
    r.rname AS rname,
    r.type AS type, 
    r.change as change,
    r.handle as handle,
    r.id as id,
    collect(distinct [id(s), s.stitle, s.sauthor, s.spubinfo, rr.medium]) AS sources,
    collect(distinct w) as notes
order by r.rname"""

    get_w_sources_all = _get_all + _get_tail 
    get_w_sources =  _get_one + _get_tail

    get_w_notes = """
match (repo:Repository) where ID(repo) = $rid
    optional match (repo) -[:NOTE]-> (w:Note)
return repo, collect(w) as notes"""

    get_one = """
match (r:Repository) where ID(r) = $rid
return r"""

    get_all = """
match (r:Repository)
return r order by r.type"""


class Cypher_media():

#     get_by_uniq_id = """
# MATCH (obj:Media)
#     WHERE ID(obj) = $rid
# RETURN obj"""

    get_by_uuid = """
MATCH (obj:Media) <-[r:MEDIA] - (n) 
    WHERE obj.uuid = $rid
RETURN obj, COLLECT([n, properties(r)]) as ref"""

    get_all = "MATCH (o:Media) RETURN o"

    # Media list by description with count limit
    read_common_media = """
MATCH (prof) -[:PASSED]-> (o:Media) <- [r:MEDIA] - () 
WHERE o.description >= $start_name 
RETURN o, prof.user as credit, prof.id as batch_id, COUNT(r) AS count
    ORDER BY o.description LIMIT $limit"""

    read_my_own_media = """
MATCH (prof) -[:OWNS]-> (o:Media) <- [r:MEDIA] - () 
WHERE  prof.user = $user AND o.description >= $start_name
RETURN o, prof.user as credit, prof.id as batch_id, COUNT(r) AS count
    ORDER BY o.description LIMIT $limit"""


class Cypher_batch():
    # Read information of user Batches and data connected to them

    get_filename = """
MATCH (b:Batch {id: $batch_id, user: $username}) 
RETURN b.file"""

    list_all = """
MATCH (b:Batch) 
RETURN b """

    get_batches = '''
match (b:Batch) 
    where b.user = $user and b.status = "completed"
optional match (b) -[:OWNS]-> (x)
return b as batch,
    labels(x)[0] as label, count(x) as cnt 
    order by batch.user, batch.id'''

    get_passed = '''
match (b:Audit) 
    where b.user = $user
optional match (b) -[:PASSED]-> (x)
return b as batch, count(x) as cnt 
    order by batch.id'''

    get_single_batch = '''
match (up:UserProfile) -[r:HAS_LOADED]-> (b:Batch {id:$batch}) 
optional match (b) -[:OWNS]-> (x)
return up as profile, b as batch, labels(x)[0] as label, count(x) as cnt'''

    get_user_batch_names = '''
match (b:Batch) where b.user = $user
optional match (b) -[r:OWNS]-> (:Person)
return b.id as batch, b.timestamp as timestamp, b.status as status,
    count(r) as persons 
    order by batch'''

    get_empty_batches = '''
MATCH (a:Batch) 
WHERE NOT ((a)-[:OWNS]->()) AND NOT a.id CONTAINS "2019-10"
RETURN a AS batch ORDER BY a.id DESC'''

    # Batch removal
    delete = """
MATCH (u:UserProfile{username:$username}) -[:HAS_LOADED]-> (b:Batch{id:$batch_id}) 
OPTIONAL MATCH (b) -[*]-> (n) 
DETACH DELETE b, n"""


class Cypher_audit():
    ' Query Audit materials '

    get_my_audits = '''
match (b:Audit {auditor: $oper})
optional match (b) -[:PASSED]-> (x)
return b, labels(x)[0] as label, count(x) as cnt 
    order by b.user, b.id, label'''

    get_all_audits = '''
match (b:Audit)
optional match (b) -[:PASSED]-> (x)
return b, labels(x)[0] as label, count(x) as cnt 
    order by b.user, b.id, label'''

#     get_single_audit = '''
# match (b:Audit {id:$batch}) 
# optional match (b) -[:PASSED]-> (x)
# return labels(x)[0] as label, count(x) as cnt'''
# 
#     get_my_audit_names = '''
# match (b:Audit) where b.auditor = $oper
# optional match (b) -[r:PASSED]-> (:Person)
# return b.id as audition, b.timestamp as timestamp, 
#     b.auditor as auditor, b.status as status,
#     count(r) as persons 
# order by audition'''
