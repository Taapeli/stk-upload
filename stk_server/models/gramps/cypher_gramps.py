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

# --- For Source and Citation classes -----------------------------------------


