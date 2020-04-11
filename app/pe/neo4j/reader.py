'''
Created on 17.3.2020

@author: jm
'''
import logging
logger = logging.getLogger('stkserver')

from bl.place import PlaceBl, PlaceName
from bl.place_coordinates import Point
from .place_cypher import CypherPlace

#Todo: Change Old style includes to bl classes
from models.gen.person_combo import Person_combo
from models.gen.cypher import Cypher_person
from models.gen.person_name import Name
from models.gen.event_combo import Event_combo
from models.gen.note import Note
from models.gen.media import Media
from models.dbtree import DbTree
from models.gen.dates import DateRange


class Neo4jDriver:
    ''' Methods for accessing Neo4j database.
    '''
    def __init__(self, driver):
        self.driver = driver
    
    def dr_get_person_list(self, user, fw_from, limit):
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
            print('Error pe.neo4j.reader.Neo4jDriver.dr_get_person_list: {} {}'.format(e.__class__.__name__, e))            
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


    def dr_get_place_list_fw(self, user, fw_from, limit, lang='fi'):
        ''' Read place list from given start point
        '''
        ret = []
        with self.driver.session() as session: 
            if user == None: 
                #1 get approved common data
                print("pe.neo4j.reader.Neo4jDriver.dr_get_place_list_fw: from common")
                result = session.run(CypherPlace.get_common_name_hierarchies,
                                     fw=fw_from, limit=limit, lang=lang)
            else: 
                #2 get my own
                print("pe.neo4j.reader.Neo4jDriver.dr_get_place_list_fw: by owner")
                result = session.run(CypherPlace.get_my_name_hierarchies,
                                     user=user, fw=fw_from, limit=limit, lang=lang)
        for record in result:
            # <Record 
            #    place=<Node id=514341 labels={'Place'}
            #        properties={'coord': [61.49, 23.76], 
            #            'id': 'P0300', 'type': 'City', 'uuid': '8fbe632144584d30aa75701b49f15484', 
            #            'pname': 'Tampere', 'change': 1585409704}>
            #    name=<Node id=514342 labels={'Place_name'}
            #        properties={'name': 'Tampere', 'lang': ''}> 
            #    names=[<Node id=514344 labels={'Place_name'}
            #            properties={'name': 'Tampereen kaupunki', 'lang': ''}>, 
            #        <Node id=514343 ...>]
            #    uses=4
            #    upper=[[514289, 'b16a6ee2c7a24e399d45554faa8fb094', 'Country', 'Finnland', 'de'],
            #        [514289, 'b16a6ee2c7a24e399d45554faa8fb094', 'Country', 'Finland', 'sv'],
            #        [514289, 'b16a6ee2c7a24e399d45554faa8fb094', 'Country', 'Suomi', '']
            #    ]
            #    lower=[[None, None, None, None, None]]>
            node = record["place"]
            p = PlaceBl.from_node(node)
            p.ref_cnt = record['uses']

            # Set place names and default display name pname
            node = record['name']    
            p.names.append(PlaceName.from_node(node))
            oth_names = []
            for node in record['names']:
                oth_names.append(PlaceName.from_node(node))
            # Arrage names by local language first 
            lst = PlaceName.arrange_names(oth_names)

            p.names += lst
            p.pname = p.names[0].name
            p.uppers = PlaceBl.combine_places(record['upper'], lang)
            p.lowers = PlaceBl.combine_places(record['lower'], lang)
            ret.append(p)

        # Return sorted by first name in the list p.names -> p.pname
        return sorted(ret, key=lambda x:x.pname)


    def dr_get_place_w_na_no_me(self, user, uuid, lang='fi'): 
        """ Returns the PlaceBl with Notes and PlaceNames included.
        """
        pl = None
        with self.driver.session() as session:
            if user == None: 
                result = session.run(CypherPlace.get_common_w_names_notes,
                                     uuid=uuid, lang=lang)
            else:
                result = session.run(CypherPlace.get_my_w_names_notes,
                                     user=user, uuid=uuid, lang=lang)
            for record in result:
                # <Record 
                #    place=<Node id=514286 labels={'Place'} 
                #        properties={'coord': [60.45138888888889, 22.266666666666666], 
                #            'id': 'P0007', 'type': 'City', 'uuid': '494a748a2730417ca02ccaa11685e21a', 
                #            'pname': 'Turku', 'change': 1585409704}> 
                #    name=<Node id=514288 labels={'Place_name'}
                #        properties={'name': 'Åbo', 'lang': 'sv'}>
                #    names=[<Node id=514287 labels={'Place_name'} 
                #                properties={'name': 'Turku', 'lang': ''}>] 
                #    notes=[] 
                #    medias=[]
                # >

                node = record["place"]
                pl = PlaceBl.from_node(node)
                # Default lang name
                name_node = record["name"]
                pl.name = PlaceName.from_node(name_node)
                # Other name versions
                for name_node in record["names"]:
                    pl.names.append(PlaceName.from_node(name_node))

                for notes_node in record['notes']:
                    n = Note.from_node(notes_node)
                    pl.notes.append(n)

                for medias_node in record['medias']:
                    m = Media.from_node(medias_node)
                    pl.media_ref.append(m)

        return pl
