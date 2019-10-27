'''
Created on 2.5.2017 from Ged-prepare/Bus/classes/genealogy.py
Extracted 23.5.2019 from models.gen.place.Place

@author: jm
'''

import  shareds
from .place import Place, Place_name, Point
from .note import Note
from .dates import DateRange
from .cypher import Cypher_place
from models.dbtree import DbTree
from models.gen.event_combo import Event_combo
from models.gen.person_name import Name

import logging
logger = logging.getLogger('stkserver')

class Place_combo(Place):
    """ Place / Paikka:

        Properties:
            Defined here:
                names[]             PlaceName
                level               int hierarchy level
                coord               str paikan koordinaatit (leveys- ja pituuspiiri)
                surrounding[]       int uniq_ids of upper
                note_ref[]          int uniq_ids of Notes
            Defined in Place:
                handle
                change
                id                  esim. "P0001"
                type                str paikan tyyppi
                pname               str paikan nimi
            May be defined in Place_gramps:
                surround_ref[]      dictionaries {'hlink':handle, 'dates':dates}
                citation_ref[]      int uniq_ids of Citations
                placeref_hlink      str paikan osoite
                noteref_hlink       str huomautuksen osoite (tulostuksessa Note-olioita)
     """

    def __init__(self, uniq_id=None, ptype="", level=None):
        """ Creates a new Place_combo instance.

            You may also give for printout eventuell hierarhy level
        """
        Place.__init__(self, uniq_id)
        
        if ptype:
            self.type = ptype
        self.names = []
        if level != None:
            self.level = level

        self.uppers = []        # Upper place objects for hirearchy display
        self.notes = []         # Notes connected to this place
        self.note_ref = []      # uniq_ids of Notes


    def __str__(self):
        if hasattr(self, 'level'):
            lv = self.level
        else:
            lv = ""
        return f"{self.pname} ({self.type}) {lv}"


#     @classmethod from_node(cls, node):
#         ''' Creates a node object of type Place_combo from a Neo4j node.


    def show_names_list(self):
        # Returns list of referred Place_names for this place
        # If none, return pname
        name_list = []
        for nm in self.names:
            if nm.lang:
                name_list.append("{} ({})".format(nm.name, nm.lang))
            else:
                # Put first the name with no lang
                name_list = [nm.name] + name_list
        if name_list:
            return name_list
        else:
            return [self.pname]


    @staticmethod
    def read_place_w_names(uniq_id):
        """ Reads Place_combo nodes or selected node with Place_name objects.
        """
        result = None
        with shareds.driver.session() as session:
            if uniq_id:
                result = session.run(Cypher_place.place_get_one, pid=uniq_id)
            else:
                result = session.run(Cypher_place.place_get_all)

        places = []

        for record in result:
            # Create a Place_combo object from record
            node = record['p']
            pl = Place_combo.from_node(node)
            names = []
            for node in record['names']:
                # <Node id=78278 labels={'Place_name'} properties={'lang': '', 
                #    'name': 'Kangasalan srk'}>
                plname = Place_name.from_node(node)
                names.append(str(plname))
                pl.names.append(plname)
            pl.clearname = ' • '.join(names)
            places.append(pl)

        return places

    @staticmethod
    def get_w_notes(locid): 
        """ Returns the Place_combo with Notes and PlaceNames included.

            #TODO: Luetaan Notes ja Citations vasta get_persondata_by_id() lopuksi?
        """
        #if isinstance(locid,int):
        #    p.uniq_id = locid
        #else:
        #    p.uuid = locid

        with shareds.driver.session() as session:
            if isinstance(locid,int):
                place_result = session.run(Cypher_place.get_w_names_notes, 
                                       place_id=locid)
            else:
                place_result = session.run(Cypher_place.get_w_names_notes_uuid, 
                                       uuid=locid)

            for place_record in place_result:
                # <Record
                #    place=<Node id=287246 labels={'Place'}
                #        properties={'coord': [60.375, 21.943], 
                #            'handle': '_da3b305b41147508033e318249b', 'id': 'P0335', 
                #            'type': 'City', 'pname': 'Rymättylä', 'change': 1556954336}> 
                #    names=[
                #        <Node id=287247 labels={'Place_name'} 
                #            properties={'name': 'Rymättylä', 'lang': ''}>, 
                #        <Node id=287248 labels={'Place_name'} 
                #            properties={'name': 'Rimito', 'lang': 'sv'}> ] 
                #    notes=[]>

                node = place_record["place"]
                pl = Place_combo.from_node(node)

                for names_node in place_record["names"]:
                    pl.names.append(Place_name.from_node(names_node))
