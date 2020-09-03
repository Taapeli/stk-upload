'''
    Event classes: Event, EventBl, EventReader and EventName.

    - Event        represents Event Node in database
    - EventBl      represents Event and connected data (was Event_combo)
    - EventReader  has methods for reading Event and connected data
                   called from ui routes.py

Created on 11.3.2020 in bl.Event
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
import logging 
logger = logging.getLogger('stkserver')
from flask_babelex import _

from .base import NodeObject, Status
#from .place import PlaceReader
from pe.db_reader import DBreader

from models.gen.dates import DateRange
#from models.gen.person_combo import Person_combo, Name
#from models.gen.family_combo import Family_combo


class Event(NodeObject):
    """ Person or Family Event object.
    
        Tapahtuma
            
        Properties:
                handle             Unique constant handle (mostly from Gramps)
                change             Original timestamp like 1502552858
                id                 esim. "E0001"
                type               esim. "Birth"
                description        esim. ammatin kuvaus
                date               str aika
                dates              DateRange date expression
                attr[]             dict lisätiedot {attr_type: attr_value}
#                 attr_type          str lisätiedon tyyppi
#                 attr_value         str lisätiedon arvo
            For gramps_loader:
                note_handles[]     str lisätiedon handle (ent. noteref_hlink)
            Planned from gramps_loader:
                place_handles[]    str paikan handle (ent. place_hlink)
                citation_handles[] str viittauksen handle (ent. citationref_hlink)
                #place_hlink       str paikan handle
                #citation_ref      str viittauksen handle
                #objref_hlink      str median handle
        Event_combo properties:
                citations = []     Citations attached
                names = []         Names attached
     """

    def __init__(self, uniq_id=None):
        """ Creates a new Event instance.
        """
        """ Luo uuden event-instanssin """
        NodeObject.__init__(self, uniq_id)
        self.type = ''
        self.description = ''
        self.dates = None
        self.attr = dict()         # prev. attr_type, attr_value
       
    def __str__(self):
        return f"{self.uniq_id} {self.type} {self.description}"


    @classmethod
    def from_node(cls, node, obj=None):
        '''
        Transforms a db node to an object of type Event or EventBl.
        
        <Node id=88532 labels={'Event'} 
            properties={'type': 'Birth', 'change': 1500907890, attr_value': '', 
                'id': 'E0161', 'attr_type': '', 'description': ''
                'datetype': 0, 'date1': 1754183, 'date2': 1754183}>
        '''
        if not obj:
            obj = cls()
        obj.uniq_id = node.id
        obj.id = node['id']
        obj.uuid = node['uuid']
        obj.type = node['type']
        obj.handle = node.get('handle', None)
        obj.change = node.get('change', None)
        if "datetype" in node:
            obj.dates = DateRange(node["datetype"], node["date1"], node["date2"])
        else:
            obj.dates = DateRange()
        obj.description = node['description'] or ''
        obj.attr = node.get('attr', dict())
        return obj


class EventReader(DBreader):
    '''
        Data reading class for Event objects with associated data.

        - Use pe.db_reader.DBreader.__init__(self, dbdriver, u_context) 
          to define the database driver and user context

        - Returns a Result object.
    '''
    def get_event_data(self, uuid):
        '''
            Get event data and participants: Persons and Families.
        '''
        result = self.dbdriver.dr_get_event_by_uuid(self.use_user, uuid)
        if (result['status'] != Status.OK):
            return {'item':None, 'status':result['status'], 
                    'statustext': _('The event is not accessible')}
        event = result['item']

        result = self.dbdriver.dr_get_event_participants(event.uniq_id)
        if (result['status'] == Status.ERROR):
            return {'item':None, 'status':result['status'], 
                    'statustext': _('Participants read error')}
        members = result['items']

        return {'event':event, 'members':members, 'status':result['status'], 
                    'statustext': f'Got {len(members)} participants'}


class EventBl(Event):
    """ Event / Paikka:

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

    def __init__(self):         #, eid='', desc='', handle=''):
        '''
        Constructor Luo uuden Event_combo -instanssin
        '''
        Event.__init__(self)
        self.role = ''          # role of event from EVENT relation, if available
        # Lists of uniq_ids:
        self.note_ref = []
        self.citation_ref = []
        self.place_ref = []
        self.media_ref = []
        
        self.citations = []     # For creating display sets
        self.place = None       # Place node, if included
        self.person = None      # Persons names connected; for creating display

