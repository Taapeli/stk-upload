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
#import shareds
import logging

from .base import NodeObject, Status
from .person import Person
from pe.dataservice import DataService
from pe.neo4j.cypher.cy_source import CypherSourceByHandle

logger = logging.getLogger("stkserver")


class Source(NodeObject):
    """Source

    Properties:
            handle
            change
            id              esim. "S0001"
            stitle          str lähteen otsikko
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


    def save(self, dataservice, **kwargs):
        """ Saves this Source and connect it to Notes and Repositories.

            :param: batch_id      batch id where this place is linked

        """
        if 'batch_id' in kwargs:
            batch_id = kwargs['batch_id']
        else:
            raise RuntimeError(f"Source_gramps.save needs batch_id for {self.id}")
            
        self.uuid = self.newUuid()
        s_attr = {}
        try:
            s_attr = {
                "uuid": self.uuid,
                "handle": self.handle,
                "change": self.change,
                "id": self.id,
                "stitle": self.stitle,
                "sauthor": self.sauthor,
                "spubinfo": self.spubinfo
            }

            result = dataservice.tx.run(CypherSourceByHandle.create_to_batch,
                                        batch_id=batch_id, s_attr=s_attr)
            ids = []
            for record in result:
                self.uniq_id = record[0]
                ids.append(self.uniq_id)
                if len(ids) > 1:
                    print("iError updated multiple Sources {} - {}, attr={}".format(self.id, ids, s_attr))

        except Exception as err:
            print("iError source_save: {0} attr={1}".format(err, s_attr))
            raise RuntimeError("Could not save Source {}".format(self.id))

        # Make relation to the Note nodes
        for note_handle in self.note_handles:
            try:
                dataservice.tx.run(CypherSourceByHandle.link_note,
                                   handle=self.handle, hlink=note_handle)
            except Exception as err:
                logger.error(f"Source_gramps.save: {err} in linking Notes {self.handle} -> {self.note_handles}")
                #print("iError Source.save note: {0}".format(err), file=stderr)

        # Make relation to the Repository nodes
        for repo in self.repositories:
            try:
                dataservice.tx.run(CypherSourceByHandle.link_repository,
                                   handle=self.handle, 
                                   hlink=repo.handle, 
                                   medium=repo.medium)
            except Exception as err:
                print("iError Source.save Repository: {0}".format(err))
                
        return


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
            if u_context.is_common():
                self.use_user = None
            else:
                self.use_user = u_context.user

    def get_source_list(self):
        """Get junk of Source objects for Sources list."""
        context = self.user_context
        fw = context.first  # From here forward
        use_user = context.batch_user()
        args = {"user": use_user, "fw": fw, "count": context.count}
        args['batch_id'] = context.material.batch_id
        if context.series:
            # Filtering by series (Lähdesarja)
            THEMES = {
                "birth": ("syntyneet", "födda"),
                "baptism": ("kastetut", "döpta"),
                "wedding": ("vihityt", "vigda"),
                "death": ("kuolleet", "döda"),
                "move": ("muuttaneet", "flyttade"),
            }
            theme_fi, theme_sv = THEMES[context.series]
            args["theme1"] = theme_fi
            args["theme2"] = theme_sv
        try:
            sources = self.dataservice.dr_get_source_list_fw(args)
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
        res = self.dataservice.dr_get_source_w_repository(use_user, uuid)
        if Status.has_failed(res):
            return res
        source = res.get("item")
        if not source:
            res.statustext = f"no Source with uuid={uuid}"
            return res

        citations, notes, targets = self.dataservice.dr_get_source_citations(
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
                        self.dataservice.dr_inlay_person_lifedata(target)
                    citation.citators.append(target)
                else:
                    print(f"DbReader.get_source_with_references: hide {target}")

            cit.append(citation)
        res["citations"] = cit

        return res
        
class SourceWriter(DataService):
        
    def mergesources(self, id1, id2):
        source = self.dataservice.mergesources(id1,id2)
        return source        