#                     if pl.names[-1].lang in ['fi', '']:
#                         #TODO: use current_user's lang
#                         pl.pname = pl.names[-1].name

                for notes_node in place_record['notes']:
                    n = Note.from_node(notes_node)
                    pl.notes.append(n)
                if not (pl.type and pl.id):
                    logger.error(f"Place_combo.read_w_notes: missing data for {pl}")

        try:
            return pl
        except Exception:
            logger.error(f"Place_combo.read_w_notes: no Place with locid={locid}") 
            return None


    @staticmethod
    def get_my_places():
        """ Luetaan kaikki paikat kannasta
        #TODO Eikö voisi palauttaa listan Place_combo-olioita?
        """

        query = """
 MATCH (p:Place)
 OPTIONAL MATCH (p) -[r:IS_INSIDE]-> (up:Place)
 RETURN ID(p) AS uniq_id, p, 
     COLLECT(DISTINCT [up.pname, r.datetype, r.date1, r.date2]) AS up
 ORDER BY p.pname, p.type"""

        result = shareds.driver.session().run(query)

        titles = ['uniq_id', 'handle', 'change', 'id', 'type', 'pname',
                  'coord', 'upper']
        lists = []

        for record in result:
            # <Record uniq_id=271313 
            #    p=<Node id=271313 labels={'Place'} 
            #        properties={'coord': [60.0, 27.0], 'handle': '_ddd39c2aa3518f6db8053050c70', 
            #        'id': 'P0000', 'type': 'Town', 'pname': 'Helsinki', 'change': 1524381255}> 
            #    up=[
            #        ['Suomen suuriruhtinaskunta', 3, 1852509, 1964420], 
            #        ['Suomi', 2, 1964421, 1964421]
            #    ]>
            data_line = []
            if record['uniq_id']:
                data_line.append(record['uniq_id'])
            else:
                data_line.append('')
            if record["p"]['handle']:
                data_line.append(record["p"]['handle'])
            else:
                data_line.append('')
            if record["p"]['change']:
                data_line.append(record["p"]['change'])
            else:
                data_line.append('')
            if record["p"]['id']:
                data_line.append(record["p"]['id'])
            else:
                data_line.append('')
            if record["p"]['type']:
                data_line.append(record["p"]['type'])
            else:
                data_line.append('')
            if record["p"]['pname']:
                data_line.append(record["p"]['pname'])
            else:
                data_line.append('')
            if record["p"]['coord']:
                data_line.append(record["p"]['coord'])
            else:
                data_line.append('')
            uppers = []
            for up in record['up']:
                if up[0]:
                    # ['Suomi', 2, 1964421, 1964421]
                    pname = up[0]
                    if up[1]:
                        dates = DateRange(up[1],up[2],up[3])
                        text = f'{pname} ({dates})'
                    else:
                        text = pname
                    uppers.append(text)
            data_line.append(uppers)

            lists.append(data_line)

        return (titles, lists)


    @staticmethod
    def get_place_hierarchy():
        """ Get a list on Place_combo objects with nearest heirarchy neighbours.
        
            Haetaan paikkaluettelo ml. hierarkiassa ylemmät ja alemmat

            Esim.
╒══════╤═════════╤════════════════════╤═══════╤════════════════════╤════════════════════╕
│"id"  │"type"   │"name"              │"coord"│"upper"             │"lower"             │
╞══════╪═════════╪════════════════════╪═══════╪════════════════════╪════════════════════╡
│290228│"Borough"│[{"name":"1. Kaupung│null   │[[287443,"City","Arc│[[290226,"Tontti","T│
│      │         │inosa","lang":""}]  │       │topolis","la"],[2874│ontti 23",""]]      │
│      │         │                    │       │43,"City","Björnebor│                    │
│      │         │                    │       │g","sv"],[287443,"Ci│                    │
│      │         │                    │       │ty","Pori",""],[2874│                    │
│      │         │                    │       │43,"City","Пори","ru│                    │
│      │         │                    │       │"]]                 │                    │
└─────┴──────────┴────────────────────┴───────┴────────────────────┴────────────────────┘
"""
        def combine_places(pn_tuples):
            """ Creates a list of Places with names combined from given names.
            
                Kenttä pl_tuple sisältää Places-tietoja 
                tuplena [[28101, "City", "Lovisa", "sv"]].

                Jos sama Place esiintyy uudestaan, niiden nimet yhdistetään.
                Jos nimeen on liitetty kielikoodi, se laitetaan sulkuihin mukaan.
            """
            placedict = {}
            for nid, nuuid, ntype, name, lang in pn_tuples:
                if nid: # id of a lower place
                    pn = Place_name(name=name, lang=lang)
                    if nid in placedict:
                        # Append name to existing Place_combo
                        placedict[nid].names.append(pn)
                        if pn.lang in ['fi', '']:
                            # Default language name
                            #TODO use language from current_user's preferences
                            placedict[nid].pname = pn.name
                    else:
                        # Add a new Place_combo
                        p = Place_combo(nid)
                        p.uuid = nuuid
                        p.type = ntype
                        p.names.append(pn)
                        p.pname = pn.name
                        placedict[nid] = p
                        # ntype, Place_combo.namelist_w_lang( (name,) ))
            return list(placedict.values())


        ret = []
        result = shareds.driver.session().run(Cypher_place.get_name_hierarchies)
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
            p = Place_combo(pl_id)
            p.uuid =record['uuid']
            p.type = record.get('type')
            if record['coord']:
                p.coord = Point(record['coord']).coord
            # Set place names and default display name pname
            for nnode in record.get('names'):
                pn = Place_name.from_node(nnode)
                if pn.lang in ['fi', '']:
                    # Default language name
                    #TODO use language from current_user's preferences
                    p.pname = pn.name
                p.names.append(pn)
            if p.pname == '' and p.names:
                p.pname = p.names[0].name
            p.uppers = combine_places(record['upper'])
            p.lowers = combine_places(record['lower'])
            ret.append(p)
        # Return sorted by first name in the list p.pname
        return sorted(ret, key=lambda x:x.pname)


    def set_names_from_nodes(self, nodes):
        ''' Filter Name objects from a list of Cypher nodes to self.names.
        
            Fill self.names with Place_names by following rules:
            1. Place_names using lang == current_user.language
            2. Place_names using lang == ""
            3. If none found, use the last Place_name
            Place_names using other languages are discarded

            nodes=[
                <Node id=305800 labels={'Place_name'} properties={'name': 'Helsingfors', 'lang': ''}>, 
                <Node id=305799 labels={'Place_name'} properties={'name': 'Helsinki', 'lang': 'sv'}>
            ]>
        '''
        own_lang = []
        no_lang = []
        alien_lang = []
        from flask_security import current_user
        for node in nodes:
            pn = Place_name.from_node(node)
            if pn.lang == "":
                no_lang.append(pn)
                ##print(f"# - no lang {len(self.names)} (Place_name {pn.uniq_id} {pn})")
            elif pn.lang == current_user.language:
                own_lang.append(pn)
                ##print(f"# - my lang (Place_name {pn.uniq_id} {pn})")
            else:
                alien_lang.append(pn)
                ##print(f"# - alien lang (Place_name {pn})")

        if own_lang:
            self.names = own_lang
        elif no_lang:
            self.names = no_lang
        else:
            self.names = alien_lang
        #for pn in self.names:
        #    print(f"#  names: {pn}")


    def namelist_w_lang(self):
        """ Return a vector of name data for this place.
         
            [[name, lang], [name,lang]]
         
            Muodostetaan nimien luettelo jossa on mahdolliset kielikoodit
            mainittuna.
            Jos sarakkeessa field[1] on mainittu kielikoodi
            se lisätään kunkin nimen field[0] perään suluissa
        #TODO Lajiteltava kielen mukaan jotenkin
        """
        ret = []
        for n in sorted(self.names, key=lambda x:x.lang):
            ret.append(n)
        return ret


    @staticmethod
    def get_place_tree(locid):
        """ Haetaan koko paikkojen ketju paikan locid ympärillä
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

        # Query for Place hierarcy
        hier_query = """
