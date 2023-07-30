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
Created on 17.3.2020

@author: jm
"""
# blacked 12.2.2022/JMä
import logging

logger = logging.getLogger("stkserver")
from flask_babelex import _

from bl.base import Status, IsotammiException
from bl.material import Material
from ui.place import place_names_local_from_nodes

from pe.dataservice import ConcreteService
# from pe.neo4j
from .cypher.cy_source import CypherSource
from .cypher.cy_repository import CypherRepository
from .cypher.cy_family import CypherFamily
from .cypher.cy_event import CypherEvent
from .cypher.cy_person import CypherPerson
from .cypher.cy_media import CypherMedia
from .cypher.cy_comment import CypherComment
from .cypher.cy_root import CypherRoot

from .util import run_cypher, run_cypher_batch, dict_root_node
from .nodereaders import Citation_from_node
from .nodereaders import Comment_from_node
from .nodereaders import DateRange_from_node
from .nodereaders import EventBl_from_node
from .nodereaders import FamilyBl_from_node
from .nodereaders import MediaBl_from_node
from .nodereaders import Note_from_node
from .nodereaders import Name_from_node
from .nodereaders import PersonBl_from_node
from .nodereaders import PlaceBl_from_node
from .nodereaders import PlaceName_from_node
from .nodereaders import Repository_from_node
from .nodereaders import SourceBl_from_node


class Neo4jReadService(ConcreteService):
    """
    Methods for accessing Neo4j database.

    Referenced as shareds.dataservices["read"] class.

    The DataService class enables use as Context Manager.
    @See: https://www.integralist.co.uk/posts/python-context-managers/
    """

    def __init__(self, driver):
        self.driver = driver
        # print(f"#{self.__class__.__name__} init")

    def _set_birth_death(self, person, birth_node, death_node):
        """
        Set person.birth and person.death events from db nodes
        """
        if birth_node:
            person.event_birth = EventBl_from_node(birth_node)
        if death_node:
            person.event_death = EventBl_from_node(death_node)

    def _obj_from_node(self, node, role=None):
        """Create a Place, Event, Person or Family object from db node."""
        if "Person" in node.labels:
            obj = PersonBl_from_node(node)
        elif "Family" in node.labels:
            obj = FamilyBl_from_node(node)
            fn = obj.father_sortname if obj.father_sortname else "?"
            mn = obj.mother_sortname if obj.mother_sortname else "?"
            obj.clearname = fn + " & " + mn
        elif "Event" in node.labels:
            obj = EventBl_from_node(node)
            obj.clearname = _(obj.type) + " " + obj.description + str(obj.dates)
        elif "Place" in node.labels:
            obj = PlaceBl_from_node(node)
            obj.clearname = _(obj.type) + " " + obj.pname
        else:
            # raise NotImplementedError(f'Person or Family expexted: {list(node.labels})')
            logger.warning(
                f"pe.neo4j.read_driver.Neo4jReadService._obj_from_node: {node.id} Person or Family expexted: {list(node.labels)}"
            )
            return None
        obj.role = role if role != "Primary" else None
        return obj

    # ----- Batch (Root)  -----

    def dr_get_material_batches(self, user: str, iid: str):
        """
        Get list of my different materials and accepted all different materials.

        Returns dict {item, status, statustext}
        """
        event = None
        with self.driver.session(default_access_mode="READ") as session:
            try:
                result = run_cypher(session, CypherEvent.get_an_event, user, iid=iid)
                for record in result:
                    if record["e"]:
                        # Record: <Record
                        #    e=<Node id=16580 labels=frozenset({'Event'})
                        #        properties={'datetype': 0, 'change': 1585409701, 'description': '',
                        #            'id': 'E1742', 'date2': 1815589, 'date1': 1815589,
                        #            'type': 'Baptism', 'iid': 'E-6007'}>
                        #    root=<Node id=31100 labels=frozenset({'Audit'})
                        #        properties={'id': '2020-07-28.001', ... 'timestamp': 1596463360673}>
                        # >
                        node = record["e"]
                        event = EventBl_from_node(node)
                if event:
                    return {"item": event, "status": Status.OK}

            except Exception as e:
                return {"item": None, "status": Status.ERROR, "statustext": str(e)}

        return {
            "item": event,
            "status": Status.NOT_FOUND,
            "statustext": "No Event found",
        }

    def dr_get_auditors(self, batch_id):
        """ Read list of the auditors and auditing parameters. """
        class AuditionData: pass
        auditions = []
        with self.driver.session(default_access_mode="READ") as session:
            result = session.run(CypherRoot.get_auditions, bid=batch_id)
            for record in result:
                a = AuditionData()
                a.type = record.get("type")
                a.user = record.get("user")
                a.ts_from = record.get("from", "")
                a.ts_to = record.get("to", "")
                a.auditing = (a.type == "DOES_AUDIT")
                auditions.append(a)

        return {"status": Status.OK, "items": auditions}

    # ------ Persons -----

    # def obsolete_dr_get_person_list(self, _args): --> pe.neo4j.readservice_tx.Neo4jReadServiceTx.tx_get_person_list

    def dr_inlay_person_lifedata(self, person):
        """Reads person's def. name, birth and death event into Person obj."""

        with self.driver.session(default_access_mode="READ") as session:
            result = session.run(CypherSource.get_person_lifedata, pid=person.uniq_id)
            for record in result:
                # <Record
                #    name=<Node id=379934 labels={'Name'}
                #        properties={'firstname': 'Gustaf', 'type': 'Also Known As', 'suffix': '', 'prefix': '',
                #            'surname': 'Johansson', 'order': 0}>
                #    events=[
                #        <Node id=492911 labels={'Event'}
                #            properties={'datetype': 0, 'change': 1577803201, 'description': '',
                #                'id': 'E7750', 'date2': 1853836, 'type': 'Birth', 'date1': 1853836,
                #                'iid': 'E-a7d'}>
                #    ]
                # >
                name_node = record["name"]
                person.names.append(Name_from_node(name_node))
                events = record["events"]
                for node in events:
                    e = EventBl_from_node(node)
                    if e.type == "Birth":
                        person.event_birth = e
                    else:
                        person.event_death = e
        return

    # ------ Events -----

    def dr_get_event_by_iid(self, user: str, iid: str, material: Material):
        """
        Read an Event using iid and username.

        Returns dict {item, status, statustext}
        """
        event = None
        with self.driver.session(default_access_mode="READ") as session:
            try:
                result = run_cypher(
                    session, CypherEvent.get_an_event, user, material, iid=iid
                )
                for record in result:
                    if record["e"]:
                        # Record: <Record
                        #    e=<Node id=16580 labels=frozenset({'Event'})
                        #        properties={'datetype': 0, 'change': 1585409701, 'description': '',
                        #            'id': 'E1742', 'date2': 1815589, 'date1': 1815589,
                        #            'type': 'Baptism', 'iid': 'E-6007'}>
                        #    root=<Node id=31100 labels=frozenset({'Audit'})
                        #        properties={'id': '2020-07-28.001', ... 'timestamp': 1596463360673}>
                        # >
                        node = record["e"]
                        event = EventBl_from_node(node)
                if event:
                    return {"item": event, "status": Status.OK}

            except Exception as e:
                return {"item": None, "status": Status.ERROR, "statustext": str(e)}

        return {
            "item": event,
            "status": Status.NOT_FOUND,
            "statustext": "No Event found",
        }

    def dr_get_event_participants(self, uid):
        """Get people and families connected to this event.

        Returns dict {items, status, statustext}
        """
        try:
            with self.driver.session(default_access_mode="READ") as session:
                result = session.run(CypherEvent.get_event_participants, uid=uid)
                parts = []
                for record in result:
                    # <Record
                    #    role='Primary'
                    #    p=<Node id=24571 labels=frozenset({'Person'})
                    #        properties={'sortname': 'Lekatt#Johan#', 'death_high': 1809,
                    #            'sex': 1, 'change': 1585409698, 'confidence': '2.0',
                    #            'birth_low': 1773, 'birth_high': 1773, 'id': 'I0718',
                    #            'iid': 'H-88fa', 'death_low': 1807}>
                    #    name=<Node id=24572 labels=frozenset({'Name'})
                    #        properties={'firstname': 'Johan', 'surname': 'Lekatt', 'prefix': '',
                    #            'suffix': '', 'type': 'Also Known As', 'order': 0}>
                    # >
                    node = record["p"]
                    role = record["role"]
                    name_node = record["name"]
                    # Create Person or Family
                    referee = self._obj_from_node(node, role)
                    cls_name = referee.__class__.__name__
                    if cls_name == "PersonBl":
                        referee.label = "Person"
                    elif cls_name == "FamilyBl":
                        referee.label = "Family"
                    else:
                        raise TypeError(
                            "dr_get_event_participants: Invalid member class "
                            + cls_name
                        )
                    # Person may have Name
                    if name_node:
                        name = Name_from_node(name_node)
                        referee.names.append(name)
                    parts.append(referee)

        except Exception as e:
            return {
                "status": Status.ERROR,
                "statustext": f"Error dr_get_event_participants: {e}",
            }

        return {"items": parts, "status": Status.OK}

    def dr_get_event_place(self, uid):
        """Get event place(s) of this event with surrounding place.

        Returns dict {items, status, statustext}
        """
        places = []
        try:
            with self.driver.session(default_access_mode="READ") as session:
                result = session.run(CypherEvent.get_event_place, uid=uid, lang="fi")
                for record in result:
                    # Returns place, name, COLLECT(DISTINCT [properties(r), upper,uname]) as upper_n
                    pl = PlaceBl_from_node(record["place"])
                    pl_name = PlaceName_from_node(record["name"])
                    pl.names.append(pl_name)
                    for _rel_prop, upper, uname in record["upper_n"]:
                        pl_upper = PlaceBl_from_node(upper)
                        pl_upper.names.append(PlaceName_from_node(uname))
                        pl.uppers.append(pl_upper)
                    places.append(pl)

        except Exception as e:
            return {
                "status": Status.ERROR,
                "statustext": f"Error dr_get_event_participants: {e}",
            }

        return {"items": places, "status": Status.OK}

    def dr_get_event_notes_medias(self, uid):
        """Get notes and media connected this event.

        Returns dict {items, status, statustext}
        """
        notes = []
        medias = []
        try:
            with self.driver.session(default_access_mode="READ") as session:
                result = session.run(CypherEvent.get_event_notes_medias, uid=uid)
                for record in result:
                    # Return COLLECT(DISTINCT [properties(rel_n), note]) AS notes,
                    #        COLLECT(DISTINCT [properties(rel_m), media]) AS medias
                    for _rel_prop, node in record["notes"]:
                        if node:
                            notes.append(Note_from_node(node))
                    for _rel_prop, node in record["medias"]:
                        # _rel_prop may be {"order":0} (not used)
                        if node:
                            medias.append(MediaBl_from_node(node))

        except Exception as e:
            return {
                "status": Status.ERROR,
                "statustext": f"Error dr_get_event_notes_medias: {e}",
            }

        return {"notes": notes, "medias": medias, "status": Status.OK}

    # ------ Families -----

    def dr_get_family_by_id(self, user: str, material: Material, iid: str):
        """
        Read a Family using isotammi_id or iid and user info.

        Returns dict {item, status, statustext}
        """
        family = None
        with self.driver.session(default_access_mode="READ") as session:
            result = run_cypher(
                session, CypherFamily.get_family_iid, user, material, f_id=iid
            )
            for record in result:
                if record["f"]:
                    # <Record
                    #    f=<Node id=590928 labels={'Family'}
                    #        properties={'datetype': 1, 'father_sortname': 'Gadd#Peter Olofsson#',
                    #            'change': 1560931512, 'rel_type': 'Unknown', 'id': 'F0002',
                    #            'date2': 1766592, 'date1': 1766592, 'iid': 'F-e15a'}>
                    #    root=<Node id=384349 labels={'Batch'}
                    #        properties={'mediapath': '/home/rinminlij1l1j1/paikat_pirkanmaa_yhdistetty_06052020.gpkg.media',
                    #            'file': 'uploads/juha/paikat_pirkanmaa_yhdistetty_6.5.2020_clean.gramps',
                    #            'id': '2020-05-09.001', 'user': 'juha', 'timestamp': 1589022866282, 'status': 'completed'}>
                    # >
                    node = record["f"]
                    family = FamilyBl_from_node(node)
                    family.root = dict_root_node(record["root"])

                return {"item": family, "status": Status.OK}
        return {
            "item": None,
            "status": Status.NOT_FOUND,
            "statustext": "No families found",
        }

    def dr_get_families(self, args):
        """Read Families data ordered by parent name.

        args = dict {use_user:str, direction:str="fw", name:str=None, limit:int=50, rule:str"man"}
        """
        user = args.get("use_user", None)
        direction = args.get("direction", "fw")  # "fw" forwars or "bw" backwrds
        if direction != "fw":
            raise NotImplementedError(
                "Neo4jReadService.dr_get_families: Only fw implemented"
            )

        fw = args.get("name")  # first name
        limit = args.get("limit", 50)
        order = args.get("order", "man")  # "man" or "wife" name order
        material = args.get("material")

        # Select True = filter by this user False = filter approved data
        # show_candidate = self.user_context.use_owner_filter()
        with self.driver.session(default_access_mode="READ") as session:
            if order == "man":
                print("Neo4jReadService.dr_get_families: candidate ordered by man")
                result = run_cypher_batch(
                    session,
                    CypherFamily.get_families_by_father,
                    user,
                    material,
                    fw=fw,
                    limit=limit,
                )
            elif order == "wife":
                print("Neo4jReadService.dr_get_families: candidate ordered by wife")
                result = run_cypher_batch(
                    session,
                    CypherFamily.get_families_by_mother,
                    user,
                    material,
                    fw=fw,
                    limit=limit,
                )

            families = []
            for record in result:
                # record.keys() = ['f', 'marriage_place', 'parent', 'child', 'no_of_children']
                if record["f"]:
                    # <Node id=55577 labels={'Family'}
                    #    properties={'rel_type': 'Married', 'handle': '_d78e9a206e0772ede0d',
                    #    'id': 'F0000', 'change': 1507492602}>
                    f_node = record["f"]
                    family = FamilyBl_from_node(f_node)
                    family.marriage_place = record["marriage_place"]

                    uniq_id = -1
                    for role, parent_node, name_node in record["parent"]:
                        if parent_node:
                            # <Node id=214500 labels={'Person'}
                            #    properties={'sortname': 'Airola#ent. Silius#Kalle Kustaa',
                            #    'datetype': 19, 'confidence': '2.7', 'change': 1504606496,
                            #    'sex': 0, 'handle': '_ce373c1941d452bd5eb', 'id': 'I0008',
                            #    'date2': 1997946, 'date1': 1929380}>
                            if uniq_id != parent_node.id:
                                # Skip person with double default name
                                pp = PersonBl_from_node(parent_node)
                                if role == "father":
                                    family.father = pp
                                elif role == "mother":
                                    family.mother = pp

                            pname = Name_from_node(name_node)
                            pp.names = [pname]

                    for ch in record["child"]:
                        # <Node id=60320 labels={'Person'}
                        #    properties={'sortname': '#Björnsson#Simon', 'datetype': 19,
                        #    'confidence': '', 'sex': 0, 'change': 1507492602,
                        #    'handle': '_d78e9a2696000bfd2e0', 'id': 'I0001',
                        #    'date2': 1609920, 'date1': 1609920}>
                        #                         child = Person_as_member()
                        child = PersonBl_from_node(ch)
                        family.children.append(child)
                    family.children.sort(key=lambda x: x.birth_low)

                    if record["no_of_children"]:
                        family.no_of_children = record["no_of_children"]
                    family.num_hidden_children = 0
                    if not args.get("is_common"):
                        if family.father:
                            family.father.too_new = False
                        if family.mother:
                            family.mother.too_new = False
                    families.append(family)
            status = Status.OK if families else Status.NOT_FOUND
            return {"families": families, "status": status}

    def dr_get_family_parents(self, uniq_id: int, with_name=True):
        """
        Get Parent nodes, optionally with default Name

        returns dict {items, status, statustext}
        """
        parents = []
        with self.driver.session(default_access_mode="READ") as session:
            try:
                result = session.run(CypherFamily.get_family_parents, fuid=uniq_id)
                for record in result:
                    # <Record
                    #    role='father'
                    #    parent=<Node id=550536 labels={'Person'}
                    #        properties={'sortname': 'Linderoos#Johan Wilhelm#', 'death_high': 1844,
                    #            'confidence': '2.0', 'sex': 1, 'change': 1585409699, 'birth_low': 1788,
                    #            'birth_high': 1788, 'id': 'I1314', 'iid': 'F-f9e2',
                    #            'death_low': 1844}>
                    #    name=<Node id=550537 labels={'Name'}
                    #        properties={'firstname': 'Johan Wilhelm', 'type': 'Birth Name',
                    #            'suffix': '', 'prefix': '', 'surname': 'Linderoos', 'order': 0}>
                    #    birth=<Node id=543985 labels={'Event'}
                    #        properties={'datetype': 0, 'change': 1585409702, 'description': '',
                    #            'id': 'E4460', 'date2': 1831101, 'type': 'Birth', 'date1': 1831101,
                    #            'iid': 'E-774'}>
                    #   death=<Node id=543986 labels={'Event'} properties={'id': 'E4461', ...}>
                    # >

                    role = record["role"]
                    person_node = record["person"]
                    if person_node:
                        if uniq_id != person_node.id:
                            # Skip person with double default name
                            p = PersonBl_from_node(person_node)
                            p.role = role
                            name_node = record["name"]
                            if name_node:
                                p.names.append(Name_from_node(name_node))

                            birth_node = record["birth"]
                            death_node = record["death"]
                            self._set_birth_death(p, birth_node, death_node)

                            parents.append(p)

            except Exception as e:
                return {
                    "status": Status.ERROR,
                    "statustext": f"Error dr_get_family_parents: {e}",
                }

        return {"items": parents, "status": Status.OK, "statustext": ""}

    def dr_get_family_children(self, uniq_id, with_events=True, with_names=True):
        """
        Get Child nodes, optionally with Birth and Death nodes

            returns dict {items, status, statustext}
        """
        children = []
        with self.driver.session(default_access_mode="READ") as session:
            try:
                result = session.run(CypherFamily.get_family_children, fuid=uniq_id)
                for record in result:
                    # <Record
                    #    person=<Node id=550538 labels={'Person'}
                    #        properties={'sortname': 'Linderoos#Gustaf Mathias Israel#',...}>
                    #    name=<Node id=550539 labels={'Name'}
                    #        properties={'firstname': 'Gustaf Mathias Israel', 'type': 'Birth Name',...'order': 0}>
                    #    birth=<Node id=543988 labels={'Event'}
                    #        properties={'id': 'E4463', 'type': 'Birth', ...}>
                    #    death=None
                    # >
                    person_node = record["person"]
                    if person_node:
                        p = PersonBl_from_node(person_node)
                        name_node = record["name"]
                        if name_node:
                            p.names.append(Name_from_node(name_node))
                        birth_node = record["birth"]
                        death_node = record["death"]
                        self._set_birth_death(p, birth_node, death_node)

                        children.append(p)

            except Exception as e:
                return {
                    "status": Status.ERROR,
                    "statustext": f"Error dr_get_family_children: {e}",
                }

        return {"items": children, "status": Status.OK}

    def dr_get_family_events(self, uniq_id, with_places=True):
        """
        4. Get family Events node with Places

        returns dict {items, status, statustext}
        """
        events = []
        with self.driver.session(default_access_mode="READ") as session:
            try:
                result = session.run(CypherFamily.get_events_w_places, fuid=uniq_id)
                # RETURN event, place, names,
                #        COLLECT(DISTINCT [place_in, rel_in, COLLECT in_names]) AS inside
                for record in result:
                    event_node = record["event"]
                    if event_node:
                        #    event=<Node id=543995 labels={'Event'}
                        #        properties={'datetype': 0, 'change': 1585409702, 'description': '',
                        #            'id': 'E0170', 'date2': 1860684, 'type': 'Marriage', 'date1': 1860684,
                        #            'iid': 'E-b219'}>
                        e = EventBl_from_node(event_node)

                        place_node = record["place"]
                        if place_node:
                            #    place=<Node id=531912 labels={'Place'}
                            #        properties={'id': 'P1077', 'type': 'Parish', 'iid': 'P-1a4',
                            #            'pname': 'Loviisan srk', 'change': 1585562874}>
                            #    names=[ <Node id=531913 labels={'Place_name'}
                            #                properties={'name': 'Loviisan srk', 'lang': ''}>
                            #        ]
                            e.place = PlaceBl_from_node(place_node)
                            e.place.names = place_names_local_from_nodes(
                                record["names"]
                            )

                        for inside_node, inside_rel, inside_names in record["inside"]:
                            if inside_node:
                                # <Node id=5494 labels=frozenset({'Place'})
                                #     properties={'id': 'P0024', 'type': 'Country', 'iid': 'P-5c',
                                #         'pname': 'Venäjä', 'change': 1585409705}>
                                # <Relationship id=6192
                                #     nodes=(
                                #         <Node id=5788 labels=frozenset({'Place'})
                                #             properties={'coord': [60.70911111111111, 28.745330555555558],
                                #                 'pname': 'Viipuri', 'change': 1585409704, 'id': 'P0011',
                                #                 'type': 'City', 'iid': 'P-cf5'}>,
                                #         <Node id=5494 labels=frozenset({'Place'})
                                #             properties={'id': 'P0024', 'type': 'Country', 'iid': 'P-805c',
                                #                 'pname': 'Venäjä', 'change': 1585409705}>
                                #     )
                                #     type='IS_INSIDE'
                                #     properties={'datetype': 2, 'date2': 2040000, 'date1': 2040000}
                                # >
                                # [
                                #     <Node id=5496 labels=frozenset({'Place_name'}) properties={'name': 'Ryssland', 'lang': 'sv'}>
                                #     <Node id=5495 labels=frozenset({'Place_name'}) properties={'name': 'Venäjä', 'lang': ''}>
                                # ]
                                pl_in = PlaceBl_from_node(inside_node)
                                if len(inside_rel._properties):
                                    pl_in.dates = DateRange_from_node(
                                        inside_rel._properties
                                    )

                                pl_in.names = place_names_local_from_nodes(inside_names)
                                e.place.uppers.append(pl_in)

                        events.append(e)

            except Exception as e:
                return {
                    "status": Status.ERROR,
                    "statustext": f"Error dr_get_family_events: {e}",
                }

        return {"items": events, "status": Status.OK}

    def dr_get_family_sources(self, id_list, with_notes=True):
        """
        Get Sources Citations and Repositories for given families and events.

        The id_list should include the uniq_ids for Family and events Events

        returns dict {items, status, statustext}
        """
        sources = []
        with self.driver.session(default_access_mode="READ") as session:
            try:
                result = session.run(CypherFamily.get_family_sources, id_list=id_list)
                for record in result:
                    # <Record
                    #    src_id=543995
                    #    repository=<Node id=529693 labels={'Repository'}
                    #        properties={'id': 'R0179', 'rname': 'Loviisan seurakunnan arkisto', 'type': 'Archive', 'iid': 'R-e45', 'change': 1585409708}>
                    #    source=<Node id=534511 labels={'Source'}
                    #        properties={'id': 'S0876', 'stitle': 'Loviisan srk - vihityt 1794-1837', 'iid': 'S-82b',
                    #            'spubinfo': 'MKO131-133', 'change': 1585409705, 'sauthor': ''}>
                    #    citation=<Node id=537795 labels={'Citation'}
                    #        properties={'id': 'C2598', 'page': '1817 Mars 13', 'iid': 'N-d23',
                    #            'change': 1585409707, 'confidence': '2'}>
                    # >
                    repository_node = record["repository"]
                    if repository_node:
                        source_node = record["source"]
                        citation_node = record["citation"]
                        src_id = record["src_id"]

                        source = SourceBl_from_node(source_node)
                        cita = Citation_from_node(citation_node)
                        repo = Repository_from_node(repository_node)
                        source.repositories.append(repo)
                        source.citations.append(cita)
                        source.referrer = src_id
                        sources.append(source)
            except Exception as e:
                return {
                    "status": Status.ERROR,
                    "statustext": f"Error dr_get_family_sources: {e}",
                }

        return {"items": sources, "status": Status.OK}

    def dr_get_family_notes(self, id_list: list):
        """
        Get Notes for family and events
        The id_list should include the uniq_ids for Family and events Events

        returns dict {items, status, statustext}
        """
        notes = []
        with self.driver.session(default_access_mode="READ") as session:
            try:
                result = session.run(CypherFamily.get_family_notes, id_list=id_list)
                for record in result:
                    # <Record
                    #    src_id=543995
                    #    repository=<Node id=529693 labels={'Repository'}
                    #        properties={'id': 'R0179', 'rname': 'Loviisan seurakunnan arkisto', 'type': 'Archive', 'iid': 'R-45', 'change': 1585409708}>
                    #    source=<Node id=534511 labels={'Source'}
                    #        properties={'id': 'S0876', 'stitle': 'Loviisan srk - vihityt 1794-1837', 'iid': 'S-82b',
                    #            'spubinfo': 'MKO131-133', 'change': 1585409705, 'sauthor': ''}>
                    #    citation=<Node id=537795 labels={'Citation'}
                    #        properties={'id': 'C2598', 'page': '1817 Mars 13', 'iid': 'C-d23',
                    #            'change': 1585409707, 'confidence': '2'}>
                    # >
                    note_node = record["note"]
                    if note_node:
                        src_id = record["src_id"]
                        note = Note_from_node(note_node)
                        note.referrer = src_id
                        notes.append(note)

            except Exception as e:
                return {
                    "status": Status.ERROR,
                    "statustext": f"Error dr_get_family_notes: {e}",
                }

        return {"items": notes, "status": Status.OK}

    #   @functools.lru_cache
    def dr_get_family_members_by_id(self, oid, which):
        """
        Get the minimal data required for creating graphs with person labels.
        The target depends on which = ('person', 'parents', 'children').
        For which='person', the oid should contain an iid.
        For 'parents' and 'children' the oid should contain a database uniq_id.
        The 'death_high' value is always returned for privacy checks.
        """
        switcher = {
            "person": CypherPerson.get_person_for_graph,
            "parents": CypherPerson.get_persons_parents,
            "children": CypherPerson.get_persons_children,
        }
        result_list = []
        with self.driver.session(default_access_mode="READ") as session:
            result = session.run(switcher.get(which), ids=[oid])
            for record in result:
                result_list.append(
                    {
                        "uniq_id": record["uniq_id"],
                        "iid": record["iid"],
                        "sortname": record["sortname"],
                        "gender": record["gender"],
                        "events": record["events"],
                        "death_high": record["death_high"],
                    }
                )
        return result_list

    def dr_get_person_families_iid(self, iid):
        """
        Get the Families where Person is a member (parent or child).

        Returns dict {items, status, statustext}

        Family.parents[] has mother and father Person objects with
        corresponding .role (the fields .father and .mother are not used).
        """
        families = {}
        with self.driver.session(default_access_mode="READ") as session:
            try:
                result = session.run(CypherFamily.get_person_families, p_iid=iid)
                for record in result:
                    # <Record
                    #    family=<Node id=552768 labels={'Family'}
                    #        properties={'datetype': 3, 'father_sortname': 'Åkerberg#Mathias#Andersson',
                    #            'change': 1585409700, 'rel_type': 'Married', 'mother_sortname': 'Unonius#Catharina Ulrica#',
                    #            'id': 'F0011', 'date2': 1842189, 'date1': 1834016, 'iid': 'F-2a'}>
                    #    type='PARENT'
                    #    role='father'
                    #    person=<Node id=547514 labels={'Person'}
                    #        properties={'sortname': 'Åkerberg#Mathias#Andersson', 'death_high': 1831, 'confidence': '2.6',
                    #            'sex': 1, 'change': 1585409697, 'birth_low': 1750, 'birth_high': 1750, 'id': 'I0022',
                    #            'iid': 'P-d89', 'death_low': 1831}>
                    #    birth=<Node id=539796 labels={'Event'}
                    #        properties={'datetype': 0, 'change': 1585409700, 'description': '', 'id': 'E0238',
                    #            'date2': 1792123, 'type': 'Birth', 'date1': 1792123, 'iid': 'E-fa7'}>
                    # >
                    family_node = record["family"]
                    fid = family_node.id
                    if not fid in families:
                        # New family
                        family = FamilyBl_from_node(family_node)
                        family.parents = []
                        families[fid] = family
                    family = families[fid]
                    person_node = record["person"]
                    person = PersonBl_from_node(person_node)
                    birth_node = record["birth"]
                    if birth_node:
                        birth = EventBl_from_node(birth_node)
                        person.event_birth = birth
                    if record["type"] == "PARENT":
                        person.role = record["role"]
                        family.parents.append(person)
                        if iid == person.iid:
                            family.role = "parent"
                            print(
                                f"# Family {family.id} {family.role} --> {person.id} ({person.role})"
                            )
                    else:
                        person.role = "child"
                        family.children.append(person)
                        if iid == person.iid:
                            family.role = "child"
                            print(f"# Family {family.id} {family.role} --> {person.id}")

                if not families:
                    return {
                        "status": Status.NOT_FOUND,
                        "statustext": f"No families for this person",
                    }

                # Sort parents always on same order
                for family in families.values():
                    if len(family.parents) > 1:
                        family.parents.sort(key=lambda x: x.role)

            except Exception as e:
                return {
                    "status": Status.ERROR,
                    "statustext": f"Error dr_get_person_families: {e}",
                }

        return {"items": list(families.values()), "status": Status.OK}

    # # ------ Places ----- # Moved to --> pe.neo4j.readservice_tx.Neo4jReadServiceTx
    #
    # def dr_get_place_list_fw(self, user, fw_from, limit, lang, material):
    #     """Read place list from given start point"""
    #     ret = []
    #     if lang not in ["fi", "sv"]:
    #         lang = "fi"
    #     with self.driver.session(default_access_mode="READ") as session:
    #         print("Neo4jReadService.dr_get_place_list_fw")
    #         result = run_cypher_batch(
    #             session,
    #             CypherPlace.get_name_hierarchies,
    #             user,
    #             material,
    #             fw=fw_from,
    #             limit=limit,
    #             lang=lang,
    #         )
    #         for record in result:
    #             # <Record
    #             #    place=<Node id=514341 labels={'Place'}
    #             #        properties={'coord': [61.49, 23.76],
    #             #            'id': 'P0300', 'type': 'City', 'iid': 'P-484',
    #             #            'pname': 'Tampere', 'change': 1585409704}>
    #             #    name=<Node id=514342 labels={'Place_name'}
    #             #        properties={'name': 'Tampere', 'lang': ''}>
    #             #    names=[<Node id=514344 labels={'Place_name'}
    #             #            properties={'name': 'Tampereen kaupunki', 'lang': ''}>,
    #             #        <Node id=514343 ...>]
    #             #    uses=4
    #             #    upper=[[514289, 'b16a6ee2c7a24e399d45554faa8fb094', 'Country', 'Finnland', 'de'],
    #             #        [514289, 'b16a6ee2c7a24e399d45554faa8fb094', 'Country', 'Finland', 'sv'],
    #             #        [514289, 'b16a6ee2c7a24e399d45554faa8fb094', 'Country', 'Suomi', '']
    #             #    ]
    #             #    lower=[[None, None, None, None, None]]>
    #             node = record["place"]
    #             p = PlaceBl_from_node(node)
    #             p.ref_cnt = record["uses"]
    #
    #             # Set place names and default display name pname
    #             node = record["name"]
    #             p.names.append(PlaceName_from_node(node))
    #             oth_names = []
    #             for node in record["names"]:
    #                 oth_names.append(PlaceName_from_node(node))
    #             # Arrage names by local language first
    #             lst = PlaceName.arrange_names(oth_names)
    #
    #             p.names += lst
    #             p.pname = p.names[0].name
    #             p.uppers = PlaceBl.combine_places(record["upper"], lang)
    #             p.lowers = PlaceBl.combine_places(record["lower"], lang)
    #             ret.append(p)
    #
    #     # Return sorted by first name in the list p.names -> p.pname
    #     return sorted(ret, key=lambda x: x.pname)
    #
    # def dr_get_place_w_names_notes_medias(self, user, iid, lang, material):
    #     """Returns the PlaceBl with PlaceNames, Notes and Medias included."""
    #     pl = None
    #     node_ids = []  # List of uniq_is for place, name, note and media nodes
    #     with self.driver.session(default_access_mode="READ") as session:
    #         result = run_cypher(
    #             session,
    #             CypherPlace.get_w_names_notes,
    #             user,
    #             material,
    #             iid=iid,
    #             lang=lang,
    #         )
    #         for record in result:
    #             # <Record
    #             #    place=<Node id=514286 labels={'Place'}
    #             #        properties={'coord': [60.45138888888889, 22.266666666666666],
    #             #            'id': 'P0007', 'type': 'City', 'iid': 'P-e21a',
    #             #            'pname': 'Turku', 'change': 1585409704}>
    #             #    name=<Node id=514288 labels={'Place_name'}
    #             #        properties={'name': 'Åbo', 'lang': 'sv'}>
    #             #    names=[<Node id=514287 labels={'Place_name'}
    #             #                properties={'name': 'Turku', 'lang': ''}>]
    #             #    notes=[<Node id=582777 labels=frozenset({'Note'}) properties=...>]
    #             #    medias=[]
    #             # >
    #
    #             node = record["place"]
    #             pl = PlaceBl_from_node(node)
    #             node_ids.append(pl.uniq_id)
    #             # Default lang name
    #             name_node = record["name"]
    #             if name_node:
    #                 pl.names.append(PlaceName_from_node(name_node))
    #             # Other name versions
    #             for name_node in record["names"]:
    #                 pl.names.append(PlaceName_from_node(name_node))
    #                 node_ids.append(pl.names[-1].uniq_id)
    #
    #             for notes_node in record["notes"]:
    #                 n = Note_from_node(notes_node)
    #                 pl.notes.append(n)
    #                 node_ids.append(pl.notes[-1].uniq_id)
    #
    #             for medias_node in record["medias"]:
    #                 m = MediaBl_from_node(medias_node)
    #                 # Todo: should replace pl.media_ref[] <-- pl.medias[]
    #                 pl.media_ref.append(m)
    #                 node_ids.append(pl.media_ref[-1].uniq_id)
    #
    #     return {"place": pl, "uniq_ids": node_ids}
    #
    # def dr_get_place_tree(self, locid, lang="fi"):
    #     """Read upper and lower places around this place.
    #
    #     Haetaan koko paikkojen ketju paikan locid ympärillä
    #     Palauttaa listan paikka-olioita ylimmästä alimpaan.
    #     Jos hierarkiaa ei ole, listalla on vain oma Place_combo.
    #
    #     Esim. Tuutarin hierarkia
    #           2 Venäjä -> 1 Inkeri -> 0 Tuutari -> -1 Nurkkala
    #           tulee tietokannasta näin:
    #     ╒════╤═══════╤═════════╤══════════╤═══════╤═════════╤═════════╕
    #     │"lv"│"id1"  │"type1"  │"name1"   │"id2"  │"type2"  │"name2"  │
    #     ╞════╪═══════╪═════════╪══════════╪═══════╪═════════╪═════════╡
    #     │"2" │"21774"│"Region" │"Tuutari" │"21747"│"Country"│"Venäjä" │
    #     ├────┼───────┼─────────┼──────────┼───────┼─────────┼─────────┤
    #     │"1" │"21774"│"Region" │"Tuutari" │"21773"│"State"  │"Inkeri" │
    #     ├────┼───────┼─────────┼──────────┼───────┼─────────┼─────────┤
    #     │"-1"│"21775"│"Village"│"Nurkkala"│"21774"│"Region" │"Tuutari"│
    #     └────┴───────┴─────────┴──────────┴───────┴─────────┴─────────┘
    #     Metodi palauttaa siitä listan
    #         Place(result[0].id2) # Artjärvi City
    #         Place(result[0].id1) # Männistö Village
    #         Place(result[1].id1) # Pekkala Farm
    #     Muuttuja lv on taso:
    #         >0 = ylemmät,
    #          0 = tämä,
    #         <0 = alemmat
    #     """
    #     t = DbTree(self.driver, CypherPlace.read_pl_hierarchy, "pname", "type")
    #     t.load_to_tree_struct(locid)
    #     if t.tree.depth() == 0:
    #         # Vain ROOT-solmu: Tällä paikalla ei ole hierarkiaa.
    #         # Hae oman paikan tiedot ilman yhteyksiä
    #         with self.driver.session(default_access_mode="READ") as session:
    #             result = session.run(CypherPlace.root_query, locid=int(locid))
    #             record = result.single()
    #             t.tree.create_node(
    #                 record["name"],
    #                 locid,
    #                 parent=0,
    #                 data={"type": record["type"], "iid": record["iid"]},
    #             )
    #     ret = []
    #     for tnode in t.tree.expand_tree(mode=t.tree.DEPTH):
    #         logger.debug(
    #             f"{t.tree.depth(t.tree[tnode])} {t.tree[tnode]} {t.tree[tnode].bpointer}"
    #         )
    #         if tnode != 0:
    #             n = t.tree[tnode]
    #
    #             # Get all names: default lang: 'name' and others: 'names'
    #             with self.driver.session(default_access_mode="READ") as session:
    #                 result = session.run(
    #                     CypherPlace.read_pl_names, locid=tnode, lang=lang
    #                 )
    #                 record = result.single()
    #                 # <Record
    #                 #    name=<Node id=514413 labels={'Place_name'}
    #                 #        properties={'name': 'Suomi', 'lang': ''}>
    #                 #    names=[<Node id=514415 labels={'Place_name'}
    #                 #            properties={'name': 'Finnland', 'lang': 'de'}>,
    #                 #        <Node id=514414 labels={'Place_name'} ...}>
    #                 #    ]
    #                 # >
    #             lv = t.tree.depth(n)
    #             p = PlaceBl(uniq_id=tnode, ptype=n.data["type"], level=lv)
    #             p.iid = n.data["iid"]
    #             node = record["name"]
    #             if node:
    #                 p.names.append(PlaceName_from_node(node))
    #             oth_names = []
    #             for node in record["names"]:
    #                 oth_names.append(PlaceName_from_node(node))
    #             # Arrage names by local language first
    #             lst = PlaceName.arrange_names(oth_names)
    #             p.names += lst
    #
    #             p.pname = p.names[0].name
    #             # logger.info("# {}".format(p))
    #             p.parent = n.bpointer
    #             ret.append(p)
    #     return ret
    #
    # def dr_get_place_events(self, uniq_id, privacy):
    #     """Find events and persons associated to given Place.
    #
    #         :param: uniq_id    current place uniq_id
    #         :param: privacy    True, if not showing live people
    #     """
    #     result = self.driver.session(default_access_mode="READ").run(
    #         CypherPlace.get_person_family_events, locid=uniq_id
    #     )
    #     ret = []
    #     for record in result:
    #         # <Record
    #         #    indi=<Node id=523974 labels={'Person'}
    #         #        properties={'sortname': 'Borg#Maria Charlotta#', 'death_high': 1897,
    #         #            'confidence': '', 'sex': 2, 'change': 1585409709, 'birth_low': 1841,
    #         #            'birth_high': 1841, 'id': 'I0029', 'iid': 'H-9cd',
    #         #            'death_low': 1897}>
    #         #    role='Primary'
    #         #    names=[<Node id=523975 labels={'Name'}
    #         #            properties={'firstname': 'Maria Charlotta', 'type': 'Birth Name',
    #         #                'suffix': '', 'surname': 'Borg', 'prefix': '', 'order': 0}>,
    #         #        <Node id=523976 labels={'Name'} properties={...}>]
    #         #    event=<Node id=523891 labels={'Event'}
    #         #            properties={'datetype': 0, 'change': 1585409700, 'description': '',
    #         #                'id': 'E0080', 'date2': 1885458, 'type': 'Birth', 'date1': 1885458,
    #         #                'iid': 'E-5f9'}>
    #         # >
    #         e = EventBl_from_node(record["event"])
    #         # Fields uid (person uniq_id) and names are on standard in EventBl
    #         e.role = record["role"]
    #         indi_label = list(record["indi"].labels)[0]
    #         # if indi_label in ["Audit", "Batch"]:
    #         #     continue
    #         if "Person" == indi_label:
    #             e.indi_label = "Person"
    #             e.indi = PersonBl_from_node(record["indi"])
    #             # Reading confidental person data which is available to this user?
    #             if not privacy:
    #                 e.indi.too_new = False
    #             elif e.indi.too_new:  # Check privacy
    #                 continue
    #             for node in record["names"]:
    #                 e.indi.names.append(Name_from_node(node))
    #             ##ret.append({'event':e, 'indi':e.indi, 'label':'Person'})
    #             ret.append(e)
    #         elif "Family" == indi_label:
    #             e.indi_label = "Family"
    #             e.indi = FamilyBl_from_node(record["indi"])
    #             ##ret.append({'event':e, 'indi':e.indi, 'label':'Family'})
    #             ret.append(e)
    #         else:  # Root
    #             pass
    #             # print(
    #             #     f"dr_get_place_events: No Person or Family:"
    #             #     f" {e.id} {list(record['indi'].labels)[0]} {record['indi'].get('id')}"
    #             # )
    #     return {"items": ret, "status": Status.OK}

    # ------ Sources -----

    def dr_get_source_list_fw(self, args):
        """Read all sources with notes and repositories, optionally limited by keywords.

        used keyword arguments:
        - user        Username to select data
        - theme1      A keyword (fi) for selecting source titles
        - theme2      Another keyword (sv) for selecting source titles
        - fw          Read sources starting from this keyword
        - count       How many sources to read

        Todo: Valinta vuosien mukaan
        Todo: tuloksen sivuttaminen esim. 100 kpl / sivu
        """
        sources = []
        user = args.get("user")
        material = args.get("material")

        with self.driver.session(default_access_mode="READ") as session:
            if args.get("theme1"):
                # Filter sources by searching keywords in fi and sv language
                key1 = args.get("theme1")
                key2 = args.get("theme2")
                # Show my researcher data
                print(f"dr_get_source_list_fw: my researcher data: {key1!r} {key2!r}")
                result = run_cypher_batch(
                    session,
                    CypherSource.get_sources_with_selections,
                    user,
                    material,
                    key1=key1,
                    key2=key2,
                )
            else:
                # Show all themes
                result = run_cypher_batch(
                    session, CypherSource.get_sources, user, material
                )

            for record in result:
                # <Record
                # 0  root=<Node element_id='155335' labels=frozenset({'Root'}) 
                #        properties={'material': 'Family Tree', 'state': 'Accepted', 
                #            'id': '2021-08-29.003', 'user': 'juha', ...}>
                # 1  source=<Node id=242567 labels={'Source'}
                #        properties={'handle': '_dcb5682a0f47b7de686b3251557', 'id': 'S0334',
                #            'stitle': 'Åbo stifts herdaminne 1554-1640', 'change': '1516698633'}>
                # 2  notes=[<Node id=238491 labels={'Note'}
                #        properties={'handle': '_e07cd6210c57e0d53393a62fa7a', 'id': 'N3952',
                #        'text': '', 'type': 'Source Note', 'url': 'http://www.narc.fi:8080/...',
                #        'change': 1542667331}>]
                # 3  repositories=[
                #        ['Book', <Node id=238996 labels={'Repository'}
                #            properties={'handle': '_db51a3f358e67ac82ade828edd1', 'id': 'R0057',
                #            'rname': 'Painoteokset', 'type': 'Collection', 'change': '1541350910'}>]]
                # 4  cit_cnt=1
                # 5  ref_cnt=1
                # >
                node = record["source"]
                s = SourceBl_from_node(node)
                s.root = dict_root_node(record["root"])
                notes = record["notes"]
                for node in notes:
                    n = Note_from_node(node)
                    s.notes.append(n)
                repositories = record["repositories"]
                for medium, node in repositories:
                    if node:
                        rep = Repository_from_node(node)
                        rep.medium = medium
                        s.repositories.append(rep)
                s.cit_cnt = record["cit_cnt"]
                s.ref_cnt = record["ref_cnt"]
                sources.append(s)

        return sources

    def dr_get_source_w_repository(self, user: str, material: Material, iid: str):
        """Returns the Source with Repositories and Notes."""
        source = None
        with self.driver.session(default_access_mode="READ") as session:
            result = run_cypher(
                session, CypherSource.get_source_iid, user, material, iid=iid
            )
            for record in result:
                # <Record
                #    owner_type='PASSED'
                #    source=<Node id=340694 labels={'Source'}
                #        properties={'id': 'S1112', 'stitle': 'Aamulehti (sanomalehti)',
                #            'iid': 'S-e1', 'spubinfo': '',
                #            'sauthor': '', 'change': 1585409705}>
                #    notes=[]
                #    reps=[
                #        ['Book', <Node id=337715 labels={'Repository'}
                #            properties={'id': 'R0002', 'rname': 'Kansalliskirjaston digitoidut sanomalehdet',
                #                'type': 'Collection', 'iid': 'R-f9',
                #                'change': 1585409708}>]]
                # >
                source_node = record["source"]
                source = SourceBl_from_node(source_node)
                source.root = dict_root_node(record["root"])
                notes = record["notes"]
                for note_node in notes:
                    n = Note_from_node(note_node)
                    source.notes.append(n)
                repositories = record["reps"]
                for medium, repo_node in repositories:
                    if repo_node != None:
                        rep = Repository_from_node(repo_node)
                        rep.medium = medium
                        source.repositories.append(rep)

            if source:
                return {"item": source, "status": Status.OK}
            return {
                "status": Status.NOT_FOUND,
                "statustext": f"source iid={iid} not found",
            }


    def dr_get_sources_for_obj(self, user, material, iid):
        """Read Citations, Sources and Repositories referred from given object.

        :param: user        username, who has access
        :param: material    the material concerned
        :param: iid         Current object node iid

         Returns Citation (w Notes) - Source (w Notes) - Repository data 
                 as list of SourceCitation objects.
        
        TODO: Not processing Citation properties and connected Media
       """

        class SourceCitation:
            """ Carrier for a Source and Repository reference. """
            def __init__(self):
                # Referencing Citation (w Notes), Source (w Notes) and Repository
                self.citation = None
                self.source = None
                self.repository = None
            def __str__(self):
                c = self.citation.iid if self.citation else "?"
                s = self.source.iid if self.source else "?"
                r = self.repository.iid if self.repository else "?"
                return (f"{c} -> {s} -> {r}")


        citations = []
    
        if iid[0] == "M":
            select_obj = CypherMedia.media_prefix
        else:
            raise IsotammiException("Neo4jReadService.dr_get_sources_for_obj: Unknown object type")

        with self.driver.session(default_access_mode="READ") as session:
            try:
                result = run_cypher_batch(session, CypherMedia.get_obj_source_notes, user, material,
                                          cypher_prefix=select_obj, iid=iid)
                # RETURN a, cita, sour, repo,
                #    COLLECT(DISTINCT s_note) AS source_notes,
                #    COLLECT(DISTINCT c_note) AS citation_notes
    
                for record in result:
                    cita_node = record["cita"]
                    sour_node = record["sour"]
                    repo_node = record["repo"]
                    source_notes = record["source_notes"]
                    citation_notes = record["citation_notes"]
 
                    if cita_node:
                        cita = Citation_from_node(cita_node)
                        cita.notes = []
                        for node in citation_notes:
                            cita.notes.append(Note_from_node(node))
                    # else:
                    #     return {"status": Status.NOT_FOUND}

                    sour = None
                    if sour_node:
                        sour = SourceBl_from_node(sour_node)
                        for node in source_notes:
                            sour.notes.append(Note_from_node(node))

                    repo = None
                    if repo_node:
                        repo = Repository_from_node(repo_node)

                    cita_tuple = SourceCitation()
                    cita_tuple.citation = cita
                    cita_tuple.source = sour
                    cita_tuple.repository = repo
                    citations.append(cita_tuple)

            except Exception as e:
                return {
                    "status": Status.ERROR,
                    "statustext": f"Neo4jReadService.dr_get_sources_for_obj: {e.__class__.__name__} {e}",
                }

        return {"status": Status.OK, "citations": citations}


    def dr_get_source_citators(self, sourceid: int):
        """Read Events and Person, Family and Media citating this Source.

        Returns
        - citation      Citation node
        - notes         list of Note nodes for this citation
        - near          node connected derectly to Citation
        - targets       list of the Person or Family nodes
                        (from near or behind near)
        """

        citations = {}  # {uniq_id:citation_object}
        notes = {}  # {uniq_id:[note_object]}
        # near = {}           # {uniq_id:object}
        targets = {}  # {uniq_id:[object]} Person or Family

        with self.driver.session(default_access_mode="READ") as session:
            result = session.run(CypherSource.get_citators_of_source, uniq_id=sourceid)
            for record in result:
                # <Record        # (1) A Person or Family
                #                #     referencing directly Citation
                #    citation=<Node id=342041 labels={'Citation'}
                #        properties={'id': 'C2840', 'page': '11.10.1907 sivu 2',
                #            'iid': 'C-b6b', 'confidence': '2',
                #            'change': 1585409708}>
                #    notes=[<Node id=384644 labels={'Note'}
                #        properties={'id': 'N3556', 'text': '', 'type': 'Citation', 'iid': 'C-db9',
                #            'url': 'https://digi.kansalliskirjasto.fi/sanomalehti/binding/609338?page=2&term=Sommer&term=Maria&term=Sommerin&term=sommer',
                #            'change': 1585409709}>]
                #    near=<Node id=347773 labels={'Person'}
                #            properties={'sortname': 'Johansson#Gustaf#', 'death_high': 1920, 'confidence': '2.0',
                #                'sex': 1, 'change': 1585409699, 'birth_low': 1810, 'birth_high': 1810,
                #                'id': 'I1745', 'iid': 'H-bed',
                #                'death_low': 1852}>
                #    far=[]
                # >
                # <Record        # (2) A Person or Family having an Event, Name, or Media
                #                #     referencing the Citation
                #    citation=<Node id=342042 labels={'Citation'} properties={...}>
                #    notes=[<Node id=381700 labels={'Note'} properties={...}>]
                #    near=<Node id=359150 labels={'Event'}
                #        properties={'datetype': 0, 'change': 1585409703, 'description': '',
                #            'id': 'E5451', 'date2': 1953097, 'type': 'Death', 'date1': 1953097,
                #            'iid': 'E-f0'}>
                #    far=[
                #         [<Node id=347835 labels={'Person'}
                #            properties={'sortname': 'Sommer#Arthur#',...}>,
                #          'Primary']
                #    ]
                # >
                citation_node = record["citation"]
                near_node = record["near"]
                far_nodes = record["far"]
                note_nodes = record["notes"]

                uniq_id = citation_node.id
                citation = Citation_from_node(citation_node)
                citations[uniq_id] = citation

                notelist = []
                for node in note_nodes:
                    notelist.append(Note_from_node(node))
                if notelist:
                    notes[uniq_id] = notelist

                targetlist = []  # Persons or Families referring this source
                for node, role in far_nodes:
                    if not node:
                        continue
                    obj = self._obj_from_node(node, role)
                    if obj:  # Far node is the Person or Family
                        obj.eventtype = near_node["type"]
                        targetlist.append(obj)
                if not targetlist:  # No far node: there is a middle node near
                    obj = self._obj_from_node(near_node)
                    if obj:
                        targetlist.append(obj)
                if targetlist:
                    targets[uniq_id] = targetlist
                else:
                    print(
                        f'dr_get_source_citators: Event {near_node.id} {near_node.get("id")} without Person or Family?'
                    )

        # Result dictionaries using key = Citation uniq_id
        return citations, notes, targets

    def dr_source_search(self, args):
        # material = args.get('material')
        # username = args.get('use_user')
        searchtext = args.get('searchtext')
        limit = args.get('limit', 100)
        #print(args)

        cypher = """
            CALL db.index.fulltext.queryNodes("sourcetitle",$searchtext) 
                YIELD node as source, score
            WITH source,score
            ORDER by score desc

            MATCH (root:Root {state:"Accepted"}) --> (source)
            RETURN DISTINCT source, score
            LIMIT $limit
            """
        with self.driver.session(default_access_mode="READ") as session:
            result = session.run( cypher, 
                                  searchtext=searchtext,
                                  limit=limit)
            rsp = []
            for record in result:
                source = record.get('source')
                score = record.get('score')
                d = dict(
                    source=dict(source),
                    score=score)
                rsp.append(d) 
            return {'items': rsp, 'status': Status.OK}


    # ------ Repositories (Archives) -----

    def dr_get_repo_list_fw(self, args):
        """Read all repositories with notes and number of sources.

        used keyword arguments:
        - user        Username to select data
        - fw          Read repositories starting from this keyword
        - count       How many repositories to read

        Todo: tuloksen sivuttaminen esim. 100 kpl / sivu
        """
        repos = []
        user = args.get("user")
        material = args.get("material")

        with self.driver.session(default_access_mode="READ") as session:
            result = run_cypher_batch(
                session, CypherRepository.get_repositories, user, material
            )

            for record in result:
                # Record root, repository, notes[], mediums[], source_cnt 
                node = record["repository"]
                rep = Repository_from_node(node)
                # Got <id>, Change, id, iid, rname, type
                rep.root = dict_root_node(record["root"])
                for node in record["notes"]:
                    n = Note_from_node(node)
                    rep.notes.append(n)
                rep.mediums = record["mediums"] or []
                rep.source_cnt = record["source_cnt"]
                repos.append(rep)

        return repos

    def dr_get_repository(self, user: str, material: Material, iid: str):
        """Returns the Repository with Sources included."""
        repo = None
        with self.driver.session(default_access_mode="READ") as session:
            result = run_cypher(session, 
                CypherRepository.get_repository_sources_iid, 
                user, material, iid=iid
            )
            for record in result:
                # <Record 
                #    root=<Node element_id='155335' labels=frozenset({'Root'}) 
                #        properties={'material': 'Family Tree', 'state': 'Accepted', 'id': '2021-08-29.003', 'user': 'juha', ...}> 
                #    repo=<Node element_id='160455' labels=frozenset({'Repository'}) 
                #        properties={'rname': 'Haminan seurakunnan arkisto', 'iid': 'R-22s', 
                #        'change': 1585409708, 'id': 'R0260', 'type': 'Archive'}> 
                #    sources=[
                #        [<Node element_id='165962' labels=frozenset({'Source'}) 
                #            properties={'stitle': 'Haminan srk - pää- ja rippikirja 1732-1742 (I Aa:1, ruotsinkieliset)', 
                #            'iid': 'S-amc', 'spubinfo': '', 'sauthor': '', 'change': 1585409706, 'id': 'S1705'}>, 
                #         'Book'], 
                #        [<Node element_id='165487', ...], 
                #    ]>
                # >
                node = record["repo"]
                repo = Repository_from_node(node)
                repo.root = dict_root_node(record["root"])
                source_list = record['sources']
                if source_list:
                    for node, medium, cita_cnt in source_list:
                        if node:
                            s = SourceBl_from_node(node)
                            s.medium = medium
                            s.citation_cnt = cita_cnt
                            repo.sources.append(s)
                            
                notes = record["notes"]
                for note_node in notes:
                    n = Note_from_node(note_node)
                    repo.notes.append(n)

            if repo:
                return {"item": repo, "status": Status.OK}
            return {
                "status": Status.NOT_FOUND,
                "statustext": f"repo iid={iid} not found",
            }


    # ------ Media -----

    def dr_get_media_list(self, user, material, fw_from, limit):
        """Reads Media objects from user batch or common data using context.

        :param: user    Active user or None, if approved data is requested
        :param: fw_from The name from which the list is requested
        :param: limit   How many items per page
        """

        with self.driver.session(default_access_mode="READ") as session:
            result = run_cypher_batch(
                session,
                CypherMedia.get_media_list,
                user,
                material,
                start_name=fw_from,
                limit=limit,
            )

            media = []
            for record in result:
                # <Record
                #    root=<Node element_id='911199' labels=frozenset({'Root'}) 
                #        properties={'metaname': 'uploads/valta/2022-04-16.004/Rääkkylä paikat.isotammi.gpkg.meta',
                #            'file': 'uploads/valta/2022-04-16.004/Rääkkylä paikat.isotammi.gpkg', 'xmlname': 'Rääkkylä paikat.isotammi.gpkg', 
                #            'material': 'Place Data', 'logname': 'uploads/valta/2022-04-16.004/Rääkkylä paikat.isotammi.gpkg.log', 
                #            'mediapath': '/home/kari/Rosenkvist20211231.gpkg.media', 
                #            'description': 'Rääkkylän paikkatiedot-kanta Isotammen "place data" XML-versiona', 'state': 'Accepted', 'id': '2022-04-16.004', 
                #            'user': 'valta', 'db_schema': '2022.1.8', 'timestamp': 1650124333093}> 
                #    o=<Node element_id='1144116' labels=frozenset({'Media'}) 
                #        properties={'iid': 'M-1xy', 'batch_id': '2022-04-16.004', 
                #            'src': 'SSS/ErillisetPitajankartat/PitajankarttaRaakkyla.jpg', 
                #            'mime': 'image/jpeg', 'change': 1639149676, 'name': '', 
                #            'description': 'Erilliset pitäjänkartat Rääkkylä', 'id': 'O0073'}>
                #    count=1
                # >
                m = MediaBl_from_node(record["o"])
                m.root = dict_root_node(record["root"])
                m.conn = record.get("count", 0)
                media.append(m)
            if media:
                return {"media": media, "status": Status.OK}
            else:
                return {"media": media, "status": Status.NOT_FOUND}

    def dr_get_media_single(self, user, material, iid):
        """Read a Media object with Referrers and Notes.

        :param: user        username, who has access
        :param: material    the material concerned
        :parma: iid         Media node iid
        """

        class MediaReferrer:
            """ Carrier for a referee of media object. """

            def __init__(self):
                # Referencing object, label, cropping
                self.obj = None
                self.label = None
                self.crop = None
                # If the referring obj is Event, there is a list of connected objects
                self.next_objs = []

            def __str__(self):
                s = ""
                if self.obj:
                    if self.next_objs:
                        s = " ".join([x.id for x in self.next_objs]) + "-> "
                    s += f" {self.label} {self.obj.id} -{self.crop}-> (Media)"
                return s

        media = None
        event_refs = {}  # The Person or Family nodes behind referencing Event
        with self.driver.session(default_access_mode="READ") as session:
            try:
                result = run_cypher_batch(session, CypherMedia.get_media_by_iid,
                                          user, material, iid=iid)
                # RETURN root, a, PROPERTIES(r) AS prop, referrer, referrer_e,
                #   COLLECT(DISTINCT note) AS notes

                for record in result:
                    media_node = record["a"]
                    crop = record["prop"]
                    ref_node = record["referrer"]
                    event_node = record["referrer_e"]
                    note_nodes = record["notes"]

                    # - Media node
                    # - cropping
                    # - referring Person, Family or Event
                    # - optional Person or Family behind the referring Event

                    if not media:
                        media = MediaBl_from_node(media_node)
                        media.ref = []
                        # Original owner
                        media.root = dict_root_node(record["root"])

                    #   The referring object

                    mref = MediaReferrer()
                    (mref.label,) = ref_node.labels  # Get the 1st label
                    if mref.label == "Person":
                        mref.obj = PersonBl_from_node(ref_node)
                    elif mref.label == "Place":
                        mref.obj = PlaceBl_from_node(ref_node)
                    elif mref.label == "Event":
                        mref.obj = EventBl_from_node(ref_node)
                    mref.obj.label = mref.label
                    media.ref.append(mref)

                    # Has the relation cropping properties?
                    left = crop.get("left")
                    if not left is None:
                        upper = crop.get("upper")
                        right = crop.get("right")
                        lower = crop.get("lower")
                        mref.crop = (left, upper, right, lower)

                    #    The next object behind the Event

                    if event_node:
                        if event_node.id in event_refs:
                            obj2 = event_refs[event_node.id]
                        else:
                            if "Person" in event_node.labels:
                                obj2 = PersonBl_from_node(event_node)
                                obj2.label = "Person"
                            elif "Family" in event_node.labels:
                                obj2 = FamilyBl_from_node(event_node)
                                obj2.label = "Family"
                            else:
                                raise TypeError(
                                    f"MediaReader.get_one: unknown type {list(event_node.labels)}"
                                )
                            event_refs[obj2.uniq_id] = obj2

                        mref.next_objs.append(obj2)

                    notes = []
                    for note_node in note_nodes:
                        print (f" {media_node['id']} -> (Note: {note_node._properties})")
                        obj = Note_from_node(note_node)
                        notes.append(obj)

            except Exception as e:
                return {
                    "status": Status.ERROR,
                    "statustext": f"Neo4jReadService.dr_get_media_single: {e.__class__.__name__} {e}",
                }

        status = Status.OK if media else Status.NOT_FOUND
        return {"status": status, "media": media, "notes":notes}


    # ------ Comment -----


    def dr_get_topic_list(self, user, material, fw_from, limit):
        """Reads Comment objects from user batch or common data using context.

        :param: user    Active user or None, if approved data is requested
        :param: fw_from The timestamp from which the list is requested
        :param: limit   How many items per page
        """
        from pe.neo4j.nodereaders import Root_from_node

        def record_to_topics(result):
            res = []
            for record in result: # <Record
                #    o=<Node id=189486 labels=frozenset({'Person'})
                #        properties={...}>
                #    c=<Node id=189551 labels=frozenset({'Comment'})
                #        properties={'text': 'testi Gideon', 'timestamp': 1631965129453}>
                #    commenter='juha'
                #    count=0
                #    root=<Node id=189427 labels=frozenset({'Root'})
                #        properties={'xmlname': 'A-testi 2021 koko kanta.gpkg',
                #            'material': 'Family Tree', 'state': 'Candidate',
                #            'id': '2021-09-16.001', 'user': 'juha', ...}>
                # >
                node = record["c"]
                c = Comment_from_node(node)
                # c.label = list(node.labels).pop()
                if not c.title:
                    # Show shortened text without line breaks as title
                    text = c.text.replace("\n", " ")
                    if len(text) > 50:
                        n = text[:50].rfind(" ")
                        if n < 2:
                            n = 50
                        c.title = text[:n]
                    else:
                        c.title = c.text
                o_node = record.get("o")
                if o_node:
                    c.obj_label, = o_node.labels
                else:
                    c.obj_label = "Root"
                c.count = record.get("count", 0)
                c.credit = record.get("commenter")
                node = record["root"]
                #Todo: Refactor to Root_from_node()
                c.root = Root_from_node(node)
                if c.obj_label == "Family":
                    c.object = FamilyBl_from_node(o_node)
                elif c.obj_label == "Person":
                    c.object = PersonBl_from_node(o_node)
                elif c.obj_label == "Place":
                    c.object = PlaceBl_from_node(o_node)
                elif c.obj_label == "Source":
                    c.object = SourceBl_from_node(o_node)
                elif c.obj_label == "Media":
                    c.object = MediaBl_from_node(o_node)
                elif c.obj_label == "Root":
                    c.object = c.root
                else:
                    print(
                        f"CommentReader.read_my_comment_list: Discarded referring object '{c.obj_label}'")
                    next
                res.append(c)
            return res
            # --- end record_to_topics()


        with self.driver.session(default_access_mode="READ") as session:
            # Comment topics for batch objects
            result = run_cypher_batch(
                session,
                CypherComment.get_topics,
                user,
                material,
                start_timestamp=fw_from,
                limit=limit,
            )
            topics_objs = record_to_topics(result)

            # Comment topics for batch itself
            result = run_cypher_batch(
                session,
                CypherComment.get_topics_for_root,
                user,
                material,
                start_timestamp=fw_from,
                limit=limit,
            )
            topics_root = record_to_topics(result)
            #print(f"#Neo4jReadService.dr_get_topic_list: objects {len(topics_objs)}, root {len(topics_root)}")

            # Sort concatenated data and truncate by limit
            topics = topics_root + topics_objs
            topics = sorted(topics, key=lambda x: x.timestamp, reverse=True)[:limit]
            if topics:
                return {"topics": topics, "status": Status.OK}
            else:
                return {"topics": [], "status": Status.NOT_FOUND}

    # ------ Start page statistics -----

    #   @functools.lru_cache
    def dr_get_surname_list(self, username: str, material: Material, count: int):
        """ List most common surnames """
        result_list = []
        with self.driver.session(default_access_mode="READ") as session:
            cypher = CypherPerson.get_surname_list
            #             print('#  Neo4jReadService.dr_get_surname_list: with \n{ material:"'
            #                   f'{self.material.m_type}", state:"{self.material.state}", username:"{username}", count:{count}''}')
            #             print(f"#  Neo4jReadService.dr_get_surname_list: cypher \n{cypher}\n")
            result = run_cypher_batch(session, cypher, username, material, count=count)
            for record in result:
                surname = record["surname"]
                count = record["count"]
                result_list.append({"surname": surname, "count": count})
        return result_list

