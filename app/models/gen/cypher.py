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

# class Cypher_note():
#     '''
#     Cypher clases for creating and accessing Notes
#     '''

class Cypher_person():
    '''
    Cypher clases for creating and accessing Places
    '''

    _get_events_tail = """
 OPTIONAL MATCH (person) -[:EVENT]-> (event:Event)
 OPTIONAL MATCH (event) -[:EVENT]-> (place:Place)
 OPTIONAL MATCH (person) <-[:BASENAME*1..3]- (refn:Refname)
RETURN ID(person) AS id, person.confidence AS confidence,
    person.est_birth AS est_birth, person.est_death AS est_death,
    name.firstname AS firstname, name.surname AS surname,
    name.suffix AS suffix,
    COLLECT(DISTINCT refn.name) AS refnames,
    COLLECT(DISTINCT [ID(event), event.type,
        event.datetype, event.date1, event.date2, place.pname]) AS events"""
    _get_events_surname = """, TOUPPER(LEFT(name.surname,1)) as initial 
    ORDER BY TOUPPER(name.surname), name.firstname"""
    _get_events_firstname = """, LEFT(name.firstname,1) as initial 
    ORDER BY TOUPPER(name.firstname), name.surname, name.suffix"""
    _get_events_patronyme = """, LEFT(name.suffix,1) as initial 
    ORDER BY TOUPPER(name.suffix), name.surname, name.firstname"""
#     COLLECT(DISTINCT [ID(event), event.type, event.date, event.datetype,
#         event.daterange_start, event.daterange_stop, place.pname]) AS events

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
MATCH (r:Refname {name:$name}) -[:BASENAME*1..3]-> (person:Person) --> (name:Name) 
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

    get_names = """
MATCH (n)<-[r:NAME]-(p:Person)
where id(p) = $pid
RETURN ID(p) AS ID, n.firstname AS fn, n.surname AS sn, n.suffix AS pn,
    p.gender AS sex"""

    get_all_persons_names = """
MATCH (n)<-[r:NAME]-(p:Person)
RETURN ID(p) AS ID, n.firstname AS fn, n.surname AS sn, n.suffix AS pn,
    p.gender AS sex"""


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

# --- For Source and Citation classes -----------------------------------------

# class Cypher_citation():
#     '''
#     Cypher clases for creating and accessing Citations
#     '''
# class Cypher_source():
#     '''
#     Cypher clases for creating and accessing Sources
#     '''

class Cypher_repository():
    '''
    Cypher clases for creating and accessing Repositories
    '''
    _get_all = "match (r:Repository) <-[rr:REPOSITORY]- (s:Source)"
    _get_one = _get_all + " where id(repository)=$rid"
    _get_tail = """
    with r, rr, s 
    order by s.stitle
    optional match (r) -[wr:WEBREF]-> (w:Weburl)
return id(r) AS uniq_id, 
    r.rname AS rname,
    r.type AS type, 
    r.change as change,
    r.handle as handle,
    r.id as id,
    collect(distinct [id(s), s.stitle, rr.medium]) AS sources,
    collect([w.href, wr.type, wr.description, wr.priv]) as webref
order by r.rname"""

    get_w_sources_all = _get_all + _get_tail 
    get_w_sources =  _get_one + _get_tail

    get_w_urls = """
match (repo:Repository) where ID(repo) = $rid
    optional match (repo) -[wr:WEBURL]-> (w:Weburl)
return repo, collect([w.href, wr.type, wr.description, wr.priv]) as webref"""

    get_one = """
match (r:Repository) where ID(r) == $rid
return ID(n) AS uniq_id, r"""

    get_all = """
match (r:Repository)
return ID(n) AS uniq_id, r order by r.type"""

class Cypher_weburl():
    '''
    Cypher clases for creating and accessing Weburls
    '''
    link_to_weburl = """
merge (w:Weburl {href: $href})
with w
    match (x) where ID(x) = $parent_id
    with w, x
        merge (x) -[r:WEBREF]-> (w)
            set r.type = $type
            set r.desc = $desc
            set r.priv = $priv
return id(r) as ref_id, id(w) as weburl_id"""
    link_to_weburl_X = """
match (x) where ID(x) = $parent_id
    optional match (w:Weburl) where w.href = $href
with x, w
    merge (x) -[r:WEBREF]-> (w)
        set w.href = $href
        set r.type = $type
        set r.desc = $desc
        set r.priv = $priv
return id(r) as ref_id, id(w) as weburl_id"""

# --- For User class ----------------------------------------------------------
