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
import shareds

from pe.neo4j.cypher.cy_place import CypherPlace
#from bp.stk_security.models.seccypher import Cypher
logger = logging.getLogger('stkserver')

from .base import NodeObject, Status
from .media import MediaBl
#from pe.db_reader import DbReader
from bl.dates import DateRange


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
                note_handles       str huomautuksen osoite (tulostuksessa Note-olioita)
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
        p.handle = node.get('handle',None)
        p.change = node['change']
        p.id = node.get('id','')
        p.type = node.get('type','')
        p.pname = node.get('pname','')
        p.coord = node.get('coord',None)
        return p


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
                note_handles       str huomautuksen osoite (tulostuksessa Note-olioita)
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


    def set_default_names(self, def_names:dict):
        ''' Creates default links from Place to fi and sv PlaceNames.
        
            The objects are referred with database id numbers.

            - place         Place object
            - - .names      PlaceName objects
            - def_names     dict {lang, uid} uniq_id's of PlaceName objects
        '''
        ds = shareds.datastore.dataservice
        ds.ds_place_set_default_names(self.uniq_id,
                                    def_names['fi'], def_names['sv'])


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
                    if name.lang == lang and not lang in selection.keys():
                        # A matching language
                        #print(f'# select {lang}: {name.name} {name.uniq_id}')
                        selection[lang] = name.uniq_id
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
            return {'status':Status.OK, 'ids':ret}

        except Exception as e:
            logger.error(f"bl.place.PlaceBl.find_default_names {selection}: {e}")
            return {'status':Status.ERROR, 'items':selection}


    def save(self, tx, **kwargs):
        """ Save Place, Place_names, Notes and connect to hierarchy.
        
        :param: place_keys    dict {handle: uniq_id}
        :param: batch_id      batch id where this place is linked

        The 'uniq_id's of already created nodes can be found in 'place_keys' 
        dictionary by 'handle'.

        Create node for Place self:
        1) node exists: update its parameters and link to Batch
        2) new node: create node and link to Batch

        For each 'self.surround_ref' link to upper node:
        3) upper node exists: create link to that node
        4) new upper node: create and link hierarchy to Place self

        Place names are always created as new 'Place_name' nodes.
        - If place has date information, add datetype, date1 and date2 
          parameters to NAME link
        - Notes are linked to self using 'note_handles's (the Notes have been 
          saved before)

        NOT Raises an error, if write fails.
        """
        if 'batch_id' in kwargs:
            batch_id = kwargs['batch_id']
        else:
            raise RuntimeError(f"bl.place.PlaceBl.save needs a batch_id for {self.id}")

        # Create or update this Place

        self.uuid = self.newUuid()
        pl_attr = {}
        try:

            pl_attr = {
                "uuid": self.uuid,
                "handle": self.handle,
                "change": self.change,
                "id": self.id,
                "type": self.type,
                "pname": self.pname}
            if self.coord:
                # If no coordinates, don't set coord attribute
                pl_attr["coord"] = self.coord.get_coordinates()

            # Create Place self

            if 'place_keys' in kwargs:
                # Check if this Place node is already created
                place_keys = kwargs['place_keys']
                plid = place_keys.get(self.handle)
            else:
                plid = None

            if plid:
                # 1) node has been created but not connected to Batch.
                #    update known Place node parameters and link from Batch
                self.uniq_id = plid
                if self.type:
                    #print(f"Pl_save-1 Complete Place ({self.id} #{plid}) {self.handle} {self.pname}")
                    result = tx.run(CypherPlace.complete, #TODO
                                    batch_id=batch_id, plid=plid, p_attr=pl_attr)
                else:
                    #print(f"Pl_save-1 NO UPDATE Place ({self.id} #{plid}) attr={pl_attr}")
                    pass
            else:
                # 2) new node: create and link from Batch
                #print(f"Pl_save-2 Create a new Place ({self.id} #{self.uniq_id} {self.pname}) {self.handle}")
                result = tx.run(CypherPlace.create, 
                                batch_id=batch_id, p_attr=pl_attr)
                self.uniq_id = result.single()[0]
                place_keys[self.handle] = self.uniq_id

        except Exception as err:
            print(f"iError Place.create: {err} attr={pl_attr}") #, file=stderr)
            raise

        # Create Place_names

        try:
            for name in self.names:
                n_attr = {"name": name.name,
                          "lang": name.lang}
                if name.dates:
                    n_attr.update(name.dates.for_db())
                result = tx.run(CypherPlace.add_name, 
                                pid=self.uniq_id, order=name.order, n_attr=n_attr)
                name.uniq_id = result.single()[0]
                #print(f"# ({self.uniq_id}:Place)-[:NAME]->({name.uniq_id}:{name})")
        except Exception as err:
            print("iError Place.add_name: {err}") #, file=stderr)
            raise

        # Select default names for default languages
        ret = PlaceBl.find_default_names(self.names, ['fi', 'sv'])
        if ret.get('status') == Status.OK:
            # Update default language name links
            self.set_default_names(ret.get('ids'))

        # Make hierarchy relations to upper Place nodes

        for ref in self.surround_ref:
            try:
                up_handle = ref['hlink']
                #print(f"Pl_save-surrounding {self} -[{ref['dates']}]-> {up_handle}")
                if 'dates' in ref and isinstance(ref['dates'], DateRange):
                    rel_attr = ref['dates'].for_db()
                    #_r = f"-[{ref['dates']}]->"
                else:
                    rel_attr = {}
                    #_r = f"-->"

                # Link to upper node

                uid = place_keys.get(up_handle) if place_keys else None 
                if uid:
                    # 3) Link to a known upper Place
                    #    The upper node is already created: create a link to that
                    #    upper Place node
                    #print(f"Pl_save-3 Link ({self.id} #{self.uniq_id}) {_r} (#{uid})")
                    result = tx.run(CypherPlace.link_hier,
                                    plid=self.uniq_id, up_id=uid, r_attr=rel_attr)
                else:
                    # 4) Link to unknown place
                    #    A new upper node: create a Place with only handle
                    #    parameter and link hierarchy to Place self
                    #print(f"Pl_save-4 Link to empty upper Place ({self.id} #{self.uniq_id}) {_r} {up_handle}")
                    result = tx.run(CypherPlace.link_create_hier,
                                    plid=self.uniq_id, r_attr=rel_attr, 
                                    up_handle=up_handle)
                    place_keys[up_handle] = result.single()[0]

            except Exception as err:
                print(f"iError Place.link_hier: {err} at {self.id} --> {up_handle}") #, file=stderr)
                raise
            
        try:
            for note in self.notes:
                n_attr = {"url": note.url,
                          "type": note.type,
                          "text": note.text}
                result = tx.run(CypherPlace.add_urls, 
                                batch_id=batch_id, pid=self.uniq_id, n_attr=n_attr)
        except Exception as err:
            traceback.print_exc()
            print(f"iError Place.add_urls: {err}") #, file=stderr)
            raise

        # Make the place note relations; the Notes have been stored before
        #TODO: Voi olla useita Noteja samalla handlella! Käyttäisit uniq_id:tä!
        try:
            for n_handle in self.note_handles:
                result = tx.run(CypherPlace.link_note, 
                                pid=self.uniq_id, hlink=n_handle)
