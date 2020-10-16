'''
Created on 16.10.2020

@author: jm
'''

class CypherPerson():
    '''
    Cypher clauses for Person data access.
    '''

    get_person = """
MATCH (root) -[r:OWNS|PASSED]-> (p:Person {uuid:$uuid}) 
RETURN p, type(r) AS root_type, root"""

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

    read_approved_persons_w_events_fw_name = """
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

    read_my_persons_w_events_fw_name = """
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

    get_objs_places = """
MATCH (x) -[:PLACE]-> (pl:Place)
    WHERE ID(x) IN $uid_list
OPTIONAL MATCH (pl) -[:NAME]-> (pn:Place_name)
OPTIONAL MATCH (pl) -[ri:IS_INSIDE]-> (pi:Place)
OPTIONAL MATCH (pi) -[:NAME]-> (pin:Place_name)
RETURN LABELS(x)[0] AS label, ID(x) AS uniq_id, 
    pl, COLLECT(DISTINCT pn) AS pnames,
    pi, COLLECT(DISTINCT pin) AS pinames"""

    get_objs_citation_note_media = """
MATCH (x) -[r:CITATION|NOTE|MEDIA]-> (y)
    WHERE ID(x) IN $uid_list
RETURN LABELS(x)[0] AS label, ID(x) AS uniq_id, r, y"""

