'''
Created on 24.9.2018

@author: jm
'''
from models.datareader import read_persons_with_events
from models.gen.family import Family_for_template
from models.gen.source import Source
from models.gen.citation import Citation


def get_person_for_display(keys, user):
    """ Get one Person with connected Events, Families etc

        @TODO Monet osat on ohjelmoimatta
    """
    # Get Person objects, whith included Events and Names (Refnames no needed!)
    persons = read_persons_with_events(keys, user=user)
    person = persons[0]
    person.families = Family_for_template.get_person_families_w_members(person.uniq_id)
    person.set_my_places(True)
    person.citations, source_ids = Citation.get_persons_citations(person.uniq_id)
    sources = Source.get_sources_by_idlist(source_ids)
    #TODO: Etsi sitaateille lähteet

#     person.get_all_notes()
#     person.get_media()
#     person.get_refnames()
    for c in person.citations:
        print ("Sitaatit {} {}".format(c.uniq_id, c))
        for ci in c.citators:
            print (" <- {}".format(ci))
#     for e in person.events:
#         print("Person event {}: {}".format(e.uniq_id, e))
#         if e.place == None:
#             print("- no place")
#         else:
#             for n in e.place.names:
#                 print("- place {} name {}: {}".format(e.place.uniq_id, n.uniq_id, n))

    return person, sources
    