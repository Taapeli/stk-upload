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
Created on 30.1.2021

@author: jm
"""
# blacked
#import shareds
from pe.dataservice import DataService
from bl.base import Status, NodeObject

from bl.source import SourceBl
from bl.citation import Citation
from bl.repository import Repository

# Pick a PlaceName by user language
from ui.place import place_names_local_from_placenames

# TODO Should be somewhere else!
from ui.jinja_filters import translate

import logging

logger = logging.getLogger("stkserver")
from flask_babelex import _

# from models.obsolete_source_citation_reader import get_citations_js


class PersonReaderTx(DataService):
    """
    Data reading class for Person objects with associated data.

    - Returns a Result object.
    """

    def __init__(self, service_name: str, u_context=None):
        # print(f'#~~{self.__class__.__name__} init')
        super().__init__(service_name, u_context)
        self.obj_catalog = {}  # dict {uniq_id: Connected_object: NodeObject}

    def _catalog(self, obj: NodeObject):
        """ Add the object to collection of referenced objects. """
        if obj is None:
            return
        if not obj.uniq_id in self.obj_catalog:
            self.obj_catalog[obj.uniq_id] = obj
        else:
            c = self.obj_catalog[obj.uniq_id]
            if c is obj:
                print(
                    f"bl.person_reader.PersonReaderTx._catalog: WARNING same object twice: {obj}"
                )
                print(obj)
                print(c)

    def get_person_search(self, args):
        """Read Persons with Names, Events, Refnames (reference names) and Places
        and Researcher's username.

        Search by name by args['rule'], args['key']:
            rule=all                  all
            rule=surname, key=name    by start of surname
            rule=firstname, key=name  by start of the first of first names
            rule=patronyme, key=name  by start of patronyme name
            rule=refname, key=name    by exact refname
            rule=years, key=str       by possible living years:
                str='-y2'   untill year
                str='y1'    single year
                str='y1-y2' year range
                str='y1-'   from year

        Origin from bl.person.PersonReader.get_person_search
        TODO: rule=refname: listing with refnames not supported
        """
        if args.get("rule") == "years":
            try:
                lim = args["key"].split("-")
                y1 = int(lim[0]) if lim[0] > "" else -9999
                y2 = int(lim[-1]) if lim[-1] > "" else 9999
                if y1 > y2:
                    y2, y1 = [y1, y2]
                args["years"] = [y1, y2]
            except ValueError:
                return {
                    "statustext": _("The year or years must be numeric"),
                    "status": Status.ERROR,
                }

        #         planned_search = {'rule':args.get('rule'), 'key':args.get('key'),
        #                           'years':args.get('years')}

        context = self.user_context
        args["use_user"] = self.use_user
        args["fw"] = context.first  # From here forward
        args["limit"] = context.count
        args["material"] = context.material
        args["state"] = context.material.state
        res = self.dataservice.tx_get_person_list(args)

        status = res.get("status")
        if status == Status.NOT_FOUND:
            msg = res.get("statustext")
            logger.error(f"bl.person.PersonReader.get_person_search: {msg}")
            print(f"bl.person.PersonReader.get_person_search: {msg}")
            return {
                "items": [],
                "status": res.get("status"),
                "statustext": _("No persons found"),
            }
        if status != Status.OK:
            return res
        persons = res['persons']

        # Update the page scope according to items really found
        if len(persons) > 0:
            context.update_session_scope(
                "person_scope",
                persons[0].sortname,
                persons[-1].sortname,
                context.count,
                len(persons),
            )

        if self.use_user is None:
            persons2 = [p for p in persons if not p.too_new]
            num_hidden = len(persons) - len(persons2)
        else:
            persons2 = persons
            num_hidden = 0
        return {"items": persons2, "num_hidden": num_hidden, "status": status}

    def get_person_data(self, iid: str):
        """
        Get a Person with all connected nodes for display in Person page as object tree.
        """
        """
        For Person data page we need all business objects, which has connection
        to current Person. This is done in the following steps:
    
        1. (p:Person) --> (x:Name|Event)
        2. (p:Person) <-- (f:Family)
           for f
                (f) --> (fp:Person) -[*1]-> (fpn:Name)
                (f) --> (fe:Event)
        3. for z in p, x, fe, z, s, r
               (y) --> (z:Citation|Note|Media)
        4. for pl in z:Place, ph
               (pl) --> (pn:Place_name)
               (pl) --> (ph:Place)
        5. for c in z:Citation
               (c) --> (s:Source) --> (r:Repository)
        
            p:Person
              +-- x:Name
              |     +-- z:Citation (2)
              |     +-- z:Note (3)
              |     +-- z:Media (4)
        (1)   +-- x:Event
              |     +-- z:Place
              |     |     +-- pn:Place_name
              |     |     +-- z:Place (hierarchy)
              |     |     +-- z:Citation (2)
              |     |     +-- z:Note (3)
              |     |     +-- z:Media (4)
              |     +-- z:Citation (2)
              |     +-- z:Note (3)
              |     +-- z:Media (4)
              +-- f:Family
              |     +-- fp:Person
              |     |     +-- fpn:Name
              |     +-- fe:Event (1)
              |     +-- z:Citation (2)
              |     +-- z:Note (3)
              |     +-- z:Media (4)
        (2)   +-- z:Citation
              |     +-- s:Source
              |     |     +-- r:Repository
              |     |     |     +-- z:Citation (2)
              |     |     |     +-- z:Note (3)
              |     |     |     +-- z:Media (4)
              |     |     +-- z:Citation (2)
              |     |     +-- z:Note (3)
              |     |     +-- z:Media (4)
              |     +-- z:Note (3)
              |     +-- z:Media (4)
        (3)    +-- z:Note
              |     +-- z:Citation (2)
              |     +-- z:Media (4)
        (4)   +-- z:Media
                    +-- z:Citation (2)
                    +-- z:Note (3)
          
        The objects are stored in PersonReader.person object p tree.
        - x and f: included objects (in p.names etc)
        - others: reference to "PersonReader.objs" dictionary (p.citation_ref[] etc)
    
        For example Sources may be referenced multiple times and we want to
        process them once only.
        """

        def _extract_place_w_names(pl_reference):
            """Create a PlaceBl node with PlaceNames from a place reference tuple.

            :param:    pl_reference   tuple (Place_node, [PlaceName_node])
            :return:   PlaceBl        created Place node
            """
            place_node, placenames = pl_reference
            if place_node:
                place = self.obj_catalog[place_node.id]
                place.names = place_names_local_from_placenames(placenames)
                return place
            return None

        # ---/

        res = self.dataservice.tx_get_person_by_iid(
            iid, 
            self.user_context.material,
            self.use_user,
        )
        if Status.has_failed(res):
            # Not found, not allowed (person.too_new) or error
            if res.get("status") == Status.NOT_FOUND:
                return {
                    "status": Status.NOT_FOUND,
                    "statustext": _("Requested person not found"),
                }
            return res

        # 1-2. Person, names and events

        # KKu: Collecting Person data except self._catalog calls and root_dict
        #      see -> Neo4jReadServiceTx.tx_get_person_by_iid

        person = res['person']
        root_dict = res.get("root")  # {material, root_user, batch_id}
        self._catalog(person)
        for name in person.names:
            self._catalog(name)
        for event in person.events:
            self._catalog(event)
        self._catalog(person.cause_of_death)
         
        # 3. Person's families as child or parent

        res = self.dataservice.tx_get_person_families(person.uniq_id)
        if Status.has_failed(res):
            logger.error(
                "#bl.person_reader.PersonReaderTx.get_person_data - Can not read families:"
                f' {res.get("statustext")}'
            )
            return res

        # KKu: Collecting Family data
        #      see -> Neo4jReadServiceTx.tx_get_person_by_iid

        families = res['families']
        for family in families:
            self._catalog(family)
            for event in family.events:
                self._catalog(event)
            for member in family.members:
                self._catalog(member)
            if family.family_role:  # main person is a father or mother
                person.families_as_parent.append(family)
                person.events += family.events
            else:  # child
                person.families_as_child.append(family)
 
            if not self.user_context.is_common():
                family.remove_privacy_limits()

        #    Sort all Person and family Events by date
        person.events.sort()

        # 4. Places for person and each event

        res = self.dataservice.tx_get_object_places(self.obj_catalog)
        # returns {status, place_references}
        if Status.has_failed(res):
            logger.error(
                "#bl.person_reader.PersonReaderTx.get_person_data - Can not read places:"
                f' {res.get("statustext")}'
            )
            return res

        place_references = res.get("place_references", {})
        # Got dictionary {object_id:  (place_node, (name_nodes))

        # KKu: Converting nodes to PlaceBl objects with PlaceNames included
        #      see -> Neo4jReadServiceTx.tx_get_person_by_iid

        for place in res['places']:
            self._catalog(place)

        for e in person.events:
            if e.uniq_id in place_references.keys():

                place = _extract_place_w_names(place_references[e.uniq_id])
                if place:
                    e.place_ref = [place.uniq_id]
                    # Add Upper Place, if not set and exists
                    if place.uppers == [] and place.uniq_id in place_references:
                        refs = place_references[place.uniq_id]
                        if refs:
                            up_place = _extract_place_w_names(refs)
                            if up_place:
                                place.uppers = [up_place]

        # 5. Citations, Notes, Medias

        new_ids = [-1]
        all_citations = {}
        while len(new_ids) > 0:
            # New objects
            citations = {}
            notes = {}
            medias = {}

            res = self.dataservice.tx_get_object_citation_note_media(
                self.obj_catalog, new_ids
            )
            # returns {status, new_objects, references}
            # - new_objects    the objects, for which a new search should be done
            # - references     {source id: [ReferenceObj(node, order, crop)]}
            if Status.has_failed(res):
                logger.error(
                    "#bl.person_reader.PersonReaderTx.get_person_data - Can not read citations etc.:"
                    f' {res.get("statustext")}'
                )
                return res
            new_ids = res.get("new_objects", [])
            references = res.get("references")

            for src_id, src in self.obj_catalog.items():
                refs = references.get(src_id)
                if refs:
                    for current in refs:
                        order = current.order
                        crop = current.crop
                        label = current.label
                        # print (f'Link ({src.__class__.__name__} {src_id}:{src.id}) {current}')

                        target_obj = None
                        if label == "Citation":
                            # If id is in the dictionary, return its value.
                            # If not, insert id with a value of 2nd argument.
                            target_obj = citations.setdefault(
                                current.obj.uniq_id, current.obj
                            )
                            if hasattr(src, "citation_ref"):
                                src.citation_ref.append(current.obj.uniq_id)
                            else:
                                src.citation_ref = [current.obj.uniq_id]
                        elif label == "Note":
                            target_obj = notes.setdefault(current.obj.uniq_id, current.obj)
                            if hasattr(src, "note_ref"):
                                src.note_ref.append(current.obj.uniq_id)
                            else:
                                src.note_ref = [current.obj.uniq_id]
                            target_obj.citation_ref = []
                        elif label == "Media":
                            target_obj = medias.setdefault(
                                current.obj.uniq_id, current.obj
                            )
                            if hasattr(src, "media_ref"):
                                src.media_ref.append((current.obj.uniq_id, crop, order))
                            else:
                                src.media_ref = [(current.obj.uniq_id, crop, order)]
                            target_obj.citation_ref = []
                            # Sort the Media references by order
                            # print(f'#\tMedia ref {target_obj.uniq_id} order={order}, crop={crop}')
                            if (
                                len(src.media_ref) > 1
                                and src.media_ref[-2][2] > src.media_ref[-1][2]
                            ):
                                src.media_ref.sort(key=lambda x: x[2])
                                # print("#\tMedia sort done")
                        else:
                            raise NotImplementedError(
                                "Citation, Note or Media excepted, got {label}"
                            )

            # print(f'#+ - found {len(citations)} Citations, {len(notes)} Notes,"\
            #       f" {len(medias)} Medias from {len(new_ids)} nodes')
            # for uniq_id, note in notes.items():
            #     print(f'#+ - {uniq_id}: {note}')
            all_citations.update(citations)
            self.obj_catalog.update(citations)
            self.obj_catalog.update(notes)
            self.obj_catalog.update(medias)

        # The average confidence of the sources (person.confidence) has been calculated
        # when creating (or updating) Person

        # 6. Read Sources s and Repositories r for all Citations
        #    for c in z:Citation
        #        (c) --> (s:Source) --> (r:Repository)

        res = self.dataservice.tx_get_citation_sources_repositories(
            list(all_citations.values())
        )
        if Status.has_failed(res, strict=False):
            logger.error(
                "#bl.person_reader.PersonReaderTx.get_person_data - Can not read repositories:"
                f' {res.get("statustext")}'
            )
            return res
        # res = {'status': Status.OK, 'sources': references}
        #    - references    {Citation.unid_id: SourceReference}
        #        - SourceReference    object with source_node, repository_node, medium

        source_refs = res.get("sources")
        if source_refs:
            for uniq_id, ref in source_refs.items():
                # 1. The Citation node
                cita = self.obj_catalog[uniq_id]

                # 2. The Source node
                source = ref.source_obj
                self._catalog(source)

                # 3.-4. The Repository node and medium from REPOSITORY relation
                repo = ref.repository_obj
                if repo:
                    repo.medium = ref.medium
                    self._catalog(repo)
                    # This source is in this repository
                    if not repo.uniq_id in source.repositories:
                        source.repositories.append(repo.uniq_id)

                # Referencing a (Source, medium, Repository) tuple
                cita.source_id = source.uniq_id
                # print(f"# ({uniq_id}:Citation) --> (:Source '{source}') --> (:Repository '{repo}')")

        #         # Create Javascript code to create source/citation list
        #         jscode = get_citations_js(self.dataservice.objs)
        jscode = self.get_citations_js()

        # Return Person with included objects,  and javascript code to create
        # Citations, Sources and Repositories with their Notes
        return {
            "person": person,
            "objs": self.obj_catalog,
            "jscode": jscode,
            "root": root_dict,
            "status": Status.OK,
        }

    def get_citations_js(self):
        """Create code for generating Javascript objects representing
        Citations, Sources and Repositories with their Notes.

        js-style person[id] = {name: "John", age: 31, city: "New York"}
        """

        def unquote(s):
            """Change quotes (") to fancy quotes (“), change new lines to '¤' symbol.
            """
            return s.replace('"', "“").replace("\n", "¤")

        notes = []
        js = "var citations = {};\nvar sources = {};\n"
        js += "var repositories = {};\nvar notes = {};\n"
        for o in self.obj_catalog.values():
            if isinstance(o, Citation):
                page = unquote(o.page)
                js += f"citations[{o.uniq_id}] = {{ "
                js += f'confidence:"{o.confidence}", dates:"{o.dates}", '
                js += f'id:"{o.id}", note_ref:{o.note_ref}, '
                js += f'page:"{page}", source_id:{o.source_id}, iid:"{o.iid}" '
                js += "};\n"
                notes.extend(o.note_ref)

            elif isinstance(o, SourceBl):
                sauthor = unquote(o.sauthor)
                spubinfo = unquote(o.spubinfo)
                stitle = unquote(o.stitle)
                js += f"sources[{o.uniq_id}] = {{ "
                js += f'id:"{o.id}", note_ref:{o.note_ref}, '
                js += f'repositories:{o.repositories}, sauthor:"{sauthor}", '
                js += f'spubinfo:"{spubinfo}", stitle:"{stitle}", '
                js += f'iid:"{o.iid}" '
                js += "};\n"
                notes.extend(o.note_ref)

            elif isinstance(o, Repository):
                medium = translate(o.medium, "medium")
                atype = translate(o.type, "rept")
                js += f"repositories[{o.uniq_id}] = {{ "
                js += (
                    f'iid:"{o.iid}", id:"{o.id}", type:"{atype}", rname:"{o.rname}", '
                )
                # Media type
                js += f'medium:"{medium}", notes:{o.notes}, sources:{o.sources}'
                js += "};\n"
                notes.extend(o.notes)

            else:
                continue

        # Find referenced Notes; conversion to set removes duplicates
        for uniq_id in set(notes):
            o = self.obj_catalog[uniq_id]
            text = unquote(o.text)
            url = unquote(o.url)
            js += f"notes[{o.uniq_id}] = {{ "
            js += f'iid:"{o.iid}", id:"{o.id}", type:"{o.type}", '
            js += f'priv:"{o.priv}", text:"{text}", url:"{url}" '
            js += "};\n"

        return js
