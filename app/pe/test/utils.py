from pprint import pprint

# this Cypher query will find suitable objects from the database that can be used for testing 
# Run it once and save the gramps_ids for different objects and use them in the next query.
cypher0 = """
match (root:Root)
    --> (f:Family)-[:PARENT]-> (p:Person)
    --> (e:Event)
    --> (pl:Place)
match (f) -[:CHILD]-> (child:Person)
match (p) --> (m:Media)    
match (p) --> (n:Note)    
match (e) --> (c:Citation) --> (s:Source) --> (repo:Repository)    
return * limit 1
"""

# This Cypher query will find the objects used by the test functions. 
# Assumes that the Gramps example family tree (example.gramps) has been loaded to the Neo4j database (at least once).
cypher = """
match (root:Root)
    --> (f:Family{id:'F0017'})  -[:PARENT]-> (p:Person{id:'I0044'})
    --> (e:Event{id:'E1656'})
    --> (pl:Place{id:'P1435'})
match (f) -[:CHILD]-> (child:Person{id:'I0624'})
match (p) --> (m:Media{id:'O0010'})    
match (p) --> (n:Note{id:'N0001'})    
match (e) --> (c:Citation{id:'C0000'}) 
    --> (s:Source{id:'S0000'}) 
    --> (repo:Repository{id:'R0000'})    
return * limit 1
"""

class Values: pass
values = Values()

def get_test_values(driver):
    rec = driver.session().run(cypher).single()
    values.user = rec['root']['user']
    values.batch_id = rec['root']['id']

    values.person_gramps_id = rec['p']['id']
    values.person_uuid = rec['p']['uuid']
    values.person_uniq_id = rec['p'].id

    values.child_gramps_id = rec['child']['id']

    values.family_gramps_id = rec['f']['id']
    values.family_uuid = rec['f']['uuid']
    values.family_uniq_id = rec['f'].id

    values.place_gramps_id = rec['pl']['id']
    values.place_uuid = rec['pl']['uuid']
    values.place_uniq_id = rec['pl'].id

    values.event_gramps_id = rec['e']['id']
    values.event_uuid = rec['e']['uuid']
    values.event_uniq_id = rec['e'].id

    values.citation_gramps_id = rec['c']['id']
    values.citation_uuid = rec['c']['uuid']
    values.citation_uniq_id = rec['c'].id

    values.source_gramps_id = rec['s']['id']
    values.source_uuid = rec['s']['uuid']
    values.source_uniq_id = rec['s'].id

    values.repo_gramps_id = rec['repo']['id']
    values.repo_uuid = rec['repo']['uuid']
    values.repo_uniq_id = rec['repo'].id

    values.note_gramps_id = rec['n']['id']
    values.note_uuid = rec['n']['uuid']
    values.note_uniq_id = rec['n'].id

    values.media_gramps_id = rec['m']['id']
    values.media_uuid = rec['m']['uuid']
    values.media_uniq_id = rec['m'].id

    pprint(values.__dict__)
    return values

# {'batch_id': '2021-12-20.014',
#  'child_gramps_id': 'I0624',
#  'citation_gramps_id': 'C0000',
#  'citation_uniq_id': 89705,
#  'citation_uuid': 'e29119adb567431fa85d5b874f12fdbd',
#  'event_gramps_id': 'E1656',
#  'event_uniq_id': 96958,
#  'event_uuid': 'b9cb5c77956b4b96b22e5df3f60d901a',
#  'family_gramps_id': 'F0017',
#  'family_uniq_id': 103383,
#  'family_uuid': 'b4a142f60d87478ebacf7bc435414bcc',
#  'media_gramps_id': 'O0010',
#  'media_uniq_id': 92650,
#  'media_uuid': '9440d9a8ce0545c7beb78e97b6debe62',
#  'note_gramps_id': 'N0001',
#  'note_uniq_id': 89677,
#  'note_uuid': 'f033005a2b6143438fb4685fe543b067',
#  'person_gramps_id': 'I0044',
#  'person_uniq_id': 100778,
#  'person_uuid': '349afe85e8ff42dc89d8082aee27ccbd',
#  'place_gramps_id': 'P1435',
#  'place_uniq_id': 94175,
#  'place_uuid': '6e671a0ad39e469ea6b4400ff9218dfe',
#  'repo_gramps_id': 'R0000',
#  'repo_uniq_id': 89699,
#  'repo_uuid': '8251edb4038340ef8cd2f12fb9157589',
#  'source_gramps_id': 'S0000',
#  'source_uniq_id': 89703,
#  'source_uuid': '7ce6114d643847d2ab93b7c666436ac7',
#  'user': 'kku'}

