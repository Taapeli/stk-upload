# Cypher clauses for models.gen module
# 12.2.2018 / JMä

class Cypher():

# --- For Event class ---------------------------------------------------------

# --- For Family class --------------------------------------------------------

# --- For Media class ---------------------------------------------------------

# --- For Note class ----------------------------------------------------------

# --- For Person class --------------------------------------------------------

    _person_get_events_tail = """
 OPTIONAL MATCH (person)-[:EVENT]->(event:Event)
 OPTIONAL MATCH (event)-[:EVENT]->(place:Place)
 OPTIONAL MATCH (person) <-[:BASENAME*1..3]- (refn:Refname)
RETURN ID(person) AS id, person.confidence AS confidence, 
    person.est_birth AS est_birth, person.est_death AS est_death,
    name.firstname AS firstname, name.surname AS surname,
    name.suffix AS suffix, 
    COLLECT(DISTINCT refn.name) AS refnames,
    COLLECT(DISTINCT [ID(event), event.type, event.date, event.datetype, 
        event.daterange_start, event.daterange_stop, place.pname]) AS events
ORDER BY name.surname, name.firstname"""

    person_get_events_all = "MATCH (person:Person)-[:NAME]->(name:Name)" + _person_get_events_tail

    # With attr={'use':rule, 'name':name}
    person_get_events_by_refname = """
MATCH p = (search:Refname) -[:BASENAME*{use:$attr.use}]-> (person:Person)
WHERE search.name STARTS WITH $attr.name
WITH search, person
MATCH (person) -[:NAME]-> (name:Name)
WITH person, name""" + _person_get_events_tail

    person_get_confidence = """
 MATCH (person:Person)
 OPTIONAL MATCH (person) -[:EVENT]-> (event:Event) -[r:CITATION]-> (c:Citation)
 RETURN ID(person) AS uniq_id, COLLECT(c.confidence) AS list"""

    person_set_confidence = """
 MATCH (person:Person) WHERE ID(person)=$id
 SET person.confidence='$confidence'"""
                

