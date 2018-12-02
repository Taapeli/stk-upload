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
    _get_events_tail = """
 OPTIONAL MATCH (person) -[r:EVENT]-> (event:Event)
 OPTIONAL MATCH (event) -[:PLACE]-> (place:Place)
 OPTIONAL MATCH (person) <-[:BASENAME*1..3]- (refn:Refname)
RETURN person, COLLECT(DISTINCT name) as names,
    COLLECT(DISTINCT refn.name) AS refnames,
    COLLECT(DISTINCT [r.role, event, place.pname]) AS events"""
#  2.12.2018 20.47 (14:48)
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

    get_w_names_notes = """
MATCH (person:Person) -[r:NAME]-> (name:Name)
  WHERE ID(person)=$pid
OPTIONAL MATCH (person) -[:NOTE]-> (n:Note)
  WITH person, name, COLLECT (n) AS notes ORDER BY name.order
RETURN person, notes, COLLECT (name) AS names"""

    get_names = """
MATCH (n) <-[r:NAME]- (p:Person)
    where id(p) = $pid
RETURN id(p) as pid, n as name
ORDER BY name.order"""

    get_all_persons_names = """
MATCH (n)<-[r:NAME]-(p:Person)
RETURN ID(p) AS ID, n.firstname AS fn, n.surname AS sn, n.suffix AS pn,
    p.gender AS sex
ORDER BY n.order"""


class Cypher_name():
    """ 
        For Person Name class 
    """

    create_as_leaf = """
CREATE (n:Name) SET n = $n_attr
WITH n
MATCH (p:Person)    WHERE ID(p) = $parent_id
MERGE (p)-[r:NAME]->(n)"""


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

    # from models.gen.person_combo.Person_combo.get_family_members 
    get_persons_family_members = """
MATCH (p:Person) <-- (f:Family) -[r1]-> (m:Person) -[:NAME]-> (n:Name) 
    WHERE ID(p) = $pid
  OPTIONAL MATCH (m) -[:EVENT]-> (birth {type:'Birth'})
    WITH f.id AS family_id, ID(f) AS f_uniq_id, 
         TYPE(r1) AS role,
         m.id AS m_id, ID(m) AS uniq_id, m.gender AS gender, 
         n, [birth.datetype, birth.date1, birth.date2] AS birth_date
    ORDER BY n.order
    RETURN family_id, f_uniq_id, role, 
           m_id, uniq_id, gender, birth_date,
           COLLECT(n) AS names
    ORDER BY family_id, role, birth_date
UNION
MATCH (p:Person) <-[r2]- (f:Family) 
    WHERE id(p) = $pid
  OPTIONAL MATCH (p) -[:EVENT]-> (birth {type:'Birth'})
    RETURN f.id AS family_id, ID(f) AS f_uniq_id, TYPE(r2) AS role, 
           p.id AS m_id, ID(p) AS uniq_id, p.gender AS gender, 
           [birth.datetype, birth.date1, birth.date2] AS birth_date,
           [] AS names"""

    # from models.gen.family.Family_for_template.get_person_families_w_members
    # NOT IN USE
    get_members = '''
match (x) <-[r0]- (f:Family) where id(x) = $pid
with x, r0, f
match (f) -[r:FATHER|MOTHER|CHILD]-> (p:Person)
    where id(x) <> id(p)
with x, r0, f, r, p
match (p) -[rn:NAME]-> (n:Name)
return f.id as f_id, f.rel_type as rel_type,  type(r0) as myrole,
    collect(distinct [id(p), type(r), p]) as members,
    collect(distinct [id(p), n, rn]) as names'''

    get_wedding_couple_names = """
match (e:Event) <-- (:Family) -[r:FATHER|MOTHER]-> (p:Person) -[:NAME]-> (n:Name)
    where ID(e)=$eid
return type(r) as frole, id(p) as pid, collect(n) as names"""


