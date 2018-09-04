'''
Created on 2.5.2017 from Ged-prepare/Bus/classes/genealogy.py

@author: jm
'''

from sys import stderr
#import logging
#from flask import g
from models.dbtree import DbTree
from models.gen.weburl import Weburl
from models.gen.note import Note
from models.gen.dates import DateRange
from models.gen.cypher import Cypher_place
from models.cypher_gramps import Cypher_place_w_handle
import  shareds

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
                urls[]:
                    priv            str url salattu tieto
                    href            str url osoite
                    type            str url tyyppi
                    description     str url kuvaus
                placeref_hlink      str paikan osoite
                noteref_hlink       str huomautuksen osoite (tulostuksessa Note-olioita)
    #TODO: urls[] list should contain Weburl instances
     """

    def __init__(self, locid="", ptype="", pname="", level=None):
        """ Luo uuden place-instanssin.
            Argumenttina voidaan antaa valmiiksi paikan uniq_id, tyylin, nimen
            ja (tulossivua varten) mahdollisen hierarkiatason
        """
        self.id = locid
        self.type = ptype
        self.pname = pname
        if level != None:
            self.level = level
        # Gramps-tietoja
        self.handle = ''
        self.change = 0
        self.names = []
        self.coord = None
        self.urls = []          # Weburl instance list

        self.surround_ref = []  # members are dictionaries {'hlink':hlink, 'dates':dates}
        self.noteref_hlink = []


    def __str__(self):
        try:
            lv = self.level
        except:
            lv = ""
        desc = "Place {}: {} ({}) {}".format(self.id, self.pname, self.type, lv)
        return desc


    def get_place_data_by_id(self):
        """ Luetaan kaikki paikan tiedot ml. nimivariaatiot (tekstinä)
            Nimivariaatiot talletetaan kenttään pname,
            esim. [["Svartholm", "sv"], ["Svartholma", None]]
            #TODO: Ei hieno, po. Place_name objects!
        """
        plid = self.uniq_id
        query = """
MATCH (place:Place)-[:NAME]->(n:Place_name)
    WHERE ID(place)=$place_id
OPTIONAL MATCH (place)-[wu:WEBURL]->(url:Weburl)
OPTIONAL MATCH (place)-[nr:NOTE]->(note:Note)
RETURN place, COLLECT([n.name, n.lang]) AS names,
    COLLECT (DISTINCT url) AS urls, COLLECT (DISTINCT note) AS notes
        """
        place_result = shareds.driver.session().run(query, place_id=plid)

        for place_record in place_result:
            self.change = place_record["place"]["change"]
            self.id = place_record["place"]["id"]
            self.type = place_record["place"]["type"]
            names = place_record["names"]
            self.pname = Place.namelist_w_lang(names)
            self.coord = place_record["place"]["coord"]

            urls = place_record['urls']
            for url in urls:
                weburl = Weburl()
                weburl.href = url["href"]
                weburl.type = url["type"]
                weburl.priv = url["priv"]
                weburl.description = url["description"]
                self.urls.append(weburl)

            notes = place_record['notes']
            for note in notes:
                n = Note()
                n.priv = note["priv"]
                n.type = note["type"]
                n.text = note["text"]
                self.noteref_hlink.append(n)

        return True


    @staticmethod
    def get_places():
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
                data_line.append(record["p"]['change'])
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
    def get_place_names():
        """ Haetaan paikkaluettelo ml. hierarkiassa ylemmät ja alemmat

            Esim.