#                 if not (pl.type and pl.id):
#                     logger.error(f"Place_combo.read_w_notes: missing data for {pl}")
#         try:
#             return pl
#         except Exception:
#             logger.error(f"Place_combo.read_w_notes: no Place with uuid={uuid}") 
#             return None


    def dr_get_place_tree(self, locid, lang="fi"):
        """ Read upper and lower places around this place.
        
            Haetaan koko paikkojen ketju paikan locid ympärillä
            Palauttaa listan paikka-olioita ylimmästä alimpaan.
            Jos hierarkiaa ei ole, listalla on vain oma Place_combo.

            Esim. Tuutarin hierarkia
                  2 Venäjä -> 1 Inkeri -> 0 Tuutari -> -1 Nurkkala
                  tulee tietokannasta näin:
            ╒════╤═══════╤═════════╤══════════╤═══════╤═════════╤═════════╕
            │"lv"│"id1"  │"type1"  │"name1"   │"id2"  │"type2"  │"name2"  │
            ╞════╪═══════╪═════════╪══════════╪═══════╪═════════╪═════════╡
            │"2" │"21774"│"Region" │"Tuutari" │"21747"│"Country"│"Venäjä" │
            ├────┼───────┼─────────┼──────────┼───────┼─────────┼─────────┤
            │"1" │"21774"│"Region" │"Tuutari" │"21773"│"State"  │"Inkeri" │
            ├────┼───────┼─────────┼──────────┼───────┼─────────┼─────────┤
            │"-1"│"21775"│"Village"│"Nurkkala"│"21774"│"Region" │"Tuutari"│
            └────┴───────┴─────────┴──────────┴───────┴─────────┴─────────┘
            Metodi palauttaa siitä listan
                Place(result[0].id2) # Artjärvi City
                Place(result[0].id1) # Männistö Village
                Place(result[1].id1) # Pekkala Farm
            Muuttuja lv on taso:
                >0 = ylemmät,
                 0 = tämä,
                <0 = alemmat
        """
        t = DbTree(self.driver, CypherPlace.read_pl_hierarchy, 'pname', 'type')
        t.load_to_tree_struct(locid)
        if t.tree.depth() == 0:
            # Vain ROOT-solmu: Tällä paikalla ei ole hierarkiaa.
            # Hae oman paikan tiedot ilman yhteyksiä
            with self.driver.session() as session:
                result = session.run(CypherPlace.root_query, locid=int(locid))
                record = result.single()
                t.tree.create_node(record["name"], locid, parent=0,
                                   data={'type': record["type"],'uuid':record['uuid']})
        ret = []
        for tnode in t.tree.expand_tree(mode=t.tree.DEPTH):
            logger.debug(f"{t.tree.depth(t.tree[tnode])} {t.tree[tnode]} {t.tree[tnode].bpointer}")
            if tnode != 0:
                n = t.tree[tnode]

                # Get all names: default lang: 'name' and others: 'names'
                with self.driver.session() as session:
                    result = session.run(CypherPlace.read_pl_names,
                                         locid=tnode, lang=lang)
                    record = result.single()
                    # <Record
                    #    name=<Node id=514413 labels={'Place_name'}
                    #        properties={'name': 'Suomi', 'lang': ''}>
                    #    names=[<Node id=514415 labels={'Place_name'}
                    #            properties={'name': 'Finnland', 'lang': 'de'}>, 
                    #        <Node id=514414 labels={'Place_name'} ...}>
                    #    ]
                    # >
                lv = t.tree.depth(n)
                p = PlaceBl(uniq_id=tnode, ptype=n.data['type'], level=lv)
                p.uuid = n.data['uuid']
                node = record['name']    
                p.names.append(PlaceName.from_node(node))
                oth_names = []
                for node in record['names']:
                    oth_names.append(PlaceName.from_node(node))
                # Arrage names by local language first 
                lst = PlaceName.arrange_names(oth_names)
                p.names += lst
                
                # TODO: Order by lang here! (The order field is not in use) 
                p.pname = p.names[0].name
                #logger.info("# {}".format(p))
                p.parent = n.bpointer
                ret.append(p)
        return ret

    def dr_get_place_events(self, uniq_id):
        """ Find events and persons associated to given Place
        
            Haetaan paikkaan liittyvät tapahtumat sekä
            osallisen henkilön nimitiedot.
        """
        result = self.driver.session().run(CypherPlace.get_person_events, 
                                           locid=uniq_id)
        ret = []
        for record in result:
            # <Record 
            #    person=<Node id=523974 labels={'Person'}
            #        properties={'sortname': 'Borg#Maria Charlotta#', 'death_high': 1897, 
            #            'confidence': '', 'sex': 2, 'change': 1585409709, 'birth_low': 1841, 
            #            'birth_high': 1841, 'id': 'I0029', 'uuid': 'e9bc18f7e9b34f1e8291de96002689cd', 
            #            'death_low': 1897}> 
            #    role='Primary'
            #    names=[<Node id=523975 labels={'Name'}
            #            properties={'firstname': 'Maria Charlotta', 'type': 'Birth Name', 
            #                'suffix': '', 'surname': 'Borg', 'prefix': '', 'order': 0}>, 
            #        <Node id=523976 labels={'Name'} properties={...}>] 
            #    event=<Node id=523891 labels={'Event'} 
            #            properties={'datetype': 0, 'change': 1585409700, 'description': '', 
            #                'id': 'E0080', 'date2': 1885458, 'type': 'Birth', 'date1': 1885458, 
            #                'uuid': '160a0c75659145a4ac09809823fca5f9'}>
            # >
            e = Event_combo.from_node(record['event'])
            # Fields uid (person uniq_id) and names are on standard in Event_combo
            e.role = record["role"]
            e.person = Person_combo.from_node(record['person'])
            if e.person.too_new:    # Check privacy
                continue
            for node in record["names"]:
                e.person.names.append(Name.from_node(node))
            ret.append(e)
        return ret

