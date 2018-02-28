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
    COLLECT(DISTINCT [ID(event), event.type, event.date, event.dates,
                      place.pname]) AS events
ORDER BY name.surname, name.firstname"""
#     COLLECT(DISTINCT [ID(event), event.type, event.date, event.datetype, 
#         event.daterange_start, event.daterange_stop, place.pname]) AS events

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
 SET person.confidence=$confidence"""
                

# --- For Place class ---------------------------------------------------------

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

