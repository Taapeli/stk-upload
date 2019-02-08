'''
Created on 2.5.2017 from Ged-prepare/Bus/classes/genealogy.py

@author: jm
'''

from sys import stderr

import  shareds
#from .weburl import Weburl
from .note import Note
from .dates import DateRange
from .cypher import Cypher_place
from models.dbtree import DbTree
from models.cypher_gramps import Cypher_place_w_handle
from models.gen.event_combo import Event_combo

class Place:
    """ Paikka

        Properties:
                handle
                change
                id                  esim. "P0001"
                type                str paikan tyyppi
                pname               str paikan nimi
                names[]:
                   name             str paikan nimi
                   lang             str kielikoodi
                   dates            DateRange date expression
                coord               str paikan koordinaatit (leveys- ja pituuspiiri)
                surrounding[]       int uniq_ids of upper
                surround_ref[]      dictionaries {'hlink':handle, 'dates':dates}
                note_ref[]          int uniq_ids of Notes
                citation_ref[]      int uniq_ids of Citations
                placeref_hlink      str paikan osoite
                noteref_hlink       str huomautuksen osoite (tulostuksessa Note-olioita)
     """

    def __init__(self, uniq_id=None, ptype="", pname="", level=None):
        """ Luo uuden place-instanssin.
            Argumenttina voidaan antaa valmiiksi paikan uniq_id, tyylin, nimen
            ja (tulossivua varten) mahdollisen hierarkiatason
        """
        self.uniq_id = uniq_id
        self.type = ptype
        self.pname = pname
        if level != None:
            self.level = level
        # Gramps-tietoja
        self.handle = ''
        self.change = 0
        self.names = []
        self.coord = None
        
        self.uppers = []        # Upper place objects for hirearchy display
        self.notes = []         # Upper place objects for hierarchy display