MATCH x= (p:Place)<-[r:IS_INSIDE*]-(i:Place) WHERE ID(p) = $locid
    RETURN NODES(x) AS nodes, SIZE(r) AS lv, r
    UNION
MATCH x= (p:Place)-[r:IS_INSIDE*]->(i:Place) WHERE ID(p) = $locid
    RETURN NODES(x) AS nodes, SIZE(r)*-1 AS lv, r
"""
        # Query for single Place without hierarcy
        root_query = """
MATCH (p:Place) WHERE ID(p) = $locid
RETURN p.type AS type, p.uuid as uuid, p.pname AS name
"""
        # Query to get names for a Place
        name_query="""
MATCH (l:Place)-->(n:Place_name) WHERE ID(l) = $locid
RETURN COLLECT(n) AS names LIMIT 15
"""

        t = DbTree(shareds.driver, hier_query, 'pname', 'type')
        t.load_to_tree_struct(locid)
        if t.tree.depth() == 0:
            # Vain ROOT-solmu: Tällä paikalla ei ole hierarkiaa.
            # Hae oman paikan tiedot ilman yhteyksiä
            with shareds.driver.session() as session:
                result = session.run(root_query, locid=int(locid))
                record = result.single()
                t.tree.create_node(record["name"], locid, parent=0,
                                   data={'type': record["type"],'uuid':record['uuid']})
        ret = []
        for node in t.tree.expand_tree(mode=t.tree.DEPTH):
            logger.debug(f"{t.tree.depth(t.tree[node])} {t.tree[node]} {t.tree[node].bpointer}")
            if node != 0:
                n = t.tree[node]

                # Get all names
                with shareds.driver.session() as session:
                    result = session.run(name_query, locid=node)
                    record = result.single()
#                     Kysely palauttaa esim. [["Svartholm","sv"],["Svartholma",""]]
#                     josta tehdään ["Svartholm (sv)","Svartholma"]
#                     
                    # <Record names=[
                    #    <Node id=289028 labels={'Place_name'} 
                    #        properties={'name': 'Finland', 'lang': 'sv'}>, 
                    #    <Node id=289027 labels={'Place_name'} 
                    #        properties={'name': 'Suomi', 'lang': ''}>, 
                    #    <Node id=289029 labels={'Place_name'} 
                    #        properties={'name': 'Finnland', 'lang': 'de'}>
                    # ]>
                lv = t.tree.depth(n)
                p = Place_combo(uniq_id=node, ptype=n.data['type'], level=lv)
                p.uuid = n.data['uuid']
                for node in record['names']:
                    p.names.append(Place_name.from_node(node))
                # TODO: Order by lang here!
                if p.names:
                    p.pname = p.names[0].name
                    
                logger.info("# {}".format(p))
                p.parent = n.bpointer
                ret.append(p)
        return ret


    @staticmethod
    def get_place_events(loc_id):
        """ Haetaan paikkaan liittyvät tapahtumat sekä
            osallisen henkilön nimitiedot.

        Palauttaa esimerkin mukaiset tiedot:
        ╒══════╤═════════╤═══════════════════╤═════════════╤═══════════════════╕
        │"uid" │"role"   │"names"            │"etype"      │"edates"           │
        ╞══════╪═════════╪═══════════════════╪═════════════╪═══════════════════╡
        │305353│"Primary"│[{"firstname":"Eva │"Residence"  │[3,1863872,1866944]│
        │      │         │Sophia","type":"Bir│             │                   │
        │      │         │th Name","suffix":"│             │                   │
        │      │         │","surname":"Forsté│             │                   │
        │      │         │n","order":0, "pref│             │                   │
        |      |         |ix":""}]           │             │                   │
        ├──────┼─────────┼───────────────────┼─────────────┼───────────────────┤
        │305450│"Primary"│[{"firstname":"Erik│"Occupation" │[3,1863872,1866944]│
        │      │         │ Berndt","type":"Bi│             │                   │
        │      │         │rth Name","suffix":│             │                   │
        │      │         │"","surname":"Konow│             │                   │
        │      │         │","order":0, "prefi│             │                   │
        |      |         |x":"von"}]         │             │                   │
        └──────┴─────────┴───────────────────┴─────────────┴───────────────────┘
        """
        result = shareds.driver.session().run(Cypher_place.get_person_events, 
                                              locid=int(loc_id))
        ret = []
        for record in result:
            e = Event_combo()
            # Fields uid (person uniq_id) and names are on standard in Event_combo
            e.uid = record["uid"]
            e.type = record["etype"]
            if record["edates"][0] != None:
                dates = DateRange(record["edates"])
                e.dates = str(dates)
                e.date = dates.estimate()
            e.role = record["role"]
            e.names = []
            for node in record["names"]:
                e.names.append(Name.from_node(node))
            ret.append(e)
        return ret

    @staticmethod
    def get_total():
        """ Tulostaa paikkojen määrän tietokannassa """

        query = "MATCH (p:Place) RETURN COUNT(p)"
        results =  shareds.driver.session().run(query)
        for result in results:
            return str(result[0])


    def print_data(self):
        """ Tulostaa tiedot """
        print ("*****Placeobj*****")
        print ("Handle: " + self.handle)
        print ("Change: {}".format(self.change))
        print ("Id: " + self.id)
        print ("Type: " + self.type)
        if self.pname:
            print ("Pname: " + self.pname)
        if self.coord:
            print ("Coord: {}".format(self.coord))
        return True


#     save() - see PlaceGramps.save()
