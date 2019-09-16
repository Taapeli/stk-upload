# Cypher clauses for models.gen module
#
# Reading and updating Neo4j database
#
# See also: gramps.cypher_gramps for updates from Gramps xml file
#
# 12.2.2018 / JMä

# class Cypher_event():
#     '''
#     Cypher clases for creating and accessing Events
#     '''

# class Cypher_family():
#     '''
#     Cypher clases for creating and accessing Family objects
#     '''

# class Cypher_media():
#     '''
#     Cypher clases for creating and accessing Media objects
#     '''

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
    all_nodes_query_w_apoc="""
MATCH (p:Person {uuid:$uuid})
CALL apoc.path.subgraphAll(p, {maxLevel:4, 
        relationshipFilter: 'EVENT>|NAME>|PLACE>|CITATION>|SOURCE>|REPOSITORY>|NOTE>|MEDIA|HIERARCHY>|<CHILD|<PARENT'}) 
    YIELD nodes, relationships
RETURN extract(x IN relationships | 
        [id(startnode(x)), type(x), properties(x), id(endnode(x))]) as relations,
        extract(x in nodes | x) as nodelist"""
    #TODO Obsolete
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

#     xxxx_all_persons_with_events_from_name = """
# MATCH (b:Batch) -[:BATCH_MEMBER]-> (p:Person)
#     WHERE p.sortname >= $start_name
# WITH p, b.user as user ORDER BY p.sortname LIMIT $limit
#   MATCH (p:Person) -[:NAME]-> (n:Name)
#   WITH p, n ORDER BY p.sortname, n.order, user
#     OPTIONAL MATCH (p) -[rn:EVENT]-> (e:Event)
#     OPTIONAL MATCH (e) -[rpl:PLACE]-> (pl:Place)
# RETURN p as person, 
#     collect(distinct n) as names, 
#     collect(distinct [e, pl.pname, rn.role]) as events,
#     user
# ORDER BY p.sortname"""



    read_persons_list_by_refn = """
MATCH p = (search:Refname) -[:BASENAME*1..3 {use:'surname'}]-> (person:Person)
WHERE search.name STARTS WITH 'Kottu'
WITH search, person
MATCH (person) -[:NAME]-> (name:Name)
OPTIONAL MATCH (person) <-[:BASENAME*1..3]- (refn:Refname)
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
    _get_events_tail = """
 OPTIONAL MATCH (person) -[r:EVENT]-> (event:Event)
 OPTIONAL MATCH (event) -[:PLACE]-> (place:Place)
 OPTIONAL MATCH (person) <-[:BASENAME*1..3]- (refn:Refname)
RETURN person, COLLECT(DISTINCT name) as names,
    COLLECT(DISTINCT refn.name) AS refnames,
    COLLECT(DISTINCT [r.role, event, place.pname]) AS events"""
    _get_events_surname = """, TOUPPER(LEFT(name.surname,1)) as initial 
    ORDER BY TOUPPER(names[0].surname), names[0].firstname"""
    _get_events_firstname = """, LEFT(name.firstname,1) as initial 
    ORDER BY TOUPPER(names[0].firstname), names[0].surname, names[0].suffix"""
    _get_events_patronyme = """, LEFT(name.suffix,1) as initial 
    ORDER BY TOUPPER(names[0].suffix), names[0].surname, names[0].firstname"""

    get_events_all = "MATCH (person:Person) -[:NAME]-> (name:Name)" \
        + _get_events_tail + _get_events_surname

    get_events_all_firstname = "MATCH (person:Person) -[:NAME]-> (name:Name)" \
        + _get_events_tail + _get_events_firstname

    get_events_all_patronyme = "MATCH (person:Person) -[:NAME]-> (name:Name)" \
        + _get_events_tail + _get_events_patronyme

    get_events_uniq_id = """
MATCH (person:Person) -[:NAME]-> (name:Name)
WHERE ID(person) = $id""" + _get_events_tail

    get_events_by_refname = """
MATCH (refn:Refname {name:$name}) -[:BASENAME*1..3]-> (person:Person) --> (name:Name) 
""" + _get_events_tail + _get_events_surname

    # With attr={'use':rule, 'name':name}
    get_events_by_refname_use = """
MATCH p = (search:Refname) -[:BASENAME*1..3 {use:$attr.use}]-> (person:Person)
WHERE search.name STARTS WITH $attr.name
WITH search, person
MATCH (person) -[:NAME]-> (name:Name)
WITH person, name""" + _get_events_tail + _get_events_surname

    get_confidences_all = """
MATCH (person:Person)
OPTIONAL MATCH (person) -[:EVENT]-> (event:Event) -[r:CITATION]-> (c:Citation)
RETURN ID(person) AS uniq_id, COLLECT(c.confidence) AS list"""

    get_confidence = """
MATCH (person:Person) WHERE ID(person)=$id
OPTIONAL MATCH (person) -[:EVENT]-> (event:Event) -[r:CITATION]-> (c:Citation)
RETURN ID(person) AS uniq_id, COLLECT(c.confidence) AS list"""

    set_confidence = """
MATCH (person:Person) WHERE ID(person)=$id
SET person.confidence=$confidence"""

    set_sortname = """
MATCH (person:Person) WHERE ID(person) = $id
SET person.sortname=$key"""

    set_est_lifetimes = """
MATCH (p:Person) -[r:EVENT]-> (e:Event)
    WHERE id(p) IN $idlist
WITH p, collect(e) AS events, 
    max(e.date2) AS dmax, min(e.date1) AS dmin
WHERE NOT (dmax IS NULL OR dmin IS NULL)
    SET p.date1 = dmin, p.date2 = dmax, p.datetype = 19
RETURN null"""

    set_est_lifetimes_all = """
MATCH (p:Person) -[r:EVENT]-> (e:Event)
WITH p, collect(e) AS events, 
    max(e.date2) AS dmax, min(e.date1) AS dmin
WHERE NOT (dmax IS NULL OR dmin IS NULL)
    SET p.date1 = dmin, p.date2 = dmax, p.datetype = 19
RETURN null"""

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
    
    get_family_data = """
MATCH (f:Family) WHERE ID(f)=$pid
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
match (e:Event) <-- (:Family) -[r:PARENT|FATHER|MOTHER]-> (p:Person) -[:NAME]-> (n:Name)
    where ID(e)=$eid
return type(r) as frole, id(p) as pid, collect(n) as names"""


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
RETURN id(p) AS uid, r.role AS role,
  COLLECT(n) AS names,
  e.type AS etype, [e.datetype, e.date1, e.date2] AS edates
ORDER BY edates[1]"""

    get_name_hierarchies = """
MATCH (a:Place) -[:NAME]-> (pn:Place_name)
OPTIONAL MATCH (a:Place) -[:IS_INSIDE]-> (up:Place) -[:NAME]-> (upn:Place_name)
OPTIONAL MATCH (a:Place) <-[:IS_INSIDE]- (do:Place) -[:NAME]-> (don:Place_name)
RETURN ID(a) AS id, a.type AS type,
    COLLECT(DISTINCT pn) AS names, a.coord AS coord,
    COLLECT(DISTINCT [ID(up), up.type, upn.name, upn.lang]) AS upper,
    COLLECT(DISTINCT [ID(do), do.type, don.name, don.lang]) AS lower
ORDER BY names[0].name"""

    get_w_names_notes = """
MATCH (place:Place) -[:NAME]-> (n:Place_name)
    WHERE ID(place)=$place_id
OPTIONAL MATCH (place) -[nr:NOTE]-> (note:Note)
RETURN place, 
    COLLECT(DISTINCT n) AS names,
    COLLECT (DISTINCT note) AS notes"""

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
MERGE (a) -[:BASENAME {use:$use}]-> (p)
RETURN ID(a) as rid"""

    # Get all Refnames. Returns a list of Refname objects, with referenced names,
    # reftypes and count of usages
    get_all = """
MATCH (n:Refname)
OPTIONAL MATCH (n) -[r]-> (m:Refname)
OPTIONAL MATCH (n) -[l:BASENAME]-> (p:Person)
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
#     source_list = """
# MATCH (s:Source)
#     OPTIONAL MATCH (s) <-[:SOURCE]- (c:Citation)
#     OPTIONAL MATCH (c) <-[:NOTE]- (note)
#     OPTIONAL MATCH (c) <-[:CITATION]- (cit)
#     OPTIONAL MATCH (s) -[r:REPOSITORY]-> (rep:Repository)
# RETURN ID(s) AS uniq_id, s as source, collect(DISTINCT note) as notes, 
#        rep.rname AS repository, r.medium AS medium,
#        COUNT(c) AS cit_cnt, COUNT(cit) AS ref_cnt 
# ORDER BY toUpper(s.stitle)
# """

    get_sources_w_notes = """
MATCH (s:Source)
    OPTIONAL MATCH (s) -[:NOTE]-> (note)
    OPTIONAL MATCH (s) -[r:REPOSITORY]-> (rep:Repository)
    OPTIONAL MATCH (c:Citation) -[:SOURCE]-> (s)
    OPTIONAL MATCH (c) <-[:CITATION]- (citator)
RETURN ID(s) AS uniq_id, s as source, collect(DISTINCT note) as notes, 
       collect(DISTINCT [r.medium, rep]) as repositories,
       COUNT(c) AS cit_cnt, COUNT(citator) AS ref_cnt 
ORDER BY toUpper(s.stitle)"""

    get_a_source_w_notes = """
MATCH (source:Source) WHERE ID(source)=$sid
OPTIONAL MATCH (source) -[:NOTE]-> (n)
RETURN source, COLLECT(n) as notes"""
#     get_repositories_w_notes = """
# MATCH (source:Source) -[r:REPOSITORY]-> (repo:Repository)
#     WHERE ID(source) = $sid
# OPTIONAL MATCH (repo) -[:NOTE]-> (note:Note)
# RETURN r.medium AS medium, repo, COLLECT(note) AS notes"""


    get_citators_of_source = """
match (s) <-[:SOURCE]- (c:Citation) where id(s)=$sid 
with c
    match (c) <-[:CITATION]- (x)
    optional match (c) -[:NOTE]-> (n:Note)
    optional match (x) <-[re:EVENT]- (p)
    return id(c) as c_id, c, collect(n) as notes, re.role as role,
           id(x) as x_id, labels(x)[0] as label, x, 
           coalesce(id(p), id(x))  as p_id
    order by c_id, p_id"""


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

    get_by_uuid = """
MATCH (obj:Media)
    WHERE Iobj.uuid = $rid
RETURN obj"""

    get_by_uniq_id = """
MATCH (obj:Media)
    WHERE ID(obj) = $rid
RETURN obj"""

