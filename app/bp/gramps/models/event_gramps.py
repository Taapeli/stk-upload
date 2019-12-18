'''
    Event class for Gramps XML conversion to Neo4j.

Created on 2.5.2017
@author: Jorma Haapasalo <jorma.haapasalo@pp.inet.fi>
'''
import datetime
from sys import stderr

from shareds import logger
from models.gen.event import Event
from models.cypher_gramps import Cypher_event_w_handle


class Event_gramps(Event):
    """ An Event from Gramps xml file.

        Tapahtuma grampsista tuotuna

        Event properties for gramps_loader:
                note_handles[]     str lisätiedon handle (ent. noteref_hlink)
            Planned from gramps_loader:
                place_handles[]    str paikan handle (ent. place_hlink)
                citation_handles[] str viittauksen handle (ent. citationref_hlink)
            media_handles[]     list media ref tuples:    (ent. objref_hlink)
                                str media_handle
                                tuple picture crop = (int left, int upper, int right, int lower)
#             Properties from Gramps:
#                 attr_type          str lisätiedon tyyppi
#                 attr_value         str lisätiedon arvo
            Obsolete:
                place_hlink        str paikan handle
                objref_hlink       str median handle
     """

    def __init__(self):
        """ Luo uuden event-instanssin """
        Event.__init__(self)
        self.note_handles = []      # Note handles (previous noteref_hlink had
                                    # only the first one)
        self.citation_handles = []  # (previous citationref_hlink)

        self.place_hlink = ''
        self.media_handles = []

        self.citations = []   # For creating display sets
        self.names = []   # For creating display sets


    def save(self, tx, **kwargs):
        """ Saves event to database:
            - Creates a new db node for this Event
            - Sets self.uniq_id

            - links to existing Place, Note, Citation, Media objects
            - Does not link it from UserProfile or Person
        """
        if kwargs:
            print(f"Warning: Event_gramps.save: extra arguments {kwargs}!")

        today = str(datetime.date.today())
        self.uuid = self.newUuid()
        e_attr = {
            "uuid": self.uuid,
            "handle": self.handle,
            "change": self.change, 
            "id": self.id, 
            "type": self.type,
            "description": self.description}
        if self.attr:
            # Convert 'attr' dict to list for db
            a = []
            for key, value in self.attr.items(): 
                a = a + [key, value]
                e_attr.update({'attr': a})
        if self.dates:
            e_attr.update(self.dates.for_db())
        try:
            result = tx.run(Cypher_event_w_handle.create, date=today, e_attr=e_attr)
            ids = []
            for record in result:
                self.uniq_id = record[0]
                ids.append(self.uniq_id)
                if len(ids) > 1:
                    print("iError updated multiple Events {} - {}, attr={}".format(self.id, ids, e_attr))
        except Exception as err:
            print("iError: Event_save: {0} attr={1}".format(err, e_attr), file=stderr)
            raise RuntimeError("Could not save Event {}".format(self.id))

        try:
            # Make relation to the Place node
            if self.place_hlink:
                tx.run(Cypher_event_w_handle.link_place, 
                       handle=self.handle, place_hlink=self.place_hlink)
        except Exception as err:
            print("iError: Event_link_place: {0}".format(err), file=stderr)

        try:
            # Make relations to the Note nodes
            if self.note_handles:
                result = tx.run(Cypher_event_w_handle.link_notes, handle=self.handle,
                       note_handles=self.note_handles)
                _cnt = result.single()["cnt"]
                #print(f"##Luotiin {cnt} Note-yhteyttä: {self.id}->{self.note_handles}")
        except Exception as err:
            logger.error(f"{err}: in creating Note links: {self.id}->{self.note_handles}")
            #print("iError: Event_link_notes: {0}".format(err), file=stderr)

        try:
            # Make relations to the Citation nodes
            if self.citation_handles: #  citationref_hlink != '':
                tx.run(Cypher_event_w_handle.link_citations,
                       handle=self.handle, citation_handles=self.citation_handles)
        except Exception as err:
            print("iError: Event_link_citations: {0}".format(err), file=stderr)

        try:
            # Make relation to the Media nodes
            order = 1
            for handle, crop in self.media_handles:
                r_attr = {'order':order}
                if crop:
                    r_attr['left']  = crop[0]
                    r_attr['upper'] = crop[1]
                    r_attr['right'] = crop[2]
                    r_attr['lower'] = crop[3]
                tx.run(Cypher_event_w_handle.link_media, 
                       handle=self.handle, m_handle=handle, r_attr=r_attr)
                order =+ 1
        except Exception as err:
            print("iError: Event_link_media: {0}".format(err), file=stderr)
            
        return
