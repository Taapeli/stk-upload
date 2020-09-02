'''
Reading and updating Neo4j database

See also: gramps.cypher_gramps for updates from Gramps xml file

Created on 2.9.2020

@author: JMä
'''

class CypherEvent(object):

    get_an_event_common = '''
MATCH (root:Audit) -[r:PASSED]-> (e:Event {uuid:$uuid}) 
RETURN e, type(r) AS root_type, root'''
    get_an_event_own = '''
MATCH (root:Batch {user:$user}) -[r:OWNS]-> (e:Event {uuid:$uuid}) 
RETURN e, type(r) AS root_type, root'''

    # Get Event with referring Persons and Families
    get_event_w_participants = """
MATCH (event:Event) <-[r:EVENT]- (p) 
    WHERE ID(event) = $uid
OPTIONAL MATCH (p) -[:NAME]-> (n:Name {order:0})
RETURN  r.role AS role, p, n AS name
    ORDER BY role"""
    