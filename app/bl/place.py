'''
Created on 11.3.2020

@author: jm
'''
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

from bl.base import NodeObject
from bl.place_coordinates import Point
from pe.neo4j.neo4j_reader import DbReader

# import shareds
# from .dates import DateRange
# from .cypher import Cypher_place
# from .event_combo import Event_combo
# from .person_name import Name

class Place(NodeObject):
    """ Place / Paikka:

        Properties:
            Defined in NodeObject:
                change
                id                  esim. "P0001"
                type                str paikan tyyppi
                pname               str paikan nimi
            May be defined in PlaceBl:
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


class PlaceBl(Place):
    """ Place / Paikka:

        Properties, might be defined in here:
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

    def __init__(self, uniq_id=None, ptype="", level=None):
        """ Creates a new PlaceBl instance.

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
        self.media_ref = []     # uniq_id of models.gen.media.Media

# 
#     @staticmethod
#     def get_list(u_context):
#         """ Get a list on PlaceBl objects with nearest heirarchy neighbours.
#         
#             Haetaan paikkaluettelo ml. hierarkiassa ylemmät ja alemmat
# 
#             Esim.
# ╒══════╤═════════╤════════════════════╤═══════╤════════════════════╤════════════════════╕
# │"id"  │"type"   │"name"              │"coord"│"upper"             │"lower"             │
# ╞══════╪═════════╪════════════════════╪═══════╪════════════════════╪════════════════════╡
# │290228│"Borough"│[{"name":"1. Kaupung│null   │[[287443,"City","Arc│[[290226,"Tontti","T│
# │      │         │inosa","lang":""}]  │       │topolis","la"],[2874│ontti 23",""]]      │
# │      │         │                    │       │43,"City","Björnebor│                    │
# │      │         │                    │       │g","sv"],[287443,"Ci│                    │
# │      │         │                    │       │ty","Pori",""],[2874│                    │
# │      │         │                    │       │43,"City","Пори","ru│                    │
# │      │         │                    │       │"]]                 │                    │
# └─────┴──────────┴────────────────────┴───────┴────────────────────┴────────────────────┘
# """
# 
#         ret = []
#         dbreader = DbReader(u_context)
#         result = dbreader.place_list()
#         for record in result:
#             # Luodaan paikka ja siihen taulukko liittyvistä hierarkiassa lähinnä
#             # alemmista paikoista
#             #
#             # Record: <Record id=290228 type='Borough' 
#             #    names=[<Node id=290235 labels={'Place_name'} 
#             #        properties={'name': '1. Kaupunginosa', 'lang': ''}>] 
#             #    coord=None
#             #    upper=[
#             #        [287443, 'City', 'Arctopolis', 'la'], 
#             #        [287443, 'City', 'Björneborg', 'sv'], 
#             #        [287443, 'City', 'Pori', ''], 
#             #        [287443, 'City', 'Пори', 'ru']] 
#             #    lower=[[290226, 'Tontti', 'Tontti 23', '']]
#             # >
#             pl_id =record['id']
#             p = PlaceBl(pl_id)
#             p.uuid =record['uuid']
#             p.type = record.get('type')
#             if record['coord']:
#                 p.coord = Point(record['coord']).coord
#             # Set place names and default display name pname
#             for nnode in record.get('names'):
#                 pn = PlaceName.from_node(nnode)
# #                 if pn.lang in ['fi', '']:
# #                     # Default language name
# #                     #TODO use language from current_user's preferences
# #                     p.pname = pn.name
#                 p.names.append(pn)
#             if len(p.names) > 1:
#                 p.names.sort()
#             if p.pname == '' and p.names:
#                 p.pname = p.names[0].name
#             p.uppers = PlaceBl._combine_places(record['upper'])
#             p.lowers = PlaceBl._combine_places(record['lower'])
#             ret.append(p)
# 
#         # Update the page scope according to items really found 
#         if ret:
#             u_context.update_session_scope('person_scope', 
#                                           ret[0].pname, ret[-1].pname, 
#                                           u_context.count, len(ret))
# 
#         # Return sorted by first name in the list p.pname
#         return sorted(ret, key=lambda x:x.names[0].name if x.names else "")

    @staticmethod
    def _combine_places(pn_tuples):
        """ Creates a list of Places with names combined from given names.
        
            The pl_tuple has Places data as a tuple [[28101, "City", "Lovisa", "sv"]].

            Jos sama Place esiintyy uudestaan, niiden nimet yhdistetään.
            Jos nimeen on liitetty kielikoodi, se laitetaan sulkuihin mukaan.
            
            TODO. Lajittele paikannimet kielen mukaan (si, sv, <muut>, "")
                  ja aakkosjärjestykseen
        """
        placedict = {}
        for nid, nuuid, ntype, name, lang in pn_tuples:
            if nid: # id of a lower place
                pn = PlaceName(name=name, lang=lang)
                if nid in placedict:
                    # Append name to existing PlaceBl
                    placedict[nid].names.append(pn)
                    placedict[nid].names.sort()
#                     if pn.lang in ['fi', '']:
#                         # Default language name
#                         #TODO use language from current_user's preferences
#                         placedict[nid].pname = pn.name
                else:
                    # Add a new PlaceBl
                    p = PlaceBl(nid)
                    p.uuid = nuuid
                    p.type = ntype
                    p.names.append(pn)
                    p.pname = pn.name
                    placedict[nid] = p
                    # ntype, PlaceBl.namelist_w_lang( (name,) ))
        li = list(placedict.values())
        ret = sorted(li, key=lambda x: x.names[0].name if x.names else "")
        return ret

#     def set_place_names_from_nodes(self, nodes): --> ui.place.place_names_from_nodes
#         ''' Filter user language Name objects from a list of Cypher nodes to self.names.
#         self.names = place_names_from_nodes(nodes)


class PlaceName():
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

    def _lang_key(self, obj):
        ''' Name comparison key by 1) language, 2) name '''
        lang_order = {'fi':'0', 'sv':'1', 'vi': '2', 'de':'3', 'la':'4', 'ru':'5', '':'6'}
        if obj:
            if obj.lang in lang_order.keys():
                return lang_order[obj.lang] + ':' + obj.name
            return 'x:' + obj.name
        return ""

    def __lt__(self, other):
        a = self._lang_key(self)
        b = self._lang_key(other)
        return a < b
        #return self._lang_key(self) < self.lang_key(other)
    def __le__(self, other):        return self._lang_key(self) <= self.lang_key(other)
    def __eq__(self, other):        return self._lang_key(self) == self.lang_key(other)
    def __ge__(self, other):        return self._lang_key(self) >= self.lang_key(other)
    def __gt__(self, other):        return self._lang_key(self) > self.lang_key(other)
    def __ne__(self, other):        return self._lang_key(self) != self.lang_key(other)

