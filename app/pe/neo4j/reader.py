'''
Created on 17.3.2020

@author: jm
'''

from bl.place import PlaceBl, PlaceName, Point
from .place_cypher import CypherPlace

#Todo: Change Old style includes to bl classes
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
        # Select a) filter by user or b) show Isotammi common data (too)
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
            print('Error pe.neo4j.reader.Neo4jDriver.person_list: {} {}'.format(e.__class__.__name__, e))            
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


    def place_list(self, user, fw_from, limit):
        ''' Read place list from given start point
        '''
        #fw = self.context.next_name_fw()
        with self.driver.session() as session: 
            if user == None: 
                #1 get approved common data
                print("pe.neo4j.reader.Neo4jDriver.place_list: by owner with common")
                result = session.run(CypherPlace.get_common_name_hierarchies,
                                     user=user, fw=fw_from, 
                                     limit=limit)
            else: 
                #2 get my own (no owner name needed)
                print("pe.neo4j.reader.Neo4jDriver.place_list: by owner only")
                result = session.run(CypherPlace.get_my_name_hierarchies,
                                     user=user, fw=fw_from, 
                                     limit=limit)

        ret =[]
        for record in result:
            # Luodaan paikka ja siihen taulukko liittyvistä hierarkiassa lähinnä
            # alemmista paikoista
            #
            # Record: <Record id=290228 type='Borough' 
            #    names=[<Node id=290235 labels={'Place_name'} 
            #        properties={'name': '1. Kaupunginosa', 'lang': ''}>] 
            #    coord=None
            #    upper=[
            #        [287443, 'City', 'Arctopolis', 'la'], 
            #        [287443, 'City', 'Björneborg', 'sv'], 
            #        [287443, 'City', 'Pori', ''], 
            #        [287443, 'City', 'Пори', 'ru']] 
            #    lower=[[290226, 'Tontti', 'Tontti 23', '']]
            # >
            pl_id =record['id']
            p = PlaceBl(pl_id)
            p.uuid =record['uuid']
            p.type = record.get('type')
            if record['coord']:
                p.coord = Point(record['coord']).coord
            # Set place names and default display name pname
            for nnode in record.get('names'):
                pn = PlaceName.from_node(nnode)
#                 if pn.lang in ['fi', '']:
#                     # Default language name
#                     #TODO use language from current_user's preferences
#                     p.pname = pn.name
                p.names.append(pn)
            if len(p.names) > 1:
                p.names.sort()
            if p.pname == '' and p.names:
                p.pname = p.names[0].name
            p.uppers = PlaceBl._combine_places(record['upper'])
            p.lowers = PlaceBl._combine_places(record['lower'])
            ret.append(p)

        # Return sorted by first name in the list p.pname
        return sorted(ret, key=lambda x:x.names[0].name if x.names else "")

