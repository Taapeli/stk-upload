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
Created on 24.3.2020

@author: jm
"""
# blacked 2021-05-01 JMä
from .base import NodeObject, Status

from pe.dataservice import DataService

class Media(NodeObject):
    """A media object with description, file link and mime information.

    Tallenne

    Properties:
            handle
            change
            id              esim. "O0001"
            uniq_id         int database key
            src             str file path
            mime            str mime type
            description     str description
    """

    def __init__(self, iid=None):
        """ Luo uuden media-instanssin """
        NodeObject.__init__(self, iid)
        self.description = ""
        self.src = None
        self.mime = None
        self.name = ""

    def __str__(self):
        desc = (
            self.description
            if len(self.description) < 17
            else self.description[:16] + "..."
        )
        return f"{self.id}: {self.mime} {self.src} {desc!r}"



class MediaBl(Media):
    """
    Media file object for pictures and documents.
    """

    def __init__(self):
        """
        Constructor
        """
        Media.__init__(self)
        self.description = ""
        self.src = None
        self.mime = None
        self.name = ""



class MediaReader(DataService):
    """
    Data reading class for Event objects with associated data.

    - Returns a Result object.
    """

    def read_my_media_list(self):
        """Read Media object list using u_context."""
        fw = self.user_context.first  # next name
        user = self.user_context.batch_user()
        limit = self.user_context.count
        ustr = "for user " + user if user else "approved "
        print(
            f"MediaReader.read_my_media_list: Get max {limit} medias {ustr} starting {fw!r}"
        )

        res = self.dataservice.dr_get_media_list(self.use_user,
                                                 self.user_context.material,
                                                 fw,
                                                 limit)
        if Status.has_failed(res):
            return res
        medias = res.get("media", None)

        # Update the page scope according to items really found
        if fw == " ":
            first = self.user_context.NEXT_START
        else:
            first = medias[0].description
        if medias:
            self.user_context.update_session_scope(
                "media_scope",
                first,
                medias[-1].description,
                limit,
                len(medias),
            )
            return {"status": Status.OK, "items": medias}
        return {"status": Status.NOT_FOUND}

    def get_one(self, iid):
        """Read a Media object with referrer and referenced objects."""


        # Example database items:
        #    MATCH (media:Media) <-[r:MEDIA]- (ref) <-[:EVENT]- (ref2)
        #  media     r                    ref                           ref2
        # (media) <-[crop()]-            (Person 'I0026' id=21532) <-- (None)
        # (media) <-[crop(47,67,21,91)]- (Person 'I0026' id=21532) <-- (None)
        # (media) <-[crop(20,47,22,53)]- (Person 'I0029' id=21535) <-- (None)
        # (media) <-[crop()]-   (Event  'E9999' id=99999) <-- (Person 'I9999' id=999)

        user = self.user_context.batch_user()
        serv = self.dataservice
        res = serv.dr_get_media_single(user, self.user_context.material, iid)
        # returns {status, media, notes}
        #    where media.ref = list of referrer objects
        if Status.has_failed(res):
            return res

        media = res.get("media")
        media.notes = res.get("notes")

        res2 = serv.dr_get_sources_for_obj(user, self.user_context.material, iid)
        if Status.has_failed(res2):
            return res2
        cites = res2.get("citations", [])

        return {"status": Status.OK, "item": media, "cites": cites}


# class MediaWriter(DataService):
#  def __init__(self, service_name:str, u_context=None, tx=None):
#  def create_and_link_by_handles(): #-> bl.batch.BatchUpdater.media_create_and_link_by_handles


class MediaReferenceByHandles:
    """Gramps media reference result object.

    Includes Note and Citation references and crop data.
    Used in bp.gramps.xml_dom_handler.DOM_handler
    """

    def __init__(self, source_object: NodeObject):
        """ Create a reference object having referrer object label and 
            references with different reference properties.
        """
        lbl = source_object.__class__.__name__
        self.obj_name = lbl[:-2] if lbl.endswith("Bl") else lbl
            
        self.media_handle = None
        self.media_order = 0  # Media reference order nr
        self.crop = []  # Four coordinates
        self.note_handles = []  # list of note handles
        self.citation_handles = []  # list of citation handles

    def __str__(self):
        s = f"{self.obj_name} -> {self.media_handle} [{self.media_order}]"
        if self.crop:
            s += f" crop({self.crop})"
        if self.note_handles:
            s += f" notes({self.note_handles})"
        if self.citation_handles:
            s += f" citations({self.citation_handles})"
        return s
