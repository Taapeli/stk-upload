'''
Created on 2.5.2017 from Ged-prepare/Bus/classes/genealogy.py
Extracted 23.5.2019 from models.gen.place.Place

@author: jm
'''

import  shareds
from bl.place import Place, PlaceName

#from .place import Place, Place_name, Point
from .note import Note
from .media import Media
from .dates import DateRange
from .cypher import Cypher_place
#from models.dbtree import DbTree
#from models.gen.event_combo import Event_combo
#from models.gen.person_name import Name

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
                media_ref[]         int uniq_ids of Medias
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
        self.media_ref = []     # uniq_id of models.gen.media.Media


    def __str__(self):
        if hasattr(self, 'level'):
            lv = self.level
        else:
            lv = ""
        return f"{self.pname} ({self.type}) {lv}"


#     @classmethod from_node(cls, node):
#         ''' Creates a node object of type Place_combo from a Neo4j node.


    def show_names_list(self): 
        """ Returns list of referred Place_names for this place.
            If none, return pname

            #TODO Remove:  Event_combo.clearnames is not set or in use
        """
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
        """ Reads Place_combo nodes or selected node with PlaceName objects.

            TODO Remove: Not in use
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
                plname = PlaceName.from_node(node)
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
                    pl.names.append(PlaceName.from_node(names_node))
#                     if pl.names[-1].lang in ['fi', '']:
#                         #TODO: use current_user's lang
#                         pl.pname = pl.names[-1].name

                for notes_node in place_record['notes']:
                    n = Note.from_node(notes_node)
                    pl.notes.append(n)

                for medias_node in place_record['medias']:
                    m = Media.from_node(medias_node)
                    pl.media_ref.append(m)
                    
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


#     def get_place_hierarchy():  # @staticmethod --> Neo4jDriver.get_place_list
#         """ Get a list on Place_combo objects with nearest heirarchy neighbours.
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
# └──────┴─────────┴────────────────────┴───────┴────────────────────┴────────────────────┘
# """
#         ret = []
#         result = shareds.driver.session().run(Cypher_place.get_name_hierarchies)
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
#             p = Place_combo(pl_id)
#             p.uuid =record['uuid']
#             p.type = record.get('type')
#             if record['coord']:
#                 p.coord = Point(record['coord']).coord
#             # Set place names and default display name pname
#             for nnode in record.get('names'):
#                 pn = Place_name.from_node(nnode)
#                 if pn.lang in ['fi', '']:
#                     # Default language name
#                     #TODO use language from current_user's preferences
#                     p.pname = pn.name
#                 p.names.append(pn)
#             if p.pname == '' and p.names:
#                 p.pname = p.names[0].name
#             p.uppers = Place_combo._combine_places(record['upper'])
#             p.lowers = Place_combo._combine_places(record['lower'])
#             ret.append(p)
#         # Return sorted by first name in the list p.pname
#         return sorted(ret, key=lambda x:x.pname)


#     def get_my_place_hierarchy(o_context):   # @staticmethod --> bl.place.PlaceBl.get_list
#         """ Get a list on Place_combo objects with nearest heirarchy neighbours.


#     def _combine_places(pn_tuples):    # @staticmethod --> PlaceBl.combine_places
#         """ Creates a list of Places with names combined from given names.


    def namelist_w_lang(self):
        """ Return a vector of name data for this place.
         
            [[name, lang], [name,lang]]
         
            Muodostetaan nimien luettelo jossa on mahdolliset kielikoodit
            mainittuna.
            Jos sarakkeessa field[1] on mainittu kielikoodi
            se lisätään kunkin nimen field[0] perään suluissa

        #TODO Remove, not in use
        #TODO Lajiteltava kielen mukaan jotenkin
        """
        ret = []
        for n in sorted(self.names, key=lambda x:x.lang):
            ret.append(n)
        return ret



#     def get_place_tree(locid): # @staticmethod > Neo4jDriver.get_place_tree
#         """ Haetaan koko paikkojen ketju paikan locid ympärillä
#             Palauttaa listan paikka-olioita ylimmästä alimpaan.


#     def get_place_events(loc_id): @staticmethod > DBreader.dr_get_place_with_events
#         """ Haetaan paikkaan liittyvät tapahtumat sekä
#             osallisen henkilön nimitiedot.


#     save() - see PlaceGramps.save()
