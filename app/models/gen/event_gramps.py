'''

    Event hierarkiasuunnitelma 23.8.2018/JMä

    class gen.event.*Event*(): 
       vain Event-noden parametrit (uniq_id, tyyppi, handle, päivämäärät)

    class *Event_compound*(Event): 
        - __init__()
        - get_person_events()
        - get_baptism_data()
        - get_cite_sour_repo() static <-- get_citation_path()?
        - get_event_cite()
       Event, lähteet, huomautukset, henkilön uniq_id

    2. *Event_w_person*: 
       Event ja ja siihen liittyvät Person-nodet ja roolit (ehkä myös nimet?)
    3. *Event_w_place*: 
       Event ja liittyvät paikat (pyydettäessä myös paikannimet?)

    Nämä siis periytyvät Event-luokasta ja sisältävät tarpeen mukaan 
    tietokantametodit _read(), get()_ ja _save()_ (_read_ hakukenttien avulla, 
    _get_ uniq_id:n avulla). L
    
    isäksi on kätevä olla metodi __str__(), joka antaa lyhyen sanalliseen muodon
    "syntynyt välillä 1.3.1840...31.3.1840 Hauho".
    
    Ehkä _save()_-metodi koskee vain Event-nodea, ei liittyvä nodeja? 
    Ehkä yhteydet myös?
    
    Prosessointiin ja näyttöihin tehdään tarpeen mukaan bisnes-luokkia, 
    jotka sisältävät esim. poiminta-, yhdistely- ja muokkaussääntöjä ja 
    siellä ehkä hoidetaan isompien kokonaisuuksien talletus 
    (kuten henkilö + nimet ja lähteet).

Created on 2.5.2017
@author: Jorma Haapasalo <jorma.haapasalo@pp.inet.fi>
'''
import datetime
from sys import stderr

from models.gen.dates import DateRange
from .event import Event
from models.cypher_gramps import Cypher_event_w_handle

#-------------------------------------------------------------------------------

class Event_gramps(Event):
    """ An Event from Gramps xml file
        Tapahtuma grampsista tuotuna
            
        Event properties:
                handle             Gramps handle
                change
                id                 esim. "E0001"
                type               esim. "Birth"
                description        esim. ammatin kuvaus
                date               str aika
                dates              DateRange date expression
            Planned for Gramps:
                place_handle[]     str paikan handle (ent. place_hlink)
                note_handle[]      str lisätiedon handle (ent. noteref_hlink)
                citation_handle[]  str viittauksen handle (ent. citationref_hlink)
                media_handle[]     str median handle (ent. objref_hlink)
        Properties from Gramps:
                attr_type          str lisätiedon tyyppi
                attr_value         str lisätiedon arvo
                place_hlink        str paikan handle
                noteref_hlink      str lisätiedon handle
                citationref_hlink  str viittauksen handle
                objref_hlink       str median handle
     """

    def __init__(self, eid='', desc='', handle=''):
        """ Luo uuden event-instanssin """
        Event.__init__(self, eid, desc, handle)
        # self.handle = handle
        # self.change = ''
        # self.id = eid
        # self.description = desc
        # self.date = ''
        # self.dates = None
        self.attr_type = ''
        self.attr_value = ''
        self.place_hlink = ''
        self.noteref_hlink = ''
        self.citationref_hlink = ''
        self.objref_hlink = ''
        self.citations = []   # For creating display sets
        self.names = []   # For creating display sets


    def save(self, username, tx):
        """ Saves event to database:
            - Creates a new db node for this Event
            - links it to UserProfile, Person
            - links to existing Place, Note, Citation, Media objects
        """

        today = str(datetime.date.today())
        e_attr = {
            "handle": self.handle,
            "change": self.change, 
            "id": self.id, 
            "type": self.type,
            "description": self.description, 
            "attr_type": self.attr_type, 
            "attr_value": self.attr_value}
        if self.dates:
            e_attr.update(self.dates.for_db())
        try:
            tx.run(Cypher_event_w_handle.create, 
                   username=username, date=today, e_attr=e_attr)
        except Exception as err:
            print("Virhe.event_save: {0}".format(err), file=stderr)

        try:
            # Make relation to the Place node
            if self.place_hlink != '':
                tx.run(Cypher_event_w_handle.link_place, 
                       handle=self.handle, place_hlink=self.place_hlink)
        except Exception as err:
            print("Virhe.event_link_place: {0}".format(err), file=stderr)

        try:
            # Make relation to the Note node
            if self.noteref_hlink != '':
                tx.run(Cypher_event_w_handle.link_note,
                       handle=self.handle, noteref_hlink=self.noteref_hlink)
        except Exception as err:
            print("Virhe.event_link_note: {0}".format(err), file=stderr)

        try:
            # Make relation to the Citation node
            if self.citationref_hlink != '':
                tx.run(Cypher_event_w_handle.link_citation,
                       handle=self.handle, citationref_hlink=self.citationref_hlink)
        except Exception as err:
            print("Virhe.event_link_citation: {0}".format(err), file=stderr)

        try:
            # Make relation to the Media node
            if self.objref_hlink != '':
                tx.run(Cypher_event_w_handle.link_media, 
                       handle=self.handle, objref_hlink=self.objref_hlink)
        except Exception as err:
            print("Virhe.event_link_media: {0}".format(err), file=stderr)
            
        return

# class Event_for_template(Event):
''' Tämä on korvattu luokalla Event_combo'''
#     """ Template-tapahtuma perii Tapahtuma-luokan
#             
#         Properties:
#                 place              str paikan nimi
#     """
# 
#     def __init__(self, eid='', desc='', handle=''):
#         """ Luo uuden event-instanssin """
#         Event.__init__(self, eid, desc, handle)
#         self.place = ''
