"""
Created on 30.1.2021

@author: jm
"""
import shareds
from pe.dataservice import DataService
from bl.base import Status
from bl.person import PersonBl
from bl.person_name import Name
from bl.event import EventBl
from bl.family import FamilyBl
from bl.place import PlaceBl, PlaceName
from bl.media import Media
from bl.source import SourceBl

from models.gen.note import Note

# TODO from bl.note import Note
from models.gen.citation import Citation

# TODO from bl.citation import Citation
from models.gen.repository import Repository

# Pick a PlaceName by user language
from ui.place import place_names_local_from_nodes

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
        self.obj_catalog = {}  # dict {uniq_id: Connected_object}

    def _catalog(self, obj):
        """ Add the object to collection of referenced objects. """
        if obj is None:
            return
        if not obj.uniq_id in self.obj_catalog:
            self.obj_catalog[obj.uniq_id] = obj
        else:
            c = self.obj_catalog[obj.uniq_id]
            if c is obj:
                print(
                    f"bl.person_reader.PersonReaderTx._catalog: WARNING same objects twise: {obj}"
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

        res = shareds.dservice.tx_get_person_list(args)

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
        persons = []

        # got {'items': [PersonRecord], 'status': Status.OK}
        #    - PersonRecord = object with fields person_node, names, events_w_role, owners
        #    -    events_w_role = list of tuples (event_node, place_name, role)
        for p_record in res.get("items"):
            # print(p_record)
            node = p_record.person_node
            p = PersonBl.from_node(node)

            # if take_refnames and record['refnames']:
            #     refnlist = sorted(record['refnames'])
            #     p.refnames = ", ".join(refnlist)

            for node in p_record.names:
                pname = Name.from_node(node)
                pname.initial = pname.surname[0] if pname.surname else ""
                p.names.append(pname)

            # Events
            for node, pname, role in p_record.events_w_role:
                if not node is None:
                    e = EventBl.from_node(node)
                    e.place = pname or ""
                    if role and role != "Primary":
                        e.role = role
                    p.events.append(e)

            persons.append(p)

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

    def get_person_data(self, uuid: str):
        """
        Get a Person with all connected nodes for display in Person page as object tree.
        """
        """
        For Person data page we must have all business objects, which has connection
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
              |     |     +-- z:Place (hierarkia)
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
    
        For ex. Sources may be referenced multiple times and we want to process them 
        once only.
        """

        def _extract_place_w_names(pl_reference):
            """Create a PlaceBl node with PlaceNames from a place reference tuple.

            :param:    pl_reference   tuple (Place_node, [PlaceName_node])
            :return:   PlaceBl        created Place node
            """
            place_node, name_nodes = pl_reference
            if place_node:
                place = self.obj_catalog[place_node.id]
                place.names = place_names_local_from_nodes(name_nodes)
                return place
            return None

        # ---/

        res = shareds.dservice.tx_get_person_by_uuid(uuid, active_user=self.use_user)
        if Status.has_failed(res):
            # Not found, not allowd (person.too_new) or error
            if res.get("status") == Status.NOT_FOUND:
                return {
                    "status": Status.NOT_FOUND,
                    "statustext": _("Requested person not found"),
                }
            return res
        # Got dictionary: Status and following objects:
        #     - person_node, root, name_nodes, event_node_roles, cause_of_death, families
        #     - - root = {root_type, root,user, batch_id}
        #     - - event_node_roles = [[Event node, role], ...]
        #     - - cause_of_death = Event node
        #     - - families = [{family_rel, family_role, family_node,
        #                      family_events, relation_type, family_members}, ...]
        #     - - - family_events = [event_node]
        #     - - - family_members = [{member_node, name_node, parental_role, birth_node}, ...]
        #     - - - marriage_date = {datetype, date1, date2}

        # 1-2. Person, names and events

        person = PersonBl.from_node(res.get("person_node"))
        person.families_as_parent = []
        person.families_as_child = []
        person.citation_ref = []
        person.note_ref = []
        person.media_ref = []
        self._catalog(person)

        # Info about linked Batch or Audit node
        root_dict = res.get("root")  # {root_type, root_user, batch_id}
        for name_node in res.get("name_nodes"):
            name = Name.from_node(name_node)
            person.names.append(name)
            self._catalog(name)
        # Events
        for event_node, event_role in res.get("event_node_roles"):
            event = EventBl.from_node(event_node)
            event.role = event_role
            event.citation_ref = []
            person.events.append(event)
            self._catalog(event)
        node = res.get("cause_of_death")
        if node:
            person.cause_of_death = EventBl.from_node(node)
            self._catalog(person.cause_of_death)

        # 3. Person's families as child or parent

        res = shareds.dservice.tx_get_person_families(person.uniq_id)
        if Status.has_failed(res):
            print(
                "#bl.person_reader.PersonReaderTx.get_person_data - Can not read families:"
                f' {res.get("statustext")}'
            )
            return res

        for f in res.get("families"):
            family = FamilyBl.from_node(f["family_node"])
            family_role = f["family_role"]  # Main person's role in family
            self._catalog(family)
            for event_node in f["family_events"]:
                event = EventBl.from_node(event_node)
                if event.type == "Marriage":
                    family.marriage_dates = event.dates
                family.events.append(event)
                self._catalog(event)
            for m in f["family_members"]:
                # Family member
                member = PersonBl.from_node(m["member_node"])
                self._catalog(member)
                name_node = m["name_node"]
                if name_node:
                    name = Name.from_node(name_node)
                    member.names.append(name)
                    self._catalog(name)
                event_node = m["birth_node"]
                if event_node:
                    event = EventBl.from_node(event_node)
                    member.birth_date = event.dates
                    # self._catalog(event)
                # Add member to family
                parental_role = m["parental_role"]  # Family member's role
                if parental_role == "father":
                    family.father = member
                elif parental_role == "mother":
                    family.mother = member
                else:  # children
                    family.children.append(member)

            if family_role:  # main person is a father or mother
                person.families_as_parent.append(family)
                person.events += family.events
            else:  # child
                person.families_as_child.append(family)

            if not self.user_context.use_common():
                family.remove_privacy_limits()

        #    Sort all Person and family Events by date
        person.events.sort()

        # 4. Places for person and each event

        res = shareds.dservice.tx_get_object_places(self.obj_catalog)
        # returns {status, place_references}
        if Status.has_failed(res):
            print(
                "#bl.person_reader.PersonReaderTx.get_person_data - Can not read places:"
                f' {res.get("statustext")}'
            )
            return res

        place_references = res.get("place_references", {})
        # Got dictionary {object_id:  (place_node, (name_nodes))

        # Convert nodes and store them as PlaceBl objects with PlaceNames included
        for pl_node, pn_nodes in place_references.values():
            place = PlaceBl.from_node(pl_node)
            for pn_node in pn_nodes:
                name = PlaceName.from_node(pn_node)
                place.names.append(name)
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

            res = shareds.dservice.tx_get_object_citation_note_media(
                self.obj_catalog, new_ids
            )
            # returns {status, new_objects, references}
            # - new_objects    the objects, for which a new search should be done
            # - references     {source id: [ReferenceObj(node, order, crop)]}
            if Status.has_failed(res):
                print(
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
                        node = current.node
                        order = current.order
                        crop = current.crop
                        (label,) = node.labels
                        # print (f'Link ({src.__class__.__name__} {src_id}:{src.id}) {current}')

                        target_obj = None
                        if label == "Citation":
                            # If id is in the dictionary, return its value.
                            # If not, insert id with a value of 2nd argument.
                            target_obj = citations.setdefault(
                                node.id, Citation.from_node(node)
                            )
                            if hasattr(src, "citation_ref"):
                                src.citation_ref.append(node.id)
                            else:
                                src.citation_ref = [node.id]
                        elif label == "Note":
                            target_obj = notes.setdefault(node.id, Note.from_node(node))
                            if hasattr(src, "note_ref"):
                                src.note_ref.append(node.id)
                            else:
                                src.note_ref = [node.id]
                            target_obj.citation_ref = []
                        elif label == "Media":
                            target_obj = medias.setdefault(
                                node.id, Media.from_node(node)
                            )
                            if hasattr(src, "media_ref"):
                                src.media_ref.append((node.id, crop, order))
                            else:
                                src.media_ref = [(node.id, crop, order)]
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

            # print(f'#+ - found {len(citations)} Citatons, {len(notes)} Notes, {len(medias)} Medias from {cnt} nodes')
            all_citations.update(citations)
            self.obj_catalog.update(citations)
            self.obj_catalog.update(notes)
            self.obj_catalog.update(medias)

        # The average confidence of the sources (person.confidence) has been calculated
        # when creating (or updating) Person

        # 6. Read Sources s and Repositories r for all Citations
        #    for c in z:Citation
        #        (c) --> (s:Source) --> (r:Repository)

        res = shareds.dservice.tx_get_object_sources_repositories(
            list(all_citations.keys())
        )
        if Status.has_failed(res, strict=False):
            print(
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
                node = ref.source_node
                source = SourceBl.from_node(node)
                self._catalog(source)

                # 3.-4. The Repository node and medium from REPOSITORY relation
                node = ref.repository_node
                if node:
                    repo = Repository.from_node(node)
                    repo.medium = ref.medium
                    self._catalog(repo)
                    # This source is in this repository
                    if not repo.uniq_id in source.repositories:
                        source.repositories.append(repo.uniq_id)

                # Referencing a (Source, medium, Repository) tuple
                cita.source_id = source.uniq_id
                # print(f"# ({uniq_id}:Citation) --> (:Source '{source}') --> (:Repository '{repo}')")

        #         # Create Javascript code to create source/citation list
        #         jscode = get_citations_js(shareds.dservice.objs)
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
        """Create code for generating Javascript objecs representing
        Citations, Sources and Repositories with their Notes.

        js-style person[id] = {name: "John", age: 31, city: "New York"}
        """

        def unquote(s):
            """Change quites (") to fancy quotes (“)
            Change new lines to '¤' symbol
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
                js += f'page:"{page}", source_id:{o.source_id}, uuid:"{o.uuid}" '
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
                js += f'uuid:"{o.uuid}" '
                js += "};\n"
                notes.extend(o.note_ref)

            elif isinstance(o, Repository):
                medium = translate(o.medium, "medium")
                atype = translate(o.type, "rept")
                js += f"repositories[{o.uniq_id}] = {{ "
                js += (
                    f'uuid:"{o.uuid}", id:"{o.id}", type:"{atype}", rname:"{o.rname}", '
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
            js += f'uuid:"{o.uuid}", id:"{o.id}", type:"{o.type}", '
            js += f'priv:"{o.priv}", text:"{text}", url:"{url}" '
            js += "};\n"

        return js
