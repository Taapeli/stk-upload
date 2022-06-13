#   Isotammi Genealogical Service for combining multiple researchers' results.
#   Created in co-operation with the Genealogical Society of Finland.
#
#   Copyright (C) 2016-2021  Juha Mäkeläinen, Jorma Haapasalo, Kari Kujansuu,
#                            Timo Nallikari, Pekka Valta
#
#   This program is free software: you can redistribute it and/or modify
#   it under the terms of the GNU General Public License as published by
#   the Free Software Foundation, either version 2 of the License, or
#   (at your option) any later version.
#
#   This program is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU General Public License for more details.
#
#   You should have received a copy of the GNU General Public License
#   along with this program.  If not, see <http://www.gnu.org/licenses/>.

"""
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

"""
# blacked 2021-05-01 JMä
import logging

logger = logging.getLogger("stkserver")
from flask_babelex import _

from bl.base import NodeObject, Status
from bl.material import Material
from pe.dataservice import DataService

from bl.dates import DateRange


class Event(NodeObject):
    """Person or Family Event object.

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
                    note_handles[]     str lisätiedon handle (ent. note_handles)
                Planned from gramps_loader:
                    place_handles[]    str paikan handle (ent. place_hlink)
                    citation_handles[] str viittauksen handle (ent. citation_handles)
                    #citation_ref      str viittauksen handle
                    #objref_hlink      str median handle
            Previous Event_combo properties:
                    citations = []     Citations attached
                    names = []         Names attached
    """

    def __init__(self, uniq_id=None):
        """Creates a new Event instance."""
        """ Luo uuden event-instanssin """
        NodeObject.__init__(self, uniq_id)
        self.type = ""
        self.description = ""
        self.dates = None
        self.attr = dict()  # prev. attr_type, attr_value

    def __str__(self):
        return f"{self.uniq_id} {self.type} {self.description}"


class EventReader(DataService):
    """
    Data reading class for Event objects with associated data.

    - Returns a Result object.
    """

    def get_event_data(self, iid, material:Material, args):
        """
        Get event data and participants: Persons and Families.

        The args may include
        - 'iid': 'H-ad3'
        - 'referees': True
        - 'notes': True
        """
        statustext = ""
        res_dict = {}
        res = self.dataservice.dr_get_event_by_iid(self.use_user, iid, material)
        if Status.has_failed(res):
            return {
                "item": None,
                "status": res["status"],
                "statustext": _("The event is not accessible"),
            }
        event = res["item"]
        event.note_ref = []
        res_dict["event"] = event

        members = []
        if args.get("referees"):
            res = self.dataservice.dr_get_event_participants(event.uniq_id)
            if Status.has_failed(res):
                statustext += _("Participants read error ") + res["statustext"] + " "
                print(f"bl.event.EventReader.get_event_data: {statustext}")
            else:
                members = res["items"]
                res_dict["members"] = members
        places = []
        if args.get("places"):
            res = self.dataservice.dr_get_event_place(event.uniq_id)
            if Status.has_failed(res):
                statustext += _("Place read error ") + res["statustext"] + " "
            else:
                places = res["items"]
                res_dict["places"] = places

        notes = []
        medias = []
        if args.get("notes"):
            res = self.dataservice.dr_get_event_notes_medias(event.uniq_id)
            if Status.has_failed(res):
                statustext += _("Notes read error ") + res["statustext"] + " "
            else:
                notes = res["notes"]
                res_dict["notes"] = notes
                medias = res["medias"]
                res_dict["medias"] = medias

        res_dict["status"] = res["status"]
        res_dict["statustext"] = f"Got {len(members)} participants, {len(notes)} notes"
        return res_dict


class EventBl(Event):
    """Event / Paikka:

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

    def __init__(self):  # , eid='', desc='', handle=''):
        """
        Constructor Luo uuden EventBl -instanssin
        """
        Event.__init__(self)
        self.role = ""  # role of event from EVENT relation, if available
        # Lists of uniq_ids:
        self.note_handles = []
        self.citation_ref = []
        self.place_ref = []
        self.media_ref = []
        self.note_ref = []

        self.citations = []  # For creating display sets
        #       self.notes = []         # TODO: Note objects <- note_handles[]
        self.place = None  # Place node, if included
        self.person = None  # Persons names connected; for creating display


class EventWriter:
    def __init__(self, writeservice, u_context):
        self.writeservice = writeservice
        self.u_context = u_context

    def update_event(self, iid, args):
        rec = self.writeservice.dr_update_event(iid, args)
        return rec
