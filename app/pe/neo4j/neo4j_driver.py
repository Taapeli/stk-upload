from models.gen.person_combo import Person_combo
from models.gen.cypher import Cypher_person
from models.gen.person_name import Name
from models.gen.event_combo import Event_combo


class Neo4jDriver:
    ''' Methods for accessing Neo4j database.
    '''
    def __init__(self, driver):
        self.driver = driver
    
    def person_list(self, user, fw_from, limit):
        """ Read Person data from given fw_from 
        """
        # Select a) filter by user b) show Isotammi common data (too)
        try:
            with self.driver.session() as session:
                if user is None: 
                    #3 == #1 read approved common data
                    print("_read_person_list: approved common only")
                    result = session.run(Cypher_person.read_approved_persons_with_events_starting_name,
                                         start_name=fw_from, limit=limit)
                else: 
                    #2 get my own (no owner name needed)
                    print("_read_person_list: by owner only")
                    result = session.run(Cypher_person.read_my_persons_with_events_starting_name,
                                         user=user, start_name=fw_from, limit=limit)
                # Returns person, names, events
        except Exception as e:
            print('Error _read_person_list: {} {}'.format(e.__class__.__name__, e))            
            raise      

        persons = []
        for record in result:
            ''' <Record 
                    person=<Node id=163281 labels={'Person'} 
                      properties={'sortname': 'Ahonius##Knut Hjalmar',  
                        'sex': '1', 'confidence': '', 'change': 1540719036, 
                        'handle': '_e04abcd5677326e0e132c9c8ad8', 'id': 'I1543', 
                        'priv': 1,'datetype': 19, 'date2': 1910808, 'date1': 1910808}> 
                    names=[<Node id=163282 labels={'Name'} 
                      properties={'firstname': 'Knut Hjalmar', 'type': 'Birth Name', 
                        'suffix': '', 'surname': 'Ahonius', 'order': 0}>] 
                    events=[[
                        <Node id=169494 labels={'Event'} 
                            properties={'datetype': 0, 'change': 1540587380, 
                            'description': '', 'handle': '_e04abcd46811349c7b18f6321ed', 
                            'id': 'E5126', 'date2': 1910808, 'type': 'Birth', 'date1': 1910808}>,
                         None
                         ]] 
                    owners=['jpek']>
            '''
            node = record['person']
            # The same person is not created again
            p = Person_combo.from_node(node)
            #if show_with_common and p.too_new: continue

#             if take_refnames and record['refnames']:
#                 refnlist = sorted(record['refnames'])
#                 p.refnames = ", ".join(refnlist)
            for nnode in record['names']:
                pname = Name.from_node(nnode)
                p.names.append(pname)
    
            # Create a list with the mentioned user name, if present
            if user:
                p.owners = record.get('owners',[user])
                                                                                                                                
            # Events
    
            for enode, pname, role in record['events']:
                if enode != None:
                    e = Event_combo.from_node(enode)
                    e.place = pname or ""
                    if role and role != "Primary":
                        e.role = role
                    p.events.append(e)

            persons.append(p)   

        return persons


class Personresult:
    ''' Person's result object.
    '''
    def __init__(self, persons):
        self.error = 0  
        self.num_hidden = 10  
        self.persons = persons  


class DBreader:
    ''' Public methods for accessing active database.
    
        
    '''
    def __init__(self, dbdriver, my_context):
        ''' Create a reader object with db driver and user context.
        '''
        self.dbdriver = dbdriver
        self.user_context = my_context  
        self.username = my_context.user
    
    def person_list(self):
        ''' List person data including all data needed to Person page.
        
            Calls Neo4jDriver.person_list(user, fw_from, limit)
        '''
        context = self.user_context
        fw = context.next_name_fw()
        if context.context == context.ChoicesOfView.COMMON:
            use_user = context.user
        else:
            use_user=None
        persons = self.dbdriver.person_list(use_user, fw, context.count)

        # Update the page scope according to items really found 
        if persons:
            context.update_session_scope('person_scope', 
                                          persons[0].sortname, persons[-1].sortname, 
                                          context.count, len(persons))
 
        #Todo: remove this later
        if 'next_person' in context.session: # Remove an obsolete field
            context.session.pop('next_person')
            context.session.modified = True

        personresult = Personresult(persons)
        #Todo:Calculate hidden persons
        personresult.num_hidden = 0
        return personresult

