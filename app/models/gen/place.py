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
from bl.base import NodeObject
from bl.place import PlaceName

#from .dates import DateRange
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
                media_ref[]         int uniq_ids of Medias
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
                plname = PlaceName.from_node(node)
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


#     def get_place_events(loc_id): @staticmethod --> pe.neo4j.reader.Neo4jDriver.dr_get_place_events
#         """ Haetaan paikkaan liittyvät tapahtumat sekä
#             osallisen henkilön nimitiedot.


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


# class Place_name(): --> bl.place.PlaceName
#     """ Paikan nimi
# 
#         Properties:
#                 name             str nimi
#                 lang             str kielikoodi
#                 dates            DateRange aikajakso
#     """
# 
#     def __init__(self, name='', lang=''):
#         """ Luo uuden name-instanssin """
#         self.name = name
#         self.lang = lang
#         self.dates = None
# 
#     def __str__(self):
#         if self.dates:
#             d = "/" + str(self.dates)
#         else:
#             d = ""
#         if self.lang != '':
#             return f"'{self.name}' ({self.lang}){d}"
#         else:
#             return f"'{self.name}'{d}"
# 
#     @classmethod
#     def from_node(cls, node):
#         ''' models.gen.place.Place_name.from_node
#         Transforms a db node to an object of type Place_name.
#         
#         <Node id=78278 labels={'Place_name'} 
#             properties={'lang': '', 'name': 'Kangasalan srk'}>
#         '''
#         pn = cls()  # Place_name()
#         pn.uniq_id = node.id
#         pn.name = node.get('name', '?')
#         pn.lang = node.get('lang', '')
#         pn.dates = node.get('dates')
#         return pn
# 
#     def _lang_key(self, obj):
#         ''' Name comparison key by 1) language, 2) name '''
#         lang_order = {'fi':'0', 'sv':'1', 'vi': '2', 'de':'3', 'la':'4', 'ru':'5', '':'6'}
#         if obj:
#             if obj.lang in lang_order.keys():
#                 return lang_order[obj.lang] + ':' + obj.name
#             return 'x:' + obj.name
#         return ""
# 
#     def __lt__(self, other):
#         a = self._lang_key(self)
#         b = self._lang_key(other)
#         return a < b
#         #return self._lang_key(self) < self.lang_key(other)
#     def __le__(self, other):        return self._lang_key(self) <= self.lang_key(other)
#     def __eq__(self, other):        return self._lang_key(self) == self.lang_key(other)
#     def __ge__(self, other):        return self._lang_key(self) >= self.lang_key(other)
#     def __gt__(self, other):        return self._lang_key(self) > self.lang_key(other)
#     def __ne__(self, other):        return self._lang_key(self) != self.lang_key(other)


# class Point: --> bl.place_coordinates.Point
#     """ Paikan koordinaatit
# 
#         Properties:
#             coord   coordinates of the point as list [lat, lon]
#                     (north, east directions in degrees)
#     """
#     _point_coordinate_tr = str.maketrans(',°′″\\\'"NESWPIEL', '.              ')
# 
# 
#     def __init__(self,  lon,  lat=None):
#         """ Create a new Point instance.
#             Arguments may be:
#             - lon(float), lat(float)    - real coordinates
#             - lon(str), lat(str)        - coordinates to be converted
#             - [lon, lat]                - ready coordinate vector (list or tuple)
#         """
#         self.coord = None
#         try:
#             if isinstance(lon, (list, tuple)):
#                 # is (lon, lat) or [lon, lat]
#                 if len(lon) >= 2 and \
#                         isinstance(lon[0], float) and isinstance(lon[1], float):
#                     self.coord = list(lon)    # coord = [lat, lon]
#                 else:
#                     raise(ValueError, "Point({}) are not two floats".format(lon))
#             else:
#                 self.coord = [lon, lat]
# 
#             # Now the arguments are in self.coord[0:1]
# 
#             ''' If coordinate value is string, the characters '°′″'"NESWPIEL'
#                 and '\' are replaced by space and the comma by dot with this table.
#                 (These letters stand for North, East, ... Pohjoinen, Itä ...)
#             '''
# 
#             for i in list(range(len(self.coord))):   # [0,1]
#                 # If a coordinate is float, it's ok
#                 x = self.coord[i]
#                 if not isinstance(x, float):
#                     if not x:
#                         raise ValueError("Point arg empty ({})".format(self.coord))
#                     if isinstance(x, str):
#                         # String conversion to float:
#                         #   example "60° 37' 34,647N" gives ['60', '37', '34.647']
#                         #   and "26° 11\' 7,411"I" gives
#                         a = x.translate(self._point_coordinate_tr).split()
#                         if not a:
#                             raise ValueError("Point arg error {}".format(self.coord))
#                         degrees = float(a[0])
#                         if len(a) > 1:
#                             if len(a) == 3:     # There are minutes and second
#                                 minutes = float(a[1])
#                                 seconds = float(a[2])
#                                 self.coord[i] = degrees + minutes/60. + seconds/3600.
#                             else:               # There are no seconds
#                                 minutes = float(a[1])
#                                 self.coord[i] = degrees + minutes/60.
#                         else:                   # Only degrees
#                                 self.coord[i] = degrees
#                     else:
#                         raise ValueError("Point arg type is {}".format(self.coord[i]))
#         except:
#             raise
# 
#     def __str__(self):
#         if self.coord:
#             return "({:0.4f}, {:0.4f})".format(self.coord[0], self.coord[1])
#         else:
#             return ""
# 
#     def get_coordinates(self):
#         """ Return the Point coordinates as list (leveys- ja pituuspiiri) """
# 
#         return self.coord