#         except AttributeError:
#             print('bl.place.PlaceBl.save: No notes for {self}')
        except Exception as err:
            logger.error(f"Place_gramps.save: {err} in linking Notes {self.handle} -> {self.note_handles}")
            #print(f"iError Place.link_notes {self.note_handles}: {err}", file=stderr)
            raise

        # Make relations to the Media nodes and their Note and Citation references
        MediaBl.create_and_link_by_handles(self.uniq_id, self.media_refs)
            
        return


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
        #return self._lang_key(self) < self._lang_key(other)
    def __le__(self, other):        return self._lang_key(self) <= self._lang_key(other)
    def __eq__(self, other):        return self._lang_key(self) == self._lang_key(other)
    def __ge__(self, other):        return self._lang_key(self) >= self._lang_key(other)
    def __gt__(self, other):        return self._lang_key(self) > self._lang_key(other)
    def __ne__(self, other):        return self._lang_key(self) != self._lang_key(other)




class PlaceDataReader:
    '''
    Abstracted Place datastore for reading.

    Data reading class for Place objects with associated data.

    - Use pe.db_reader.DbReader.__init__(self, readservice, u_context) 
      to define the database driver and user context

    - Returns a Result object which includes the items and eventuel error object.

    - Methods return a dict result object {'status':Status, ...}
    '''
    def __init__(self, readservice, u_context):
        ''' Initiate datastore.

        :param: readservice   pe.neo4j.readservice.Neo4jReadService
        :param: u_context     ui.user_context.UserContext object
        '''
        self.readservice = readservice
        self.driver = readservice.driver
        self.user_context = u_context


    def get_place_list(self):
        """ Get a list on PlaceBl objects with nearest heirarchy neighbours.
        
            Haetaan paikkaluettelo ml. hierarkiassa ylemmät ja alemmat
    """
        context = self.user_context
        fw = context.first  # From here forward
        use_user = context.batch_user()
        places = self.readservice.dr_get_place_list_fw(use_user, fw, context.count, 
                                                       lang=context.lang)

        # Update the page scope according to items really found 
        if places:
            print(f'PlaceDataReader.get_place_list: {len(places)} places '
                  f'{context.direction} "{places[0].pname}" – "{places[-1].pname}"')
            context.update_session_scope('place_scope', 
                                          places[0].pname, places[-1].pname, 
                                          context.count, len(places))
        else:
            print(f'bl.place.PlaceDataReader.get_place_list: no places')
            return {'status': Status.NOT_FOUND, 'items': [],
                    'statustext': f'No places fw="{fw}"'}
        return {'items':places, 'status':Status.OK}


    def get_places_w_events(self, uuid):
        """ Read the place hierarchy and events connected to this place.
        
            Luetaan aneettuun paikkaan liittyvä hierarkia ja tapahtumat
            Palauttaa paikkahierarkian ja (henkilö)tapahtumat.
    
        """
        # Get a Place with Names, Notes and Medias
        use_user = self.user_context.batch_user()
        lang = self.user_context.lang
        res = self.readservice.dr_get_place_w_names_notes_medias(use_user, uuid, lang)
        place = res.get("place")
        results = {"place":place, 'status':Status.OK}

        if not place:
            res = {'status':Status.ERROR, 'statustext':
                       f'get_places_w_events: No Place with uuid={uuid}'}
            return res
        
        #TODO: Find Citation -> Source -> Repository for each uniq_ids
        try:
            results['hierarchy'] = \
                self.readservice.dr_get_place_tree(place.uniq_id, lang=lang)

        except AttributeError as e:
            traceback.print_exc()
            return {'status': Status.ERROR,
                   'statustext': f"Place tree attr for {place.uniq_id}: {e}"}
        except ValueError as e:
            return {'status': Status.ERROR,
                   'statustext': f"Place tree value for {place.uniq_id}: {e}"}

        res = self.readservice.dr_get_place_events(place.uniq_id)
        results['events'] = res['items']
        return results


