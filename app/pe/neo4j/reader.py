'''
Created on 17.3.2020

@author: jm
'''
import logging
from models.gen.family_combo import Family_combo
logger = logging.getLogger('stkserver')

from bl.place import PlaceBl, PlaceName
from bl.source import SourceBl
#from pe.neo4j.neo_source import SourceDb
#from bl.place_coordinates import Point
from .cypher_place import CypherPlace
from .cypher_source import CypherSource

#Todo: Change Old style includes to bl classes
from models.gen.person_combo import Person_combo
from models.gen.cypher import Cypher_person
from models.gen.person_name import Name
from models.gen.event import Event
from models.gen.event_combo import Event_combo
from models.gen.note import Note
from models.gen.media import Media
from models.gen.repository import Repository
from models.dbtree import DbTree
from models.gen.citation import Citation


class Neo4jReadDriver:
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
            print('Error pe.neo4j.reader.Neo4jReadDriver.dr_get_person_list: {} {}'.format(e.__class__.__name__, e))            
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
                print("pe.neo4j.reader.Neo4jReadDriver.dr_get_place_list_fw: from common")
                result = session.run(CypherPlace.get_common_name_hierarchies,
                                     fw=fw_from, limit=limit, lang=lang)
            else: 
                #2 get my own
                print("pe.neo4j.reader.Neo4jReadDriver.dr_get_place_list_fw: by owner")
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


    def dr_get_source_list_fw(self, **kwargs):
        """ Read all sources with notes and repositories, optionally limited by keywords.
         
            used arguments:
            - user        Username to select data
            - theme1      A keyword (fi) for selecting source titles
            - theme2      Another keyword (sv) for selecting source titles
            - fw          Read sources starting from this keyword
            - count       How many sources to read

            Todo: Valinta vuosien mukaan
            Todo: tuloksen sivuttaminen esim. 100 kpl / sivu
        """
        sources = []
        user = kwargs.get('user')

        with self.driver.session() as session:
            if kwargs.get('theme1'):
                # Filter sources by searching keywords in fi and sv langiage
                key1 = kwargs.get('theme1')
                key2 = kwargs.get('theme2')
                if user: 
                    # Show my researcher data
                    print("dr_get_source_list_fw: my researcher data")
                    result = session.run(CypherSource.get_own_set_selections,
                                         key1=key1, key2=key2)
                else:
                    print("dr_get_source_list_fw: approved common only")
                    result = session.run(CypherSource.get_auditted_set_selections,
                                         key1=key1, key2=key2)
            else:
                # Show all themes
                if user: 
                    # Show my researcher data
                    print("dr_get_source_list_fw: my researcher data")
                    result = session.run(CypherSource.get_own_sets)
                else:
                    print("dr_get_source_list_fw: approved common only")
                    result = session.run(CypherSource.get_auditted_sets)
 
        for record in result:
            # <Record 
            #    owner_type='PASSED' 
            #    source=<Node id=333338 labels={'Source'}
            #        properties={'id': 'S0029', 'stitle': 'Lapinjärvi vihityt 1788-1803 vol  es346', 
            #            'uuid': '4637e07dcc7f42c09236a8482fb01b7c', 'spubinfo': '', 'sauthor': '', 
            #            'change': 1532807569}>
            #    notes=[
            #        <Node id=445002 labels={'Note'} 
            #            properties={'id': 'N2207', 'text': '', 'type': 'Source Note', 
            #                'uuid': 'e6efcc1fbcad4dcd85352fd95cd5bf35', 'url': 'http://www.sukuhistoria.fi/sshy/sivut/jasenille/paikat.php?bid=3788',
            #                'change': 1532807569}>] 
            #    repositories=[
            #        [   'Book', 
            #            <Node id=393661 labels={'Repository'} 
            #                properties={'id': 'R0003', 'rname': 'Lapinjärven seurakunnan arkisto',
            #                    'type': 'Archive', 'uuid': 'b6171feb05bc47de87ee509a79821d8f',
            #                    'change': 1577815469}>]] cit_cnt=0 ref_cnt=0>
             
            # <Record
            # 0  uniq_id=242567 
            # 1  source=<Node id=242567 labels={'Source'} 
            #        properties={'handle': '_dcb5682a0f47b7de686b3251557', 'id': 'S0334', 
            #            'stitle': 'Åbo stifts herdaminne 1554-1640', 'change': '1516698633'}> 
            # 2  notes=[<Node id=238491 labels={'Note'} 
            #        properties={'handle': '_e07cd6210c57e0d53393a62fa7a', 'id': 'N3952', 
            #        'text': '', 'type': 'Source Note', 'url': 'http://www.narc.fi:8080/...', 
            #        'change': 1542667331}>] 
            # 3  repositories=[
            #        ['Book', <Node id=238996 labels={'Repository'} 
            #            properties={'handle': '_db51a3f358e67ac82ade828edd1', 'id': 'R0057', 
            #            'rname': 'Painoteokset', 'type': 'Collection', 'change': '1541350910'}>]]
            # 4  cit_cnt=1 
            # 5  ref_cnt=1
            # >
            source = record['source']
            s = SourceBl.from_node(source)
            notes = record['notes']
            for note in notes:
                n = Note.from_node(note)
                s.notes.append(n)
            repositories = record['repositories']
            for repo in repositories:
                # [medium, repo_node]
                if repo[1] != None:
                    rep = Repository.from_node(repo[1])
                    rep.medium = repo[0]
                    s.repositories.append(rep)
            s.cit_cnt = record['cit_cnt']
            s.ref_cnt = record['ref_cnt']
            sources.append(s)
 
        return sources


    def dr_get_source_w_repository(self, user, uuid): 
        """ Returns the PlaceBl with Notes and PlaceNames included.
        """
        source = None
        with self.driver.session() as session:
            if user == None: 
                result = session.run(CypherSource.get_auditted_set_single_selection,
                                     uuid=uuid)
            else:
                result = session.run(CypherSource.get_own_set_single_selection,
                                     user=user, uuid=uuid)
            for record in result:
                # <Record 
                #    owner_type='PASSED'
                #    source=<Node id=340694 labels={'Source'}
                #        properties={'id': 'S1112', 'stitle': 'Aamulehti (sanomalehti)',
                #            'uuid': '3ac9c9e3c3a0490f8e064225b90139e1', 'spubinfo': '',
                #            'sauthor': '', 'change': 1585409705}>
                #    notes=[]
                #    reps=[
                #        ['Book', <Node id=337715 labels={'Repository'}
                #            properties={'id': 'R0002', 'rname': 'Kansalliskirjaston digitoidut sanomalehdet',
                #                'type': 'Collection', 'uuid': '2fc57cc64197461eb94a4bcc02da9ff9',
                #                'change': 1585409708}>]]
                # >
                source_node = record['source']
                source = SourceBl.from_node(source_node)
                notes = record['notes']
                for note_node in notes:
                    n = Note.from_node(note_node)
                    source.notes.append(n)
                repositories = record['reps']
                for medium, repo_node in repositories:
                    if repo_node != None:
                        rep = Repository.from_node(repo_node)
                        rep.medium = medium
                        source.repositories.append(rep)

            return source


    def dr_get_source_citations(self, sourceid:int):
        """ Read Events and Person, Family and Media citating this Source.

            Returns
            - citation      Citation node
            - notes         list of Note nodes for this citation
            - near          node connected derectly to Citation
            - targets       list of the Person or Family nodes 
                            (from near or behind near)
        """

        def obj_from_node(node, role=None):
            ''' Create Person or Family object from node
            '''
            if 'Person' in node.labels:
                obj = Person_combo.from_node(node)
            elif 'Family' in node.labels:
                obj = Family_combo.from_node(node)
                obj.clearname = obj.father_sortname+' <> '+obj.mother_sortname
            else:
                raise NotImplementedError('Person or Family expexted: {node.labels}')
            obj.role = role
            if obj.role == 'Primary':
                obj.role = None
            return obj

        citations = {}      # {uniq_id:citation_object}
        notes = {}          # {uniq_id:[note_object]}
        #near = {}           # {uniq_id:object}
        targets = {}         # {uniq_id:[object]} Person or Family

        with self.driver.session() as session:
            result = session.run(CypherSource.get_citators_of_source, 
                                 uniq_id=sourceid)
        for record in result:
            # <Record        # (1) A Person or Family
            #                #     referencing directly Citation
            #    citation=<Node id=342041 labels={'Citation'}
            #        properties={'id': 'C2840', 'page': '11.10.1907 sivu 2',
            #            'uuid': '03b2c7a7dac84701b67612bf10f60b6b', 'confidence': '2',
            #            'change': 1585409708}>
            #    notes=[<Node id=384644 labels={'Note'}
            #        properties={'id': 'N3556', 'text': '', 'type': 'Citation', 'uuid': '4a377b0e936d4e68a72cad64a4925db9',
            #            'url': 'https://digi.kansalliskirjasto.fi/sanomalehti/binding/609338?page=2&term=Sommer&term=Maria&term=Sommerin&term=sommer',
            #            'change': 1585409709}>]
            #    near=<Node id=347773 labels={'Person'}
            #            properties={'sortname': 'Johansson#Gustaf#', 'death_high': 1920, 'confidence': '2.0',
            #                'sex': 1, 'change': 1585409699, 'birth_low': 1810, 'birth_high': 1810,
            #                'id': 'I1745', 'uuid': 'dfc866bfa9274071b37ccc2f6c33abed',
            #                'death_low': 1852}>
            #    far=[]
            # >
            # <Record        # (2) A Person or Family having an Event, Name, or Media
            #                #     referencing the Citation
            #    citation=<Node id=342042 labels={'Citation'} properties={...}>
            #    notes=[<Node id=381700 labels={'Note'} properties={...}>]
            #    near=<Node id=359150 labels={'Event'}
            #        properties={'datetype': 0, 'change': 1585409703, 'description': '',
            #            'id': 'E5451', 'date2': 1953097, 'type': 'Death', 'date1': 1953097,
            #            'uuid': '467b67c1a0f84b8baed150b030a7bef0'}>
            #    far=[
            #         [<Node id=347835 labels={'Person'}
            #            properties={'sortname': 'Sommer#Arthur#',...}>,
            #          'Primary']
            #    ]
            # >
            citation_node = record['citation']
            note_nodes = record['notes']
            near_node = record['near']
            far_nodes = record['far']

            uniq_id = citation_node.id
            citation = Citation.from_node(citation_node)
            citations[uniq_id] = citation

            notelist = []
            for node in note_nodes:
                notelist.append(Note.from_node(node))
            if notelist:
                notes[uniq_id] = notelist

            targetlist = []
            for node, role in far_nodes:
                if not node: continue
                obj = obj_from_node(node, role)
                if obj:         # Far node is the Person or Family
                    obj.eventtype = near_node['type']
                    targetlist.append(obj)
            if not targetlist:  # No far node: there is a middle node near
                obj = obj_from_node(near_node)
                targetlist.append(obj)
            targets[uniq_id] = targetlist

        # Result dictionaries using key = Citation uniq_id
        return citations, notes, targets


    def dr_inlay_person_lifedata(self, person): 
        """ Reads person's default name, bith event and death event into Person obj.
        """
        with self.driver.session() as session:
            result = session.run(CypherSource.get_person_lifedata,
                                 pid=person.uniq_id)
            for record in result:
                # <Record
                #    name=<Node id=379934 labels={'Name'} 
                #        properties={'firstname': 'Gustaf', 'type': 'Also Known As', 'suffix': '', 'prefix': '', 
                #            'surname': 'Johansson', 'order': 0}>
                #    events=[
                #        <Node id=492911 labels={'Event'} 
                #            properties={'datetype': 0, 'change': 1577803201, 'description': '', 
                #                'id': 'E7750', 'date2': 1853836, 'type': 'Birth', 'date1': 1853836, 
                #                'uuid': '794e0c9e6f15479cb5d33dc4cf245a7d'}>
                #    ]
                #>
                name_node = record['name']
                person.names.append(Name.from_node(name_node))
                events = record['events']
                for node in events:
                    e = Event.from_node(node)
                    if e.type == "Birth":
                        person.event_birth = e
                    else:
                        person.event_death = e
        return


