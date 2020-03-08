from models.gen.person_combo import Person_combo
from models.gen.cypher import Cypher_person
from models.gen.person_name import Name
from models.gen.event_combo import Event_combo
class Neo4jDBdriver:

    
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

        # Update the page scope according to items really found 
#         if persons:
#             o_filter.update_session_scope('person_scope', 
#                                           persons[0].sortname, persons[-1].sortname, 
#                                           limit, len(persons))
# 
#         #Todo: remove this later
#         if 'next_person' in o_filter.session: # Unused field
#             o_filter.session.pop('next_person')
#             o_filter.session.modified = True

        return (persons)



class Personresult:
    def __init__(self, persons):
        self.error = 0  
        self.num_hidden = 10  
        self.persons = persons  

class DBreader:
    
    def __init__(self, dbdriver, my_filter, privacylimit):
        self.dbdriver = dbdriver
        self.my_filter = my_filter  
        self.username = my_filter.user
    
    def person_list(self, limit, start, include):
        persons = self.dbdriver.person_list(self.username, self.my_filter.next_name_fw(), limit=limit)
        personresult = Personresult(persons)
        return personresult
    
    
    
    



