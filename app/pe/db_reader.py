'''
Created on 17.3.2020

@author: jm
'''
from bl.base import Status
#import traceback
from models.gen.person_combo import Person_combo

class DBreader:
    ''' Public methods for accessing active database.
    
        Returns a PersonResult object
    '''
    def __init__(self, dbdriver, u_context):
        ''' Create a reader object with db driver and user context.
        '''
        self.dbdriver = dbdriver
        self.user_context = u_context  
        self.username = u_context.user
        if u_context.context == u_context.ChoicesOfView.COMMON:
            self.use_user = None
        else:
            self.use_user = u_context.user
   
    def get_person_list(self):
        ''' List person data including all data needed to Person page.
        
            Calls Neo4jDriver.dr_get_person_list(user, fw_from, limit)
        '''
        context = self.user_context
        fw = context.next_name_fw()
        persons = self.dbdriver.dr_get_person_list(self.use_user, fw, context.count)

        # Update the page scope according to items really found 
        if persons:
            context.update_session_scope('person_scope', 
                                          persons[0].sortname, persons[-1].sortname, 
                                          context.count, len(persons))

        #Todo: remove this after next main version
        if 'next_person' in context.session: # Remove an obsolete field
            context.session.pop('next_person')
            context.session.modified = True

        if self.use_user is None:
            persons2 = [p for p in persons if not p.too_new]
            num_hidden = len(persons) - len(persons2)
        else:
            persons2 = persons
            num_hidden = 0
        person_result = PersonResult(persons2, num_hidden)
        return person_result


#     def get_place_list(self): # --> bl.place.PlaceReader.get_list()
#         """ Get a list on PlaceBl objects with nearest heirarchy neighbours.

#     def get_place_with_events(self, uuid): # --> bl.place.PlaceReader.get_with_events()
#         """ Read the place hierarchy and events connected to this place.

#     def get_source_list(self): # -> bl.source.SourceReader.get_source_list()


    def get_source_with_references(self, uuid, u_context):
        """ Read the source, repository and events etc referencing this source.
        
            Returns a dictionary, where items = SourceDb object.
            - item.notes[]      Notes connected to Source
            - item.repositories Repositories for Source
            - item.citations    Citating Persons, Events, Families and Medias
                                as [label, object] tuples(?)
                                
        """
        source = self.dbdriver.dr_get_source_w_repository(self.use_user, uuid)
        results = {'item':source, 'status':Status.OK}
        if not source:
            results = {'status':Status.NOT_FOUND, 'statustext':f"Source with uuid={uuid}"}
            return results
        
        citations, notes, targets = self.dbdriver.dr_get_source_citations(source.uniq_id)

        citations = []
        for c_id, c in citations.items():
            if c_id in notes:
                c.notes = notes[c_id]
            for target in targets[c_id]:
                if u_context.privacy_ok(target):
                    # Insert person name and life events
                    if isinstance(target, Person_combo):
                        self.dbdriver.dr_inlay_person_lifedata(target)
                    c.citators.append(target)
                else:
                    print(f'DBreader.get_source_with_references: hide {target}')

            citations.append(c)
        results['citations':citations]

        return results


# ------------------------------ Result sets ----------------------------------

class BaseResult:
    ''' Result objects common operations
    '''
    def __init__(self, items=[], num_hidden=0):
        self.error = 0  
        self.num_hidden = num_hidden
        self.items = items


class PersonResult(BaseResult):
    ''' Person's result object.
    '''
    def __init__(self, items=[], num_hidden=0):
        BaseResult.__init__(self, items, num_hidden)
#         self.error = 0  
#         self.num_hidden = num_hidden
#         self.items = items  

