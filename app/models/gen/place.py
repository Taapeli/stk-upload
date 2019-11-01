'''
Created on 2.5.2017 from Ged-prepare/Bus/classes/genealogy.py

Todo:
    Miten paikkakuntiin saisi kokoluokituksen? Voisi näyttää sopivan zoomauksen karttaan
    1. _Pieniä_ talo, kortteli, tontti, tila,  rakennus
    2. _Keskikokoisia_ kylä, kaupunginosa, pitäjä, kaupunki, 
    3. _Suuria_ maa, osavaltio, lääni
    - Loput näyttäisi keskikokoisina

@author: jm
'''

import  shareds
from .base import NodeObject
from .dates import DateRange
from .cypher import Cypher_place
from .event_combo import Event_combo
from .person_name import Name

class Place(NodeObject):
    """ Place / Paikka:

        Properties:
            Defined here:
                handle
                change
                id                  esim. "P0001"
                type                str paikan tyyppi
                pname               str paikan nimi
            May be defined in Place_combo:
                names[]             PlaceName
                coord               str paikan koordinaatit (leveys- ja pituuspiiri)
                surrounding[]       int uniq_ids of upper
                note_ref[]          int uniq_ids of Notes
            May be defined in Place_gramps:
                surround_ref[]      dictionaries {'hlink':handle, 'dates':dates}
                citation_ref[]      int uniq_ids of Citations
                placeref_hlink      str paikan osoite
                noteref_hlink       str huomautuksen osoite (tulostuksessa Note-olioita)
     """

    def __init__(self, uniq_id=None):
        """ Creates a new Place instance.
        """
        NodeObject.__init__(self)
        self.uniq_id = uniq_id
        self.type = ''
        self.names = []
        self.pname = ''
        self.coord = None
        
# These are in bp.gramps.models.place_gramps.Place_gramps.__init__
#         self.uppers = []        # Upper place objects for hirearchy display
#         self.notes = []         # Notes connected to this place
#         self.note_ref = []      # uniq_ids of Notes

# These are in bp.gramps.models.place_gramps.Place_gramps.__init__
#         self.surround_ref = []  # members are dictionaries {'hlink':hlink, 'dates':dates}
#         self.noteref_hlink = []


    def __str__(self):
        return f"{self.uniq_id} {self.pname} ({self.type})"


    @classmethod
    def from_node(cls, node):
        ''' Creates a node object of type Place from a Neo4j node.
        
        models.gen.place.Place.from_node. 
        
        Example node:
        <Node id=78279 labels={'Place'} 
            properties={'handle': '_da68e12a415d936f1f6722d57a', 'id': 'P0002', 
                'change': 1500899931, 'pname': 'Kangasalan srk', 'type': 'Parish'}>

        '''
        p = cls()
        p.uniq_id = node.id
        p.uuid = node['uuid']
        p.handle = node['handle']
        p.change = node['change']
        p.id = node['id'] or ''
        p.type = node['type'] or ''
        p.pname = node['pname'] or ''
        p.coord = node['coord'] or None
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


#     def read_w_notes(self): # See: Place_combo.get_w_notes()
#         """ Luetaan kaikki paikan tiedot ml. nimivariaatiot (tekstinä)

#     @staticmethod def get_my_places():    # Use: Place_combo.get_my_places()
#         """ Luetaan kaikki paikat kannasta
#         """

#     @staticmethod get_place_hierarchy(), see Place_combo.get_place_hierarchy()
#         """ Haetaan paikkaluettelo ml. hierarkiassa ylemmät ja alemmat
#             Place list with upper and lower places in herarchy


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