╒═══════╤════════════╤══════════════════════════════╤═════════════════════════╤═══════════════════════╤═══════════════════════╕
│"id"   │"type"      │"name"                        │"coord"                  │"upper"                │"lower"                │
╞═══════╪════════════╪══════════════════════════════╪═════════════════════════╪═══════════════════════╪═══════════════════════╡
│"28427"│"Building"  │[["Ahlnäs",""]]               │""                       │[["28419","Farm",      │[[null,null,null,null]]│
│       │            │                              │                         │"Labby 6 Smeds",""]]   │                       │
├───────┼────────────┼──────────────────────────────┼─────────────────────────┼───────────────────────┼───────────────────────┤
│"28795"│"Hautausmaa"│[["Ahveniston hautausmaa",""]]│"[24.4209, 60.9895]"     │[[null,null,null,null]]│[[null,null,null,null]]│
├───────┼────────────┼──────────────────────────────┼─────────────────────────┼───────────────────────┼───────────────────────┤
│"28118"│"Farm"      │[["Ainola",""]]               │"25.0873870, 60.453655]" │[[null,null,null,null]]│[[null,null,null,null]]│
├───────┼────────────┼──────────────────────────────┼─────────────────────────┼───────────────────────┼───────────────────────┤
│"28865"│"City"      │[["Akaa",""],["Ackas","sv"]]  │"23.9481353, 61.1881064]"│[[null,null,null,null]]│[[null,null,null,null]]│
├───────┼────────────┼──────────────────────────────┼─────────────────────────┼───────────────────────┼───────────────────────┤
│"28354"│"Building"  │[["Alnäs",""]]                │""                       │[["28325","Farm","Inger│[[null,null,null,null]]│
│       │            │                              │                         │mansby 4 Sjökulla",""],│                       │
│       │            │                              │                         │["28325","Farm", "Lappt│                       │
│       │            │                              │                         │räsk Ladugård",""]]    │                       │
└───────┴────────────┴──────────────────────────────┴─────────────────────────┴───────────────────────┴───────────────────────┘
"""

        query = """
MATCH (a:Place) -[:NAME]-> (pn:Place_name)
OPTIONAL MATCH (a:Place) -[:HIERARCY]-> (up:Place) -[:NAME]-> (upn:Place_name)
OPTIONAL MATCH (a:Place) <-[:HIERARCY]- (do:Place) -[:NAME]-> (don:Place_name)
RETURN ID(a) AS id, a.type AS type,
    COLLECT(DISTINCT [pn.name, pn.lang]) AS name, a.coord AS coord,
    COLLECT(DISTINCT [ID(up), up.type, upn.name, upn.lang]) AS upper,
    COLLECT(DISTINCT [ID(do), do.type, don.name, don.lang]) AS lower
ORDER BY name[0][0]
"""

        def combine_places(field):
            """ Kenttä field sisältää Places-tietoja tuplena [[28101, "City",
                "Lovisa", "sv"]].
                Jos sama Place esiintyy uudestaan, niiden nimet yhdistetään.
                Jos nimeen on liitetty kielikoodi, se laitetaan sulkuihin mukaan.
            """
            namedict = {}
            for near in field:
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
        result = shareds.driver.session().run(query)
        for record in result:
            # Luodaan paikka ja siihen taulukko liittyvistä hierarkiassa lähinnä
            # alemmista paikoista
            p = Place(record['id'], record['type'], Place.namelist_w_lang(record['name']))
            if record['coord']:
                p.coord = Point(record['coord']).coord
            p.uppers = combine_places(record['upper'])
            p.lowers = combine_places(record['lower'])
            ret.append(p)
        return ret

    @staticmethod
    def namelist_w_lang(field):
        """ Muodostetaan nimien luettelo jossa on mahdolliset kielikoodit
            mainittuna.
            Jos sarakkeessa field[1] on mainittu kielikoodi
            se lisätään kunkin nimen field[0] perään suluissa
        #TODO Lajiteltava kielen mukaan jotenkin
        """
        names = []
        for n in field:
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

                p = Place(locid=node, ptype=n.data['type'], \
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
            p = Place()
            p.uid = record["uid"]
            p.etype = record["etype"]
            if record["edates"][0] == None:
                dates = None
                p.edates = ""   # Normal: "24.3.1861"
                p.date = ""     # Normal: "1861-03-24"
            else:
                dates = DateRange(record["edates"])
                p.edates = str(dates)
                p.date = dates.estimate()
            p.role = record["role"]
            p.names = record["names"]   # tuples [name_type, given_name, surname]
            ret.append(p)
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

        try:
            p_attr = {"handle": self.handle,
                      "change": self.change,
                      "id": self.id,
                      "type": self.type,
                      "pname": self.pname}
            if self.coord:
                # If no coordinates, don't set coord attribute
                p_attr.update({"coord": self.coord.get_coordinates()})
            tx.run(Cypher_place_w_handle.create, p_attr=p_attr)
        except Exception as err:
            print("Virhe Place.create: {0}".format(err), file=stderr)

        if len(self.names) >= 1:
            try:
                for i in range(len(self.names)):
                    n_attr = {"name": self.names[i].name,
                              "lang": self.names[i].lang}
                    if self.names[i].dates:
                        # If date information, add datetype, date1 and date2
                        n_attr.update(self.names[i].dates.for_db())
                    tx.run(Cypher_place_w_handle.add_name,
                           handle=self.handle, n_attr=n_attr)
            except Exception as err:
                print("Virhe Place.add_name: {0}".format(err), file=stderr)

        # Talleta Weburl nodet ja linkitä paikkaan
        if len(self.urls) > 0:
            for url in self.urls:
                try:
                    tx.run(Cypher_place_w_handle.link_weburl,
                           handle=self.handle, 
                           url_priv=url.priv, url_href=url.href,
                           url_type=url.type, url_description=url.description)
                except Exception as err:
                    print("Virhe (Place.save:create Weburl): {0}".format(err), file=stderr)

        # Make hierarchy relations to upper Place nodes
        for upper in self.surround_ref:
            try:
                if 'dates' in upper and upper['dates'] != None:
                    r_attr = upper['dates'].for_db()
                else:
                    r_attr = {}
                tx.run(Cypher_place_w_handle.link_hier,
                       handle=self.handle, hlink=upper['hlink'], r_attr=r_attr)
            except Exception as err:
                print("Virhe Place.link_hier: {0}".format(err), file=stderr)

        # Make place note relations
        if len(self.noteref_hlink) > 0:
            for i in range(len(self.noteref_hlink)):
                try:
                    tx.run(Cypher_place_w_handle.link_note,
                           handle=self.handle, hlink=self.noteref_hlink[i])
                except Exception as err:
                    print("Virhe Place.link_note: {0}".format(err), file=stderr)

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
            return "{} ({}){}".format(self.name, self.lang, d)
        else:
            return "{}{}".format(self.name, d)


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
                    if isinstance(x, str):
                        # String conversion to float:
                        #   example "60° 37' 34,647N" gives ['60', '37', '34.647']
                        #   and "26° 11\' 7,411"I" gives
                        a = x.translate(point_coordinate_tr).split()
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
                        raise(ValueError, "Point arg type is {}".format(self.coord[i]))
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