#         self.urls = []          # Weburl poistettu, käytössä notes[]

        self.note_ref = []      # uniq_ids of Notes
        self.surround_ref = []  # members are dictionaries {'hlink':hlink, 'dates':dates}
        self.noteref_hlink = []


    def __str__(self):
        if hasattr(self, 'level'):
            lv = self.level
        else:
            lv = ""
        desc = "{} {} ({}) {}".format(self.uniq_id, self.pname, self.type, lv)
        return desc


    @classmethod
    def from_node(cls, node):
        ''' models.gen.place.Place.from_node
        Transforms a db node to an object of type Place.
        
        <Node id=78279 labels={'Place'} 
            properties={'handle': '_da68e12a415d936f1f6722d57a', 'id': 'P0002', 
                'change': 1500899931, 'pname': 'Kangasalan srk', 'type': 'Parish'}>

        '''
        p = cls()
        p.uniq_id = node.id
        p.handle = node['handle']
        p.change = node['change']
        p.id = node['id'] or ''
        p.type = node['type'] or ''
        p.pname = node['pname'] or ''
        return p


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
        """ Reads Place nodes or selected Place node with Place_name objects
            and clearname
        """
        result = None
        with shareds.driver.session() as session:
            if uniq_id:
                result = session.run(Cypher_place.place_get_one, pid=uniq_id)
            else:
                result = session.run(Cypher_place.place_get_all)

        places = []

        for record in result:
            # Create a Place object from record
            node = record['p']
            pl = Place.from_node(node)
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


    def read_w_notes(self):
        """ Luetaan kaikki paikan tiedot ml. nimivariaatiot (tekstinä)
            #TODO: Luetaan Notes ja Citations vasta get_persondata_by_id() lopuksi

            Nimivariaatiot talletetaan kenttään pname,
            esim. [["Svartholm", "sv"], ["Svartholma", None]]
            #TODO: Ei hieno, pitäisi palauttaa Place_name objects!
        """
        with shareds.driver.session() as session:
            place_result = session.run(Cypher_place.get_w_names_notes, 
                                       place_id=self.uniq_id)

            for place_record in place_result:
                self.change = int(place_record["place"]["change"])  #TODO only temporary int()
                self.id = place_record["place"]["id"]
                self.type = place_record["place"]["type"]
                self.coord = place_record["place"]["coord"]
                self.pname = Place.namelist_w_lang(place_record["names"])

                for node in place_record['notes']:
                    n = Note.from_node(node)
                    self.notes.append(n)
        return


    @staticmethod
    def get_my_places():
        """ Luetaan kaikki paikat kannasta
        #TODO Eikö voisi palauttaa listan Place-olioita?
        """

        query = """
 MATCH (p:Place)
 RETURN ID(p) AS uniq_id, p
 ORDER BY p.pname, p.type"""

        result = shareds.driver.session().run(query)

        titles = ['uniq_id', 'handle', 'change', 'id', 'type', 'pname',
                  'coord']
        lists = []

        for record in result:
            data_line = []
            if record['uniq_id']:
                data_line.append(record['uniq_id'])
            else:
                data_line.append('-')
            if record["p"]['handle']:
                data_line.append(record["p"]['handle'])
            else:
                data_line.append('-')
            if record["p"]['change']:
                data_line.append(int(record["p"]['change']))  #TODO only temporary int()
            else:
                data_line.append('-')
            if record["p"]['id']:
                data_line.append(record["p"]['id'])
            else:
                data_line.append('-')
            if record["p"]['type']:
                data_line.append(record["p"]['type'])
            else:
                data_line.append('-')
            if record["p"]['pname']:
                data_line.append(record["p"]['pname'])
            else:
                data_line.append('-')
            if record["p"]['coord']:
                data_line.append(record["p"]['coord'])
            else:
                data_line.append('-')

            lists.append(data_line)

        return (titles, lists)


    @staticmethod
    def get_place_hierarchy():
        """ Haetaan paikkaluettelo ml. hierarkiassa ylemmät ja alemmat
            Place list with upper and lower places in herarchy

            Esim.
╒═════╤══════════╤═══════════════════╤═══════╤═══════════════════╤═══════════════════╕
│"id" │"type"    │"name"             │"coord"│"upper"            │"lower"            │
╞═════╪══════════╪═══════════════════╪═══════╪═══════════════════╪═══════════════════╡
│91225│"Tontti"  │[["1. Kortteli Nro │null   │[[78239,"City","Bor│[[null,null,null,nu│
│     │          │8",""]]            │       │gå","sv"],[78239,"C│ll]]               │
│     │          │                   │       │ity","Porvoo",""]] │                   │
├─────┼──────────┼───────────────────┼───────┼───────────────────┼───────────────────┤
│78068│"Tontti"  │[["2. Kortteli 2. T│null   │[[null,null,null,nu│[[null,null,null,nu│
│     │          │ontti",""]]        │       │ll]]               │ll]]               │
├─────┼──────────┼───────────────────┼───────┼───────────────────┼───────────────────┤
│92425│"Kortteli"│[["2. quarter",""]]│[60.122│[[78213,"City","Fre│[[92510,"Tontti","T│
│     │          │                   │7857,24│drikshamn","sv"],[7│ontti 39",""]]     │
│     │          │                   │.440669│8213,"City","Hamina│                   │
│     │          │                   │4]     │",""]]             │                   │
├─────┼──────────┼───────────────────┼───────┼───────────────────┼───────────────────┤
│92457│"Tontti"  │[["3. Kortteli 3. t│null   │[[92339,"City","Lov│[[null,null,null,nu│
│     │          │ontti",""]]        │       │iisa",""],[92339,"C│ll]]               │
│     │          │                   │       │ity","Degerby",""]]│                   │
├─────┼──────────┼───────────────────┼───────┼───────────────────┼───────────────────┤
│92455│"Tontti"  │[["3. Kortteli 8. t│null   │[[92339,"City","Lov│[[null,null,null,nu│
│     │          │ontti",""]]        │       │iisa",""],[92339,"C│ll]]               │
│     │          │                   │       │ity","Degerby",""]]│                   │
└─────┴──────────┴───────────────────┴───────┴───────────────────┴───────────────────┘
"""

        def combine_places(pl_tuple):
            """ Returns a list of cleartext names got from Place_name objects
            
                Kenttä pl_tuple sisältää Places-tietoja tuplena [[28101, "City",
                "Lovisa", "sv"]].
                Jos sama Place esiintyy uudestaan, niiden nimet yhdistetään.
                Jos nimeen on liitetty kielikoodi, se laitetaan sulkuihin mukaan.
            """
            namedict = {}
            for near in pl_tuple:
                if near[0]: # id of a lower place
                    if near[0] in namedict:
                        # Append name to existing Place
                        namedict[near[0]].pname.extend(Place.namelist_w_lang( (near[2:],) ))
                    else:
                        # Add a new Place
                        namedict[near[0]] = \
                            Place(near[0], near[1], Place.namelist_w_lang( (near[2:],) ))
            return list(namedict.values())

        ret = []
        result = shareds.driver.session().run(Cypher_place.get_name_hierarcy)
        for record in result:
            # Record: <Record id=140843 type='Tontti' 
            #    name=[['1. Kortteli Nro 37', ''], ['Elias Unoniuksen kauppaliike', '']] 
            #    coord=None upper=[[140824, 'City', 'Degerby', ''], [140824, 'City', 'Loviisa', '']] 
            #    lower=[[None, None, None, None]]>

            # Luodaan paikka ja siihen taulukko liittyvistä hierarkiassa lähinnä
            # alemmista paikoista
            p = Place(record['id'], record['type'], Place.namelist_w_lang(record['name']))
            if record['coord']:
                p.coord = Point(record['coord']).coord
            p.uppers = combine_places(record['upper'])
            p.lowers = combine_places(record['lower'])
            ret.append(p)
        # REturn sorted by first name in the list p.pname
        return sorted(ret, key=lambda x:x.pname[0])

    @staticmethod
    def namelist_w_lang(field):
        """ Muodostetaan nimien luettelo jossa on mahdolliset kielikoodit
            mainittuna.
            Jos sarakkeessa field[1] on mainittu kielikoodi
            se lisätään kunkin nimen field[0] perään suluissa
        #TODO Lajiteltava kielen mukaan jotenkin
        """
        names = []
        for n in sorted(field, key=lambda x:x[1]):
            if n[1]:
                # Name with langiage code
                names.append("{} ({})".format(n[0], n[1]))
            else:
                names.append(n[0])
        return names


    @staticmethod
    def get_place_tree(locid):
        """ Haetaan koko paikkojen ketju paikan locid ympärillä
            Palauttaa listan paikka-olioita ylimmästä alimpaan.
            Jos hierarkiaa ei ole, listalla on vain oma Place.

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
MATCH x= (p:Place)<-[r:HIERARCY*]-(i:Place) WHERE ID(p) = $locid
    RETURN NODES(x) AS nodes, SIZE(r) AS lv, r
    UNION
MATCH x= (p:Place)-[r:HIERARCY*]->(i:Place) WHERE ID(p) = $locid
    RETURN NODES(x) AS nodes, SIZE(r)*-1 AS lv, r
"""
        # Query for single Place without hierarcy
        root_query = """
MATCH (p:Place) WHERE ID(p) = $locid
RETURN p.type AS type, p.pname AS name
"""
        # Query to get names for a Place
        name_query="""
MATCH (l:Place)-->(n:Place_name) WHERE ID(l) = $locid
RETURN COLLECT([n.name, n.lang]) AS names LIMIT 15
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
                                   data={'type': record["type"]})
        ret = []
        for node in t.tree.expand_tree(mode=t.tree.DEPTH):
            print ("{} {} {}".format(t.tree.depth(t.tree[node]), t.tree[node],
                                     t.tree[node].bpointer))
            if node != 0:
                n = t.tree[node]

                # Get all names
                with shareds.driver.session() as session:
                    result = session.run(name_query, locid=node)
                    record = result.single()
                    # Kysely palauttaa esim. [["Svartholm","sv"],["Svartholma",""]]
                    # josta tehdään ["Svartholm (sv)","Svartholma"]
                    names = Place.namelist_w_lang(record['names'])

                p = Place(uniq_id=node, ptype=n.data['type'], \
                          pname=names, level=t.tree.depth(n))
                print ("# {}".format(p))
                p.parent = n.bpointer
                ret.append(p)
        return ret


    @staticmethod
    def get_place_events(loc_id):
        """ Haetaan paikkaan liittyvät tapahtumat sekä
            osallisen henkilön nimitiedot.

        Palauttaa esimerkin mukaiset tiedot:
        ╒═════╤═════════╤═══════════════════╤═══════════╤═══════════════════╕
        │"uid"│"role"   │"names"            │"etype"    │"edates"           │
        ╞═════╪═════════╪═══════════════════╪═══════════╪═══════════════════╡
        │66953│"Primary"│[["Birth Name","Jan│"Residence"│[2,1858752,1858752]│
        │     │         │ Erik","Mannerheim"│           │                   │
        │     │         │,"Jansson"]]       │           │                   │
        └─────┴─────────┴───────────────────┴───────────┴───────────────────┘
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
            e.names = record["names"]   # tuples [name_type, given_name, surname]
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
        if self.pname != '':
            print ("Pname: " + self.pname)
        if self.coord:
            print ("Coord: {}".format(self.coord))
        if self.placeref_hlink != '':
            print ("Placeref_hlink: " + self.placeref_hlink)
        if len(self.noteref_hlink) > 0:
            for i in range(len(self.noteref_hlink)):
                print ("Noteref_hlink: " + self.noteref_hlink[i])
        return True


    def save(self, tx):
        """ Saves a Place with Place_names and hierarchy links """

        p_attr = {}
        try:
            p_attr = {"handle": self.handle,
                      "change": self.change,
                      "id": self.id,
                      "type": self.type,
                      "pname": self.pname}
            if self.coord:
                # If no coordinates, don't set coord attribute
                p_attr.update({"coord": self.coord.get_coordinates()})
            result = tx.run(Cypher_place_w_handle.create, p_attr=p_attr)
            self.uniq_id = result.single()[0]
        except Exception as err:
            print("iError Place.create: {0} attr={}".format(err, p_attr), file=stderr)

        try:
            for i in range(len(self.names)):
                #TODO: Check, if this name exists; then update or create new
                n_attr = {"name": self.names[i].name,
                          "lang": self.names[i].lang}
                if self.names[i].dates:
                    # If date information, add datetype, date1 and date2
                    n_attr.update(self.names[i].dates.for_db())
                tx.run(Cypher_place_w_handle.add_name,
                       handle=self.handle, n_attr=n_attr)
        except Exception as err:
            print("iError Place.add_name: {0}".format(err), file=stderr)

        # Make hierarchy relations to upper Place nodes
        for upper in self.surround_ref:
            try:
                print("upper {} -> {}".format(self, upper))
                if 'dates' in upper and isinstance(upper['dates'], DateRange):
                    r_attr = upper['dates'].for_db()
                else:
                    r_attr = {}
                tx.run(Cypher_place_w_handle.link_hier,
                       handle=self.handle, hlink=upper['hlink'], r_attr=r_attr)
            except Exception as err:
                print("iError Place.link_hier: {0}".format(err), file=stderr)

        # Make place note relations
        if len(self.noteref_hlink) > 0:
            for i in range(len(self.noteref_hlink)):
                try:
                    tx.run(Cypher_place_w_handle.link_note,
                           handle=self.handle, hlink=self.noteref_hlink[i])
                except Exception as err:
                    print("iError Place.link_note: {0}".format(err), file=stderr)

        return