class PlaceDataStore:
    '''
    Abstracted Place datastore for update.

    Data update class for Place objects with associated data.

    - Use pe.db_reader.DbReader.__init__(self, readservice, u_context) 
      to define the database driver and user context

    - Returns a Result object which includes the items and eventuel error object.

    - Methods return a dict result object {'status':Status, ...}
    '''

    def __init__(self, dataservice):
        ''' Initiate datastore.

        #TODO Not needed: :param: driver    neo4j.DirectDriver object
        :param: dataservice pe.neo4j.dataservice.Neo4jDataService
        '''
        self.dataservice = dataservice
        self.driver = dataservice.driver


    def merge2places(self, id1, id2):
        ''' Merges two places
        '''
        # Check that given nodes are included in the same Batch or Audit node
        ret = self.dataservice.ds_merge_check(id1, id2)
        if Status.has_failed(ret):
            self.dataservice.ds_rollback()
            return ret

        # Merge nodes
        ret = self.dataservice.ds_merge_places(id1, id2)
        if Status.has_failed(ret):
            self.dataservice.ds_rollback()
            return ret

        place = ret.get('place')
        # Select default names for default languages
        ret = PlaceBl.find_default_names(place.names, ['fi', 'sv'])
        if Status.has_failed(ret):
            self.dataservice.ds_rollback()
            return ret
        st = ret.get('status')
        if st == Status.OK:
            # Update default language name links
            def_names = ret.get('ids')
            self.dataservice.ds_place_set_default_names(place.uniq_id, 
                                                        def_names['fi'], def_names['sv'])

            ret = self.dataservice.ds_commit()
            st = ret.get('status')
            return {'status':st, 'place':place, 
                    'statustext':ret.get('statustext', '')}

