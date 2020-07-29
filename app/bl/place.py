'''
    Placeclasses: Place, PlaceBl, SPlaceReader and PlaceName.

    - Place        represents Place Node in database
    - PlaceBl      represents Place and connected data (was Place_combo)
    - PlaceReader  has methods for reading Place and connected data
                   called from ui routes.py

Created on 11.3.2020 in bl.place
@author: jm

Created on 2.5.2017 from Ged-prepare/Bus/classes/genealogy.py
@author: jm

Todo:
    Miten paikkakuntiin saisi kokoluokituksen? Voisi näyttää sopivan zoomauksen karttaan
    1. _Pieniä_ talo, kortteli, tontti, tila,  rakennus
    2. _Keskikokoisia_ kylä, kaupunginosa, pitäjä, kaupunki, 
    3. _Suuria_ maa, osavaltio, lääni
    - Loput näyttäisi keskikokoisina

'''
import traceback
import logging 
logger = logging.getLogger('stkserver')

from .base import NodeObject, Status
from pe.db_reader import DBreader
#from .place_coordinates import Point


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


    @staticmethod
    def find_default_names(names:list, use_langs:list):
        ''' Select default names for listed use_langs list.

            Rules for name selection
            - if a Place_name with given lang ('if') is found, use it
            - else if a Place_name with no lang ('') is found, use it
            - else use any name
        '''
        if not names:
            return None
        selection = {}
        #print(f'# ---- Place {names[0].name}')
        try:
            # 1.     find matching languages for use_langs
            for lang in use_langs:
                for name in names:
                    if name.lang == lang:
                        # A matching language
                        #print(f'# select {lang}: {name.name} {name.uniq_id}')
                        selection[lang] = name.uniq_id
#                   elif lang == 'fi': print(f'#           {name}')
            # 2. find replacing languages, if not matching
            for lang in use_langs:
                if not lang in selection.keys():
                    # Maybe a missing language is found?
                    for name in names:
                        if name.lang == '' and not lang in selection.keys():
                            #print(f'# select {lang}>{name.lang}: {name.name} {name.uniq_id}')
                            selection[lang] = name.uniq_id
                if not lang in selection.keys():
                    # No missing language, select any
                    for name in names:
                        if  not lang in selection.keys():
                            #print(f'# select {lang}>{name.lang}: {name.name} {name.uniq_id}')
                            selection[lang] = name.uniq_id
    
            ret = {}
            for lang in use_langs:
                ret[lang] = selection[lang]
            return ret

        except Exception as e:
            logger.error(f"bl.place.PlaceBl.find_default_names {selection}: {e}")
        return

class PlaceReader(DBreader):
    '''
        Data reading class for Place objects with associated data.

        - Use pe.db_reader.DBreader.__init__(self, dbdriver, u_context) 
          to define the database driver and user context

        - Returns a Result object which includes the tems and eventuel error object.
    '''
#     def get_list(u_context):    # @staticmethod --> pe.db_reader.DBreader.place_list
#         """ Get a list on PlaceBl objects with nearest heirarchy neighbours.

    def get_list(self):
        """ Get a list on PlaceBl objects with nearest heirarchy neighbours.
        
            Haetaan paikkaluettelo ml. hierarkiassa ylemmät ja alemmat
    """
        context = self.user_context
        fw = context.next_name_fw()
        places = self.dbdriver.dr_get_place_list_fw(self.use_user, fw, context.count, 
                                                    lang=context.lang)

        # Update the page scope according to items really found 
        if places:
            context.update_session_scope('place_scope', 
                                          places[0].pname, places[-1].pname, 
                                          context.count, len(places))
        place_result = {'items':places, 'status':Status.OK}
        return place_result


    def get_with_events(self, uuid):
        """ Read the place hierarchy and events connected to this place.
        
            Luetaan aneettuun paikkaan liittyvä hierarkia ja tapahtumat
            Palauttaa paikkahierarkian ja (henkilö)tapahtumat.
    
        """
        # Get a Place with Names, Notes and Medias
        res = self.dbdriver.dr_get_place_w_names_notes_medias(self.use_user, uuid, 
                                                              self.user_context.lang)
        place = res.get("place")
        results = {"place":place, 'status':Status.OK}

        if not place:
            results = {'status':Status.ERROR, 'statustext':
                       f'get_with_events:{self.use_user} - no Place with uuid={uuid}'}
            return results
        
        #TODO: Find Citation -> Source -> Repository for each uniq_ids
        try:
            results['hierarchy'] = \
                self.dbdriver.dr_get_place_tree(place.uniq_id, lang=self.user_context.lang)

        except AttributeError as e:
            traceback.print_exc()
            results['status'] = Status.ERROR
            results['statustext'] = f"Place tree for {place.uniq_id}: {e}"
            return results
        except ValueError as e:
            results['status'] = Status.ERROR
            results['statustext'] = f"Place tree for {place.uniq_id}: {e}"
            traceback.print_exc()

        res = self.dbdriver.dr_get_place_events(place.uniq_id)
        results['events'] = res['items']
        return results



