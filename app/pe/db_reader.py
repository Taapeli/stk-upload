'''

    VANHENTUNUT TOTEUTUSMALLI
    
    Toiminnot pitäisi siirtää pe.neo4j.readservice.Neo4jReadService -luokkaan
    
Created on 17.3.2020

@author: jm
'''
from bl.base import Status
#import traceback
#from models.gen.person_combo import Person_combo

class DbReader:
    ''' Public methods for accessing active database.
    
        Returns a PersonResult object
    '''
    def __init__(self, readservice, u_context=None):
        ''' Create a reader object with db driver and user context.

            - readservice    Neo4jReadService or Neo4jWriteDriver
        '''
        self.readservice = readservice
        if u_context:
            # For reader only; writer has no context?
            self.user_context = u_context
            self.username = u_context.user
            if u_context.context == u_context.ChoicesOfView.COMMON:
                self.use_user = None
            else:
                self.use_user = u_context.user
   
#     def get_person_list(self): # --> bl.person.PersonReader.get_person_list()
#         ''' List person data including all data needed to Person page. '''

#     def get_place_list(self): # --> bl.place.PlaceReader.get_place_list()
#         """ Get a list on PlaceBl objects with nearest heirarchy neighbours.

#     def get_place_with_events(self, uuid): # --> bl.place.PlaceReader.get_with_events()
#         """ Read the place hierarchy and events connected to this place.

#     def get_source_list(self): # -> bl.source.SourceDataStore.get_source_list()


    def get_source_with_references(self, uuid, u_context):
        """ Read the source, repository and events etc referencing this source.
        
            Returns a dictionary, where items = SourceDb object.
            - item.notes[]      Notes connected to Source
            - item.repositories Repositories for Source
            - item.citations    Citating Persons, Events, Families and Medias
                                as [label, object] tuples(?)
                                
        """
        from bl.person import Person

        source = self.readservice.dr_get_source_w_repository(self.use_user, uuid)
        results = {'item':source, 'status':Status.OK}
        if not source:
            results = {'status':Status.NOT_FOUND, 'statustext':f"Source with uuid={uuid}"}
            return results
        
        _citations, notes, targets = self.readservice.dr_get_source_citations(source.uniq_id)

        citations = []
        for c_id, c in citations.items():
            if c_id in notes:
                c.notes = notes[c_id]
            for target in targets[c_id]:
                if u_context.privacy_ok(target):
                    # Insert person name and life events
                    if isinstance(target, Person):
                        self.readservice.dr_inlay_person_lifedata(target)
                    c.citators.append(target)
                else:
                    print(f'DbReader.get_source_with_references: hide {target}')

            citations.append(c)
        results['citations':citations]

        return results