class Cypher_place():
    '''
    Cypher clases for creating and accessing Places
    '''

    get_person_events = """
MATCH (p:Person) -[r:EVENT]-> (e:Event) -[:PLACE]-> (l:Place)
  WHERE id(l) = $locid
MATCH (p) --> (n:Name)
RETURN id(p) AS uid, r.role AS role,
  COLLECT([n.type, n.firstname, n.surname, n.suffix]) AS names,
  e.type AS etype, [e.datetype, e.date1, e.date2] AS edates
ORDER BY edates[1]"""

    get_name_hierarcy = """
MATCH (a:Place) -[:NAME]-> (pn:Place_name)
OPTIONAL MATCH (a:Place) -[:HIERARCY]-> (up:Place) -[:NAME]-> (upn:Place_name)
OPTIONAL MATCH (a:Place) <-[:HIERARCY]- (do:Place) -[:NAME]-> (don:Place_name)
RETURN ID(a) AS id, a.type AS type,
    COLLECT(DISTINCT [pn.name, pn.lang]) AS name, a.coord AS coord,
    COLLECT(DISTINCT [ID(up), up.type, upn.name, upn.lang]) AS upper,
    COLLECT(DISTINCT [ID(do), do.type, don.name, don.lang]) AS lower
ORDER BY name[0][0]"""

    get_w_names_notes = """
MATCH (place:Place) -[:NAME]-> (n:Place_name)
    WHERE ID(place)=$place_id
OPTIONAL MATCH (place) -[nr:NOTE]-> (note:Note)
RETURN place, 
    COLLECT(DISTINCT [n.name, n.lang]) AS names,
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
   note.text AS notetext,
   COLLECT(DISTINCT [ID(source), source.stitle, 
                     rr.medium, 
                     ID(repo), repo.rname, repo.type]) AS sources"""

    get_cita_sour_repo_all = """
MATCH (c:Citation) -[rs:SOURCE]-> (source:Source) -[rr:REPOSITORY]-> (repo:Repository)
OPTIONAL MATCH (c) -[n:NOTE]-> (note:Note)
  WITH c, rs, source, rr, repo 
  ORDER BY c.page, note""" + _cita_sour_repo_tail

    get_cita_sour_repo = """
MATCH (c:Citation) -[rs:SOURCE]-> (source:Source) -[rr:REPOSITORY]-> (repo:Repository)
    WHERE ID(c)=$uid
OPTIONAL MATCH (c) -[n:NOTE]-> (note:Note)
  WITH c, rs, source, rr, repo 
  ORDER BY c.page, note""" + _cita_sour_repo_tail


class Cypher_source():
    '''
    Cypher clases for creating and accessing Sources
    '''
    source_list = """
MATCH (s:Source)
OPTIONAL MATCH (s)<-[:SOURCE]-(c:Citation)
OPTIONAL MATCH (c)<-[:CITATION]-(e)
OPTIONAL MATCH (s)-[r:REPOSITORY]->(a:Repository)
RETURN ID(s) AS uniq_id, s.id AS id, s.stitle AS stitle, 
       a.rname AS repository, r.medium AS medium,
       COUNT(c) AS cit_cnt, COUNT(e) AS ref_cnt 
ORDER BY toUpper(stitle)
"""

    get_citators_of_source = """
match (s) <-[:SOURCE]- (c:Citation) where id(s)=$sid 
with c
    match (c) <-[:CITATION]- (x)
    optional match (x) <-[re:EVENT]- (p)
    return id(c) as c_id, c, re.role as role,
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
    collect(distinct [id(s), s.stitle, rr.medium]) AS sources,
    collect(w) as notes
order by r.rname"""

    get_w_sources_all = _get_all + _get_tail 
    get_w_sources =  _get_one + _get_tail

    get_w_notes = """
match (repo:Repository) where ID(repo) = $rid
    optional match (repo) -[:NOTE]-> (w:Note)
return repo, collect(w) as notes"""

    get_one = """
match (r:Repository) where ID(r) == $rid
return r"""

    get_all = """
match (r:Repository)
return r order by r.type"""

# class Cypher_weburl():
#     '''
#     Cypher clases for creating and accessing Weburls
#     '''
#     link_to_weburl = """
# merge (w:Weburl {href: $href})
# with w
#     match (x) where ID(x) = $parent_id
#     with w, x
#         merge (x) -[r:WEBREF]-> (w)
#             set r.type = $type
#             set r.desc = $desc
#             set r.priv = $priv
# return id(r) as ref_id, id(w) as weburl_id"""
#     link_to_weburl_X = """
# match (x) where ID(x) = $parent_id
#     optional match (w:Weburl) where w.href = $href
# with x, w
#     merge (x) -[r:WEBREF]-> (w)
#         set w.href = $href
#         set r.type = $type
#         set r.desc = $desc
#         set r.priv = $priv
# return id(r) as ref_id, id(w) as weburl_id"""