# --- For Place class ---------------------------------------------------------
        
    places_get = """
 MATCH (p:Place)
 RETURN ID(p) AS uniq_id, p
 ORDER BY p.pname, p.type"""

    place_data_by_id = """
MATCH (place:Place)-[:NAME]->(n:Place_name)
    WHERE ID(place)=$place_id
OPTIONAL MATCH (place)-[wu:WEBURL]->(url:Weburl)
OPTIONAL MATCH (place)-[nr:NOTE]->(note:Note)
RETURN place, COLLECT([n.name, n.lang]) AS names, 
    COLLECT (DISTINCT url) AS urls, COLLECT (DISTINCT note) AS notes"""

    places_get_names = """
MATCH (a:Place) -[:NAME]-> (pn:Place_name) 
OPTIONAL MATCH (a:Place) -[:HIERARCY]-> (up:Place) -[:NAME]-> (upn:Place_name)
OPTIONAL MATCH (a:Place) <-[:HIERARCY]- (do:Place) -[:NAME]-> (don:Place_name)
RETURN ID(a) AS id, a.type AS type,
    COLLECT(DISTINCT [pn.name,pn.lang]) AS name,
    a.coord_long AS coord_long, a.coord_lat AS coord_lat, 
    COLLECT(DISTINCT [ID(up), up.type, upn.name, upn.lang]) AS upper, 
    COLLECT(DISTINCT [ID(do), do.type, don.name, don.lang]) AS lower
ORDER BY name[0][0]
"""

    # Query for Place hierarcy
    place_hier_by_id = """
MATCH x= (p:Place)<-[r:HIERARCY*]-(i:Place) WHERE ID(p) = $locid
    RETURN NODES(x) AS nodes, SIZE(r) AS lv, r
    UNION
MATCH x= (p:Place)-[r:HIERARCY*]->(i:Place) WHERE ID(p) = $locid
    RETURN NODES(x) AS nodes, SIZE(r)*-1 AS lv, r
"""
    # Query for single Place without hierarcy
    place_root_by_id = """
MATCH (p:Place) WHERE ID(p) = $locid
RETURN p.type AS type, p.pname AS name
"""
    # Query to get names for a Place
    place_name_by_id="""
MATCH (l:Place)-->(n:Place_name) WHERE ID(l) = $locid 
RETURN COLLECT([n.name, n.lang]) AS names LIMIT 15
"""

    place_get_events = """
MATCH (p:Person)-[r:EVENT]->(e:Event)-[:PLACE]->(l:Place)
  WHERE id(l) = {locid}
MATCH (p) --> (n:Name)
RETURN id(p) AS uid, r.role AS role,
  COLLECT([n.type, n.firstname, n.surname, n.suffix]) AS names,
  e.type AS etype,
  e.date AS edate,
  e.datetype AS edatetype,
  e.daterange_start AS edaterange_start,
  e.daterange_stop AS edaterange_stop
ORDER BY edate"""

    place_count = "MATCH (p:Place) RETURN COUNT(p)"

    place_save = """
CREATE (p:Place) 
SET p.gramps_handle=$handle, 
    p.change=$change, 
    p.id=$id, 
    p.type=$type, 
    p.pname=$pname, 
    p.coord_long=$coord_long, 
    p.coord_lat=$coord_lat"""             

    place_save_name_by_handle = """
MATCH (p:Place) WHERE p.gramps_handle=$handle 
CREATE (n:Place_name)
MERGE (p)-[r:NAME]->(n)
SET n.name=$name,
    n.lang=$lang,
    n.datetype=$datetype,
    n.daterange_start=$daterange_start,
    n.daterange_stop=$daterange_stop"""             

    place_save_weburl_by_handle = """
MATCH (n:Place) WHERE n.gramps_handle=$handle
CREATE (n)-[wu:WEBURL]->
      (url:Weburl {priv: {url_priv}, href: {url_href},
                type: {url_type}, description: {url_description}})"""

    place_save_hier_by_handle = """
MATCH (n:Place) WHERE n.gramps_handle=$handle
MATCH (m:Place) WHERE m.gramps_handle=$hlink
MERGE (n)-[r:HIERARCY]->(m) """

    place_save_note_by_handle = """
MATCH (n:Place) WHERE n.gramps_handle=$handle
MATCH (m:Note) WHERE m.gramps_handle=$hlink
MERGE (n)-[r:NOTE]->(m)"""


# --- For Refname class -------------------------------------------------------

    @staticmethod
    # With relation to base Refname
    def refname_save_link(link_type):
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
    refname_save_single = """
MERGE (a:Refname {name: $a_name}) SET a = $a_attr
RETURN ID(a) AS aid, a.name AS aname"""

    refname_link_person_to = """
MATCH (p:Person) WHERE ID(p) = $pid
MERGE (a:Refname {name:$name})
MERGE (a) -[:BASENAME {use:$use}]-> (p)
RETURN ID(a) as rid"""

    # Get all Refnames. Returns a list of Refname objects, with referenced names,
    # reftypes and count of usages
    refnames_get = """
MATCH (n:Refname)
OPTIONAL MATCH (n) -[r]-> (m:Refname)
OPTIONAL MATCH (n) -[l:BASENAME]-> (p:Person)
RETURN n,
    COLLECT(DISTINCT [type(r), r.use, m]) AS r_ref,
    COLLECT(DISTINCT l.use) AS l_uses, COUNT(p) AS uses
ORDER BY n.name"""

    refnames_delete_all = "MATCH (n:Refname) DETACH DELETE n"
    
    refnames_set_constraint = "CREATE CONSTRAINT ON (r:Refname) ASSERT r.name IS UNIQUE"

# --- For Source and Citation classes -----------------------------------------

# --- For User class ----------------------------------------------------------