class PlaceBl(Place):
    """ Place / Paikka:

        Properties, might be defined in here:
                names[]             PlaceName default name first
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
        self.ref_cnt = None     # for display: count of referencing objects


    @staticmethod
    def combine_places(pn_tuples, lang):
        """ Creates a list of Places with names combined from given names.
        
            The pl_tuple has Places data as a tuple [[28101, "City", "Lovisa", "sv"]].

            Jos sama Place esiintyy uudestaan, niiden nimet yhdistetään.
            Jos nimeen on liitetty kielikoodi, se laitetaan sulkuihin mukaan.
            
            TODO. Lajittele paikannimet kielen mukaan (si, sv, <muut>, "")
                  ja aakkosjärjestykseen
        """
        placedict = {}
        for nid, nuuid, ntype, name, nlang in pn_tuples:
            if nid: # id of a lower place
                pn = PlaceName(name=name, lang=nlang)
                if nid in placedict:
                    # Append name to existing PlaceBl
                    placedict[nid].names.append(pn)
                    placedict[nid].names.sort()
                else:
                    # Add a new PlaceBl
                    p = PlaceBl(nid)
                    p.uuid = nuuid
                    p.type = ntype
                    p.names.append(pn)
                    placedict[nid] = p
        place_list = list(placedict.values())
        for p in place_list:
            p.names = PlaceName.arrange_names(p.names, lang)
            p.pname = p.names[0]
        return place_list

#     def set_place_names_from_nodes(self, nodes): --> ui.place.place_names_from_nodes
#         ''' Filter user language Name objects from a list of Cypher nodes to self.names.
#         self.names = place_names_from_nodes(nodes)


class PlaceName(NodeObject):
    """ Paikan nimi

        Properties:
                name             str nimi
                lang             str kielikoodi
                dates            DateRange aikajakso
                order            int display order of various names of a place
    """

    def __init__(self, name='', lang=''):
        """ Luo uuden name-instanssin """
        self.name = name
        self.lang = lang
        self.dates = None
        self.order = 0

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
        ''' Transforms a db node to an object of type Place_name.
        
        <Node id=78278 labels={'Place_name'} 
            properties={'lang': '', 'name': 'Kangasalan srk'}>
        '''
        pn = cls()  # Place_name()
        pn.uniq_id = node.id
        pn.name = node.get('name', '?')
        pn.lang = node.get('lang', '')
        pn.dates = node.get('dates')
        return pn

    @staticmethod
    def arrange_names(namelist:list, lang:str=None):
        ''' Arrange Place_name objects by name usefullness.
        
            If lang attribute is present, the default language name is processed
            outside this method.
            
            Order:
            - First local names fi, sv
            - Then names without lang
            - Last other language names
        '''
        n_default = []
        n_local = []
        n_unknown = []
        n_other = []
        if lang == 'fi':   other_lang = 'sv'
        elif lang == 'sv': other_lang = 'fi'
        else:              other_lang = None
        for nm in namelist:
            if lang != None and nm.lang == lang:
                n_local.append(nm)
            elif nm.lang in ['fi', 'sv'] and nm.lang != other_lang:
                n_local.append(nm)
            elif nm.lang == '':
                n_unknown.append(nm)
            else:
                n_other.append(nm)
        return n_default + n_local + n_unknown + n_other

#     @staticmethod
#     def arrange_other_names(namelist:list):
#         ''' Arrange Place_name objects by name usefullness.
#         
#             The default language name is processed outside this method
#             - First local names fi, sv
#             - Then names without lang
#             - Last other language names
#         '''
#         n_local = []
#         n_unknown = []
#         n_other = []
#         for nm in namelist:
#             if nm.lang in ['fi', 'sv']:
#                 n_local.append(nm)
#             elif nm.lang == '':
#                 n_unknown.append(nm)
#             else:
#                 n_other.append(nm)
#         return n_local + n_unknown + n_other

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

