'''
Cypher clauses for models.gramps module

Created on 21.3.2018

@author: jm
'''

class Cypher_w_handle(object):
    '''
    Cypher clauses for reading and updating database by data from Gramps xml file

    Here the nodes are mostly identified by gramp_handle to recognize the
    original items from the user's Gramps database
    '''

# --- For Event class ---------------------------------------------------------

    event_save = """
MATCH (u:UserProfile) WHERE u.userName=$username
MERGE (e:Event {gramps_handle: $e_attr.gramps_handle})
    SET e = $e_attr
MERGE (u) -[r:REVISION {date: $date}]-> (e)
"""

    event_link_place = """
MATCH (n:Event) WHERE n.gramps_handle=$handle
MATCH (m:Place) WHERE m.gramps_handle=$place_hlink
MERGE (n)-[r:PLACE]->(m)"""

    event_link_note = """
MATCH (e:Event) WHERE e.gramps_handle=$handle
MATCH (n:Note)  WHERE n.gramps_handle=$noteref_hlink
MERGE (e)-[r:NOTE]->(n)"""

    event_link_citation = """
MATCH (n:Event)    WHERE n.gramps_handle=$handle
MATCH (m:Citation) WHERE m.gramps_handle=$citationref_hlink
MERGE (n)-[r:CITATION]->(m)"""

    event_link_media = """
MATCH (n:Event) WHERE n.gramps_handle=$handle
MATCH (m:Media) WHERE m.gramps_handle=$objref_hlink
MERGE (n)-[r:Media]->(m)"""


# --- For Family class --------------------------------------------------------

# --- For Media class ---------------------------------------------------------

# --- For Note class ----------------------------------------------------------

# --- For Person class --------------------------------------------------------

# --- For Place class ---------------------------------------------------------

    place_create = """
CREATE (p:Place)
SET p = $p_attr"""

    place_add_name = """
MATCH (p:Place) WHERE p.gramps_handle=$handle
CREATE (n:Place_name)
MERGE (p) -[r:NAME]-> (n)
SET n = $n_attr"""

    place_link_weburl = """
MATCH (n:Place) WHERE n.gramps_handle=$handle
CREATE (n) -[wu:WEBURL]-> (url:Weburl
                {priv: {url_priv}, href: {url_href},
                 type: {url_type}, description: {url_description}})"""

    place_link_hier = """
MATCH (n:Place) WHERE n.gramps_handle=$handle
MATCH (m:Place) WHERE m.gramps_handle=$hlink
MERGE (n) -[r:HIERARCY]-> (m)
SET r = $r_attr"""

    place_link_note = """
MATCH (n:Place) WHERE n.gramps_handle=$handle
MATCH (m:Note) WHERE m.gramps_handle=$hlink
MERGE (n) -[r:NOTE]-> (m)"""



# --- For Source and Citation classes -----------------------------------------


