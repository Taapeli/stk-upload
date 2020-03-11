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
# import  shareds
# from .dates import DateRange
# from .cypher import Cypher_place
# from .event_combo import Event_combo
# from .person_name import Name

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