#     @staticmethod get_place_tree(locid):
#         """ Haetaan koko paikkojen ketju paikan locid ympärillä
#             Palauttaa listan paikka-olioita ylimmästä alimpaan.


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
            # <Record uid=414999 role='Primary' 
            #  names=[
            #    <Node id=415001 labels={'Name'} 
            #        properties={'firstname': 'Esajas', 'type': 'Also Known As', 
            #            'suffix': '', 'prefix': '', 'surname': 'Hildeen', 'order': 1}>, 
            #    <Node id=415000 labels={'Name'} 
            #        properties={'firstname': 'Esaias', 'type': 'Birth Name', 
            #            'suffix': '', 'prefix': '', 'surname': 'Hildén', 'order': 0}>] 
            #  etype='Baptism' 
            #  edates=[0, 1782139, 1782139]>

            e = Event_combo()
            # Fields uid (person uniq_id) and names are on standard in Event_combo
            e.uid = record["uid"]
            e.type = record["etype"]
            if record["edates"][0] != None:
                e.dates = DateRange(record["edates"])
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
        if self.pname != '':
            print ("Pname: " + self.pname)
        if self.coord:
            print ("Coord: {}".format(self.coord))
        return True


#     save() - see PlaceGramps.save()
#     def save(self, tx):
#         """ Saves a Place with Place_names and hierarchy links """
# 
#         p_attr = {}
#         try:
#             p_attr = {"handle": self.handle,
#                       "change": self.change,
#                       "id": self.id,
#                       "type": self.type,
#                       "pname": self.pname}
#             if self.coord:
#                 # If no coordinates, don't set coord attribute
#                 p_attr.update({"coord": self.coord.get_coordinates()})
#             result = tx.run(Cypher_place_w_handle.create, p_attr=p_attr)
#             self.uniq_id = result.single()[0]
#         except Exception as err:
#             print("iError Place.create: {0} attr={}".format(err, p_attr), file=stderr)
# 
#         try:
#             for i in range(len(self.names)):
#                 #TODO: Check, if this name exists; then update or create new
#                 n_attr = {"name": self.names[i].name,
#                           "lang": self.names[i].lang}
#                 if self.names[i].dates:
#                     # If date information, add datetype, date1 and date2
#                     n_attr.update(self.names[i].dates.for_db())
#                 tx.run(Cypher_place_w_handle.add_name,
#                        handle=self.handle, n_attr=n_attr)
#         except Exception as err:
#             print("iError Place.add_name: {0}".format(err), file=stderr)
#
#         # Make place note relations
#         for i in range(len(self.noteref_hlink)):
#             try:
#                 tx.run(Cypher_place_w_handle.link_note,
#                        handle=self.handle, hlink=self.noteref_hlink[i])
#             except Exception as err:
#                 print("iError Place.link_note: {0}".format(err), file=stderr)
# 
#         return


class Place_name:
    """ Paikan nimi

        Properties:
                name             str nimi
                lang             str kielikoodi
                dates            DateRange aikajakso
    """

    def __init__(self, name='', lang=''):
        """ Luo uuden name-instanssin """
        self.name = name
        self.lang = lang
        self.dates = None

    def __str__(self):
        if self.dates:
            d = "/" + str(self.dates)
        else:
            d = ""
        if self.lang != '':
            return f"'{self.name}' ({self.lang}){d}"
        else:
            return f"'{self.name}'{d}"

    @classmethod
    def from_node(cls, node):
        ''' models.gen.place.Place_name.from_node
        Transforms a db node to an object of type Place_name.
        
        <Node id=78278 labels={'Place_name'} 
            properties={'lang': '', 'name': 'Kangasalan srk'}>
        '''
        pn = cls()  # Place_name()
        pn.uniq_id = node.id
        pn.name = node.get('name', '?')
        pn.lang = node.get('lang', '')
        pn.dates = node.get('dates')
        return pn


class Point:
    """ Paikan koordinaatit

        Properties:
            coord   coordinates of the point as list [lat, lon]
                    (north, east directions in degrees)
    """
    _point_coordinate_tr = str.maketrans(',°′″\\\'"NESWPIEL', '.              ')


    def __init__(self,  lon,  lat=None):
        """ Create a new Point instance.
            Arguments may be:
            - lon(float), lat(float)    - real coordinates
            - lon(str), lat(str)        - coordinates to be converted
            - [lon, lat]                - ready coordinate vector (list or tuple)
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
                        a = x.translate(self._point_coordinate_tr).split()
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


