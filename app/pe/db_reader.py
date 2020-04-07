'''
Created on 17.3.2020

@author: jm
'''
import traceback

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


    def get_place_list(self):
        """ Get a list on PlaceBl objects with nearest heirarchy neighbours.
        
            Haetaan paikkaluettelo ml. hierarkiassa ylemmät ja alemmat
"""

        context = self.user_context
        fw = context.next_name_fw()
        places = self.dbdriver.dr_get_place_list_fw(self.use_user, fw, context.count, 
                                                 lang=context.lang)

        # Update the page scope according to items really found 
        if places:
            context.update_session_scope('place_scope', 
                                          places[0].pname, places[-1].pname, 
                                          context.count, len(places))
        place_result = PlaceResult(places)
        return place_result


    def get_place_with_events(self, uuid):
        """ Read the place hierarchy and events connected to this place.
        
            Luetaan aneettuun paikkaan liittyvä hierarkia ja tapahtumat
            Palauttaa paikkahierarkian ja (henkilö)tapahtumat.
    
        """
        place = self.dbdriver.dr_get_place_w_na_no_me(self.use_user, uuid, 
                                                      self.user_context.lang)
        place_result = PlaceResult(place)
        if not place:
            place_result.error = f"DBreader.get_place_with_events: {self.use_user} - no Place with uuid={uuid}"
            return place_result
        try:
            place_result.hierarchy = \
                self.dbdriver.dr_get_place_tree(place.uniq_id, lang=self.user_context.lang)

        except AttributeError as e:
            traceback.print_exc()
            place_result.error = f"Place tree for {place.uniq_id}: {e}"
            return place_result
        except ValueError as e:
            place_result.error = f"Place tree for {place.uniq_id}: {e}"
            traceback.print_exc()
                
        place_result.events = self.dbdriver.dr_get_place_events(place.uniq_id)
        return place_result



class PlaceResult:
    ''' Place's result object.
    '''
    def __init__(self, items=[]):
        self.error = 0  
        self.num_hidden = 0
        self.items = items
        self.hierarchy = []    # Hirearchy tree
        self.events = []       # Events for selected place

class PersonResult:
    ''' Person's result object.
    '''
    def __init__(self, items, num_hidden):
        self.error = 0  
        self.num_hidden = num_hidden
        self.items = items  