class Place_name:
    """ Paikan nimi

        Properties:
                name             str nimi
                lang             str kielikoodi
                dates            DateRange aikajakso
    """

    def __init__(self):
        """ Luo uuden name-instanssin """
        self.name = ''
        self.lang = ''
        self.dates = None

    def __str__(self):
        if self.dates:
            d = "/" + str(self.dates)
        else:
            d = ""
        if self.lang != '':
            return "'{}' ({}){}".format(self.name, self.lang, d)
        else:
            return "'{}'{}".format(self.name, d)

    @classmethod
    def from_node(cls, node):
        ''' models.gen.place.Place_name.from_node
        Transforms a db node to an object of type Place_name.
        
        <Node id=78278 labels={'Place_name'} 
            properties={'lang': '', 'name': 'Kangasalan srk'}>
        '''
        pn = cls()  # Place_name()
        pn.uniq_id = node.id
        pn.name = node['name']
        pn.lang = node['lang'] or ''
        pn.dates = node['dates'] or None
        return pn


class Point:
    """ Paikan koordinaatit

        Properties:
            coord   coordinates of the point as list [lat, lon]
                    (north, east directions in degrees)
    """

    def __init__(self,  lon,  lat=None):
        """ Create a new Point instance.
            Arguments may be:
            - lon(float), lat(float)    - real coordinates
            - lon(str), lat(str)        - coordinates to be converted
            - [lon, lat]                - ready coordinate vector (list of tuple)
            Returns coordinate vector (if anybody needs it)
        """
        self.coord = None
        try:
            if isinstance(lon, (list, tuple)):
                # is (lon, lat) or [lon, lat]
                if len(lon) >= 2 and \
                        isinstance(lon[0], float) and isinstance(lon[1], float):
                    self.coord = list(lon)    # coord = [lat, lon]
                else:
                    raise(ValueError, "Point({}) are not two floats".format(lon))
            else:
                self.coord = [lon, lat]

            # Now the arguments are in self.coord[0:1]

            ''' If coordinate value is string, the characters '°′″'"NESWPIEL'
                and '\' are replaced by space and the comma by dot with this table.
                (These letters stand for North, East, ... Pohjoinen, Itä ...)
            '''
            point_coordinate_tr = str.maketrans(',°′″\\\'"NESWPIEL', '.              ')

            for i in list(range(len(self.coord))):   # [0,1]
                # If a coordinate is float, it's ok
                x = self.coord[i]
                if not isinstance(x, float):
                    if not x:
                        raise ValueError("Point arg empty ({})".format(self.coord))
                    if isinstance(x, str):
                        # String conversion to float:
                        #   example "60° 37' 34,647N" gives ['60', '37', '34.647']
                        #   and "26° 11\' 7,411"I" gives
                        a = x.translate(point_coordinate_tr).split()
                        if not a:
                            raise ValueError("Point arg error {}".format(self.coord))
                        degrees = float(a[0])
                        if len(a) > 1:
                            if len(a) == 3:     # There are minutes and second
                                minutes = float(a[1])
                                seconds = float(a[2])
                                self.coord[i] = degrees + minutes/60. + seconds/3600.
                            else:               # There are no seconds
                                minutes = float(a[1])
                                self.coord[i] = degrees + minutes/60.
                        else:                   # Only degrees
                                self.coord[i] = degrees
                    else:
                        raise ValueError("Point arg type is {}".format(self.coord[i]))
        except:
            raise

    def __str__(self):
        if self.coord:
            return "({:0.4f}, {:0.4f})".format(self.coord[0], self.coord[1])
        else:
            return ""

    def get_coordinates(self):
        """ Return the Point coordinates as list (leveys- ja pituuspiiri) """

        return self.coord


