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
    Source classes: Source, SourceBl and SourceReader.

    - Source       represents Source Node in database
    - SourceBl     represents Source and connected data (was Source_combo)
    - SourceReader has methods for reading Source and connected data
                   called from ui routes.py

Created on 3.5.2020
@author: jm

Created on 2.5.2017 from Ged-prepare/Bus/classes/genealogy.py
@author: Jorma Haapasalo <jorma.haapasalo@pp.inet.fi>

"""
# blacked 2021-05-01 JMä
import shareds
import logging

from .base import NodeObject, Status
from .person import Person
from pe.dataservice import DataService

logger = logging.getLogger("stkserver")


class Source(NodeObject):
    """Source

    Properties:
            handle
            change
            id              esim. "S0001"
            stitle          str lähteen otsikko

    See also: bp.gramps.models.source_gramps.Source_gramps
    """

    def __init__(self, uniq_id=None):
        """ Luo uuden source-instanssin """
        NodeObject.__init__(self, uniq_id=uniq_id)
        self.stitle = ""
        self.sauthor = ""
        self.spubinfo = ""

    def __str__(self):
        return "{} '{}' '{}' '{}'".format(
            self.id, self.stitle, self.sauthor, self.spubinfo
        )

    @classmethod
    def from_node(cls, node):
        """
        Transforms a db node to an object of type Source.
        """
        # <Node id=355993 labels={'Source'}
        #     properties={'id': 'S0296', 'stitle': 'Hämeenlinnan lyseo 1873-1972',
        #         'uuid': 'c1367bbdc6e54297b0ef12d0dff6884f', 'spubinfo': 'Karisto 1973',
        #         'sauthor': 'toim. Mikko Uola', 'change': 1585409705}>

        s = cls()  # create a new Source or SourceBl
        s.uniq_id = node.id
        s.id = node["id"]
        s.uuid = node["uuid"]
        if "handle" in node:
            s.handle = node["handle"]
        s.stitle = node["stitle"]
        s.sauthor = node["sauthor"]
        s.spubinfo = node["spubinfo"]
        s.sabbrev = node.get("sabbrev", "")
        s.change = node["change"]
        return s


class SourceBl(Source):
    """Source with optional referenced data.

    Arrays repositories, citations, notes may contain business objects
    Array note_ref may contain database keys (uniq_ids)
    """

    def __init__(self, uniq_id=None):
        """Creates a new PlaceBl instance.

        You may also give for printout eventual hierarchy level
        """
        Source.__init__(self, uniq_id)

        # For display combo
        # Todo: onko repositories, citations käytössä?
        self.repositories = []
        self.citations = []
        self.notes = []
        self.note_handles = []
        self.note_ref = []


class SourceReader(DataService):
    """
    Data reading class for Source objects with associated data.

    - Returns a Result object which includes the items and eventual error object.
    """

    def __init__(self, service_name: str, u_context=None):
        """Create a reader object with db driver and user context."""
        super().__init__(service_name, u_context)
        if u_context:
            # For reader only; writer has no context?
            self.user_context = u_context
            self.username = u_context.user
            if u_context.context == u_context.ChoicesOfView.COMMON:
                self.use_user = None
            else:
                self.use_user = u_context.user

    def get_source_list(self):
        """Get junk of Source objects for Sources list."""
        context = self.user_context
        fw = context.first  # From here forward
        use_user = context.batch_user()
        args = {"user": use_user, "fw": fw, "count": context.count}
        if context.series:
            # Filtering by series (Lähdesarja)
            THEMES = {
                "birth": ("syntyneet", "födda"),
                "babtism": ("kastetut", "döpta"),
                "wedding": ("vihityt", "vigda"),
                "death": ("kuolleet", "döda"),
                "move": ("muuttaneet", "flyttade"),
            }
            theme_fi, theme_sv = THEMES[context.series]
            args["theme1"] = theme_fi
            args["theme2"] = theme_sv
        try:
            sources = shareds.dservice.dr_get_source_list_fw(args)
            # results = {'sources':sources,'status':Status.OK}

            # Update the page scope according to items really found
            if sources:
                context.update_session_scope(
                    "source_scope",
                    sources[0].stitle,
                    sources[-1].stitle,
                    context.count,
                    len(sources),
                )
            else:
                return {"items": [], "status": Status.NOT_FOUND}

            results = {"items": sources, "status": Status.OK}
        except Exception as e:
            results = {"status": Status.ERROR, "statustext": f"Source list: {e}"}
        return results

    def get_source_with_references(self, uuid, u_context):
        """Read the source, repository and events etc referencing this source.

        Returns a dictionary, where items = Source object.
        - item.notes[]      Notes connected to Source
        - item.repositories Repositories for Source
        - item.citations    Citating Persons, Events, Families and Medias
                            as [label, object] tuples(?)
        """
        use_user = self.user_context.batch_user()
        res = shareds.dservice.dr_get_source_w_repository(use_user, uuid)
        if Status.has_failed(res):
            return res
        source = res.get("item")
        if not source:
            res.statustext = f"no Source with uuid={uuid}"
            return res

        citations, notes, targets = shareds.dservice.dr_get_source_citations(
            source.uniq_id
        )

        #        if len(targets) == 0:
        #            # Only Citations connected to Person Event or Family Event can be
        #            # processed.
        #            #TODO: Should allow citating a Source from Place, Note, Meida etc
        #
        #            res['status'] = Status.NOT_FOUND
        #            res['statustext'] = _('No person or family has uses this source')
        #            return res

        cit = []
        for c_id, citation in citations.items():
            if c_id in notes:
                citation.notes = notes[c_id]
            for target in targets[c_id]:
                if u_context.privacy_ok(target):
                    # Insert person name and life events
                    if isinstance(target, Person):
                        shareds.dservice.dr_inlay_person_lifedata(target)
                    citation.citators.append(target)
                else:
                    print(f"DbReader.get_source_with_references: hide {target}")

            cit.append(citation)
        res["citations"] = cit

        return res
