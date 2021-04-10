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
Created on 2.5.2017 from Ged-prepare/Bus/classes/genealogy.py

Components moved 15.5.2020 from 
    - models.gen.family.Family -> Family
    - models.gen.family_combo.Family_combo -> FamilyBl
    - models.gen.family_combo.Family_combo -> FamilyBl, FamilyReader

@author: jm 
"""
import shareds
from ui.jinja_filters import translate
import logging

logger = logging.getLogger("stkserver")
from flask_babelex import _

from .base import NodeObject, Status
from .person import PersonBl
from .person_name import Name

# from pe.db_reader import DbReader
from pe.dataservice import DataService
from models.gen.cypher import Cypher_family  # TODO fix
from pe.neo4j.cypher.cy_family import CypherFamily

from bl.dates import DateRange


class Family(NodeObject):
    """Family Node object.

    Properties:
            change
            id              esim. "F0001"
            uniq_id         int database key
            uuid            str UUID key
            rel_type        str suhteen tyyppi
            priv            str private if exists
            father_sortname str search key
            mother_sortname str search key
    """

    def __init__(self, uniq_id=None):
        """Creates a new Family instance representing a database Family node."""
        NodeObject.__init__(self, uniq_id)
        self.priv = None
        self.rel_type = ""
        self.dates = None  # TODO DateRange marriage .. divorce
        # Sorting name of family's father and mother
        self.father_sortname = ""
        self.mother_sortname = ""

    def __str__(self):
        if self.rel_type:
            rel = self.rel_type.lower()
        else:
            rel = _("undefined relation")
        return "{} {}".format(self.id, rel, self.dates)

    @classmethod
    def from_node(cls, node):
        """
        Transforms a db node to an object of type Family.

        You can create a Family or FamilyBl instance. (cls is the class
        where we are, either Family or FamilyBl)

        <Node id=99991 labels={'Family'}
            properties={'rel_type': 'Married', 'handle': '_da692e4ca604cf37ac7973d7778',
            'id': 'F0031', 'change': 1507492602}>
        """
        n = cls()
        n.uniq_id = node.id
        n.id = node.get("id", "")
        n.uuid = node["uuid"]
        n.handle = node["handle"]
        n.change = node["change"]
        n.rel_type = node.get("rel_type", "")
        n.father_sortname = node.get("father_sortname", "")
        n.mother_sortname = node.get("mother_sortname", "")
        if "datetype" in node:
            n.dates = DateRange(node["datetype"], node["date1"], node["date2"])
        else:
            n.dates = DateRange()
        return n


class FamilyBl(Family):
    """Family business logic object carries the family and connected data.

            Properties from Family:
                    change
                    id              esim. "F0001"
                    uniq_id         int database key
                    uuid            str UUID key
                    rel_type        str "marriage" etc.
                    father_sortname str search key
                    mother_sortname str search key
    #             #TODO: Obsolete properties?
    #                 event_handle_roles      str tapahtuman osoite
    #                 eventref_role       str tapahtuman rooli
    #                 child_handles      str lapsen osoite
    #                 note_handles       str lisätiedon osoite
    #                 citation_handles   str lisätiedon osoite
    """

    def __init__(self, uniq_id=None):
        """Creates a Family instance for carrying whole family information."""
        Family.__init__(self, uniq_id)

        self.father = None
        self.mother = None
        self.children = []  # Child object
        self.events = []  # Event objects
        self.notes = []
        self.sources = []
        self.marriage_dates = DateRange()
        self.note_ref = []  # For a page, where same note may be referenced
        # from multiple events and other objects

    def save(self, tx, **kwargs):
        """Saves the family node to db with its relations.

        Connects the family to parent, child, citation and note nodes.
        """
        if "batch_id" in kwargs:
            batch_id = kwargs["batch_id"]
        else:
            return {
                "status": Status.ERROR,
                "statustext": f"bl.family.FamilyBl.save needs batch_id for {self.id}",
            }
            # raise RuntimeError(f"bl.family.FamilyBl.save needs batch_id for {self.id}")

        self.uuid = self.newUuid()
        f_attr = {}
        try:
            f_attr = {
                "uuid": self.uuid,
                "handle": self.handle,
                "change": self.change,
                "id": self.id,
                "rel_type": self.rel_type,
            }
            result = tx.run(
                CypherFamily.create_to_batch, batch_id=batch_id, f_attr=f_attr
            )
            ids = []
            for record in result:
                self.uniq_id = record[0]
                ids.append(self.uniq_id)
                if len(ids) > 1:
                    logger.warning(
                        f"bl.family.FamilyBl.save updated multiple Families {self.id} - {ids}, attr={f_attr}"
                    )
        except Exception as err:
            msg = f"bl.family.FamilyBl.save: {err} in #{self.uniq_id} - {f_attr}"
            logger.error(msg)
            return {"status": Status.ERROR, "statustext": msg}

        # Make father and mother relations to Person nodes
        try:
            if hasattr(self, "father") and self.father:
                tx.run(
                    CypherFamily.link_parent,
                    role="father",
                    f_handle=self.handle,
                    p_handle=self.father,
                )

            if hasattr(self, "mother") and self.mother:
                tx.run(
                    CypherFamily.link_parent,
                    role="mother",
                    f_handle=self.handle,
                    p_handle=self.mother,
                )
        except Exception as e:
            msg = (
                f"bl.family.FamilyBl.save: family={self.id}: {e.__class__.__name__} {e}"
            )
            print(msg)
            return {"status": Status.ERROR, "statustext": msg}

        # Make relations to Event nodes
        try:
            for handle_role in self.event_handle_roles:
                # a tuple (event_handle, role)
                tx.run(
                    CypherFamily.link_event,
                    f_handle=self.handle,
                    e_handle=handle_role[0],
                    role=handle_role[1],
                )
        except Exception as e:
            msg = f"bl.family.FamilyBl.save events: family={self.id}: {e.__class__.__name__} {e}"
            print(msg)
            return {"status": Status.ERROR, "statustext": msg}

        # Make child relations to Person nodes
        try:
            for handle in self.child_handles:
                tx.run(CypherFamily.link_child, f_handle=self.handle, p_handle=handle)
        except Exception as e:
            msg = f"bl.family.FamilyBl.save children: family={self.id}: {e.__class__.__name__} {e}"
            print(msg)
            return {"status": Status.ERROR, "statustext": msg}

        # Make relation(s) to the Note node
        try:
            # print(f"Family_gramps.save: linking Notes {self.handle} -> {self.note_handles}")
            for handle in self.note_handles:
                tx.run(CypherFamily.link_note, f_handle=self.handle, n_handle=handle)
        except Exception as e:
            msg = f"bl.family.FamilyBl.save notes: family={self.id}: {e.__class__.__name__} {e}"
            print(msg)
            return {"status": Status.ERROR, "statustext": msg}

        # Make relation(s) to the Citation node
        try:
            # print(f"Family_gramps.save: linking Citations {self.handle} -> {self.citationref_hlink}")
            for handle in self.citation_handles:
                tx.run(
                    CypherFamily.link_citation, f_handle=self.handle, c_handle=handle
                )
        except Exception as e:
            msg = f"bl.family.FamilyBl.save citations: family={self.id}: {e.__class__.__name__} {e}"
            print(msg)
            return {"status": Status.ERROR, "statustext": msg}

        return

    @staticmethod
    def set_calculated_attributes(uniq_id):
        """Get Family event dates and sortnames."""
        return shareds.dservice._set_family_calculated_attributes(uniq_id)
        # return tx.run(CypherFamily.get_dates_parents,id=uniq_id)

    def remove_privacy_limits(self):
        if self.father:
            self.father.too_new = False
        if self.mother:
            self.mother.too_new = False
        for c in self.children:
            c.too_new = False


class FamilyReader(DataService):
    """
    Data reading class for Family objects with associated data.

    - Returns a Result object which includes the items and eventuel error object.
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

    def get_families(self, opt="father"):
        """Find families from the database

        from /scene/families, tools: /listall/families
        """

        families = []
        fw = self.user_context.first  # next name
        user = self.user_context.batch_user()
        limit = self.user_context.count
        order = self.user_context.order
        ustr = "user " + user if user else "no user"
        print(
            f"FamilyReader.get_families: Get max {limit} families "
            f"for {ustr} starting  {order} {fw!r}"
        )

        # Select True = filter by this user False = filter approved data
        show_by_owner = self.user_context.use_owner_filter()
        # show_approved = self.user_context.use_common()

        with shareds.driver.session() as session:
            try:
                if show_by_owner:
                    # (u:UserProfile {username})
                    #    -[:HAS_LOADED]-> (b:Batch)
                    #    -[:OWNS]-> (f:Family {father_sortname})
                    if order == "man":
                        print("FamilyReader.get_families: my own order by man")
                        result = session.run(
                            Cypher_family.read_my_families_f,
                            user=user,
                            fw=fw,
                            limit=limit,
                        )
                    elif order == "wife":
                        print("FamilyReader.get_families: my own order by wife")
                        result = session.run(
                            Cypher_family.read_my_families_m,
                            user=user,
                            fwm=fw,
                            limit=limit,
                        )
                else:  # approved from any researcher
                    # (:Audit) -[:PASSED]-> (f:Family {father_sortname})
                    if order == "man":
                        # 3 == #1 simulates common by reading all
                        print("FamilyReader.get_families: approved order by man")
                        result = session.run(
                            Cypher_family.read_families_common_f,  # user=user,
                            fw=fw,
                            limit=limit,
                        )
                    elif order == "wife":
                        # 1 get all with owner name for all
                        print("FamilyReader.get_families: approved order by wife")
                        result = session.run(
                            Cypher_family.read_families_common_m, fwm=fw, limit=limit
                        )

            except Exception as e:
                print(f"FamilyReader.get_families: {e.__class__.__name__} {e}")
                raise

            for record in result:
                # record.keys() = ['f', 'marriage_place', 'parent', 'child', 'no_of_children']
                if record["f"]:
                    # <Node id=55577 labels={'Family'}
                    #    properties={'rel_type': 'Married', 'handle': '_d78e9a206e0772ede0d',
                    #    'id': 'F0000', 'change': 1507492602}>
                    f_node = record["f"]
                    family = FamilyBl.from_node(f_node)
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
                                pp = PersonBl.from_node(parent_node)
                                if role == "father":
                                    family.father = pp
                                elif role == "mother":
                                    family.mother = pp

                            pname = Name.from_node(name_node)
                            pp.names = [pname]

                    for ch in record["child"]:
                        # <Node id=60320 labels={'Person'}
                        #    properties={'sortname': '#Björnsson#Simon', 'datetype': 19,
                        #    'confidence': '', 'sex': 0, 'change': 1507492602,
                        #    'handle': '_d78e9a2696000bfd2e0', 'id': 'I0001',
                        #    'date2': 1609920, 'date1': 1609920}>
                        #                         child = Person_as_member()
                        child = PersonBl.from_node(ch)
                        family.children.append(child)
                    family.children.sort(key=lambda x: x.birth_low)

                    if record["no_of_children"]:
                        family.no_of_children = record["no_of_children"]
                    family.num_hidden_children = 0
                    if not self.user_context.use_common():
                        if family.father:
                            family.father.too_new = False
                        if family.mother:
                            family.mother.too_new = False
                    families.append(family)

        # Update the page scope according to items really found
        if families:
            up_scope = self.user_context.update_session_scope
            if order == "man":
                up_scope(
                    "person_scope",
                    families[0].father_sortname,
                    families[-1].father_sortname,
                    limit,
                    len(families),
                )
            else:
                up_scope(
                    "person_scope",
                    families[0].mother_sortname,
                    families[-1].mother_sortname,
                    limit,
                    len(families),
                )
            self.user_context.order = order

        if self.user_context.use_common():
            families = self.hide_privacy_protected_families(families)
        return families

    def get_family_data(self, uuid: str, wanted=[]):
        """Read Family information including Events, Children, Notes and Sources.

        Returns a dict {item:Family, status=0, statustext:None}

        where status code is one of Status.OK / Status.NOT_FOUND / Status.ERROR

        Ther wanted parameter is a string of short keywords separated by ':'.

        Operations path
        1) read
            (f:Family) --> (e:Event)
            (f:Family) -[:PARENT]-> (pp:Person) -> (np:Name)
            (f:Family) -[:CHILD]->  (pc:Person) -> (nc:Name)
            (f:Family) --> (fn:Note)
            (e:Event) --> (en:Note)
            (f:Family) --> (fac:Citation) --> (fas:Source) --> (far:Repository)
            (e:Event) --> (evc:Citation) --> (evs:Source) --> (evr:Repository)

        2) read
            (pp:Person) --> (ppe:Event) --> (:Place)
            (pc:Person) --> (pce:Event) --> (:Place)

        3) build
            FamilyBl.mother, .names, event_birth, event_death
            FamilyBl.father, .names, event_birth, event_death
            FamilyBl.events
            FamilyBl.notes
            FamilyBl.sources / citation -> source -> repocitory ?
            FamilyBl.children, .names, event_birth, event_death
        """

        # Select data by wanted parameter like 'pare:name:even:plac':

        # all - all data
        select_all = "all" in wanted
        if not wanted:
            select_all = True
        select_parents = select_all or "pare" in wanted  # Parents (mother, father)
        select_children = select_all or "chil" in wanted  # Children
        select_names = (
            select_all or "name" in wanted
        )  # Person names (for parents, children)
        select_events = select_all or "even" in wanted  # Events
        select_places = select_all or "plac" in wanted  # Places (for events)
        select_notes = select_all or "note" in wanted  # Notes
        select_sources = (
            select_all or "sour" in wanted
        )  # Sources (Citations, Sources, Repositories)
        # select_media  = select_all or 'medi' in wanted     # Media
        """
            1. Get Family node by user/common
               res is dict {item, status, statustext}
        """
        ret_results = shareds.dservice.dr_get_family_by_uuid(self.use_user, uuid)
        # ret_results {'item': <bl.family.FamilyBl>, 'status': Status}
        if Status.has_failed(ret_results):
            return ret_results

        family = ret_results.get("item")
        # The Nodes for search of Sources and Notes (Family and Events)
        src_list = [family.uniq_id]
        """
            2. Get Parent nodes [optionally] with default Name
               res is dict {items, status, statustext}
        """
        if select_parents:
            res = shareds.dservice.dr_get_family_parents(
                family.uniq_id, with_name=select_names
            )
            for p in res.get("items"):
                # For User's own data, no hiding for too new persons
                if self.use_user:
                    p.too_new = False
                if p.role == "father":
                    family.father = p
                elif p.role == "mother":
                    family.mother = p
        """
            3. Get Child nodes [optionally] with Birth and Death nodes
               res is dict {items, status, statustext}
        """
        if select_children:
            res = shareds.dservice.dr_get_family_children(
                family.uniq_id, with_events=select_events, with_names=select_names
            )
            # res {'items': [<bl.person.PersonBl>], 'status': Status}
            family.num_hidden_children = 0
            for p in res.get("items"):
                # For User's own data, no hiding for too new persons
                if self.use_user:
                    p.too_new = False
                if p.too_new:
                    family.num_hidden_children += 1
                family.children.append(p)
        """
            4. Get family Events node with Places
               res is dict {items, status, statustext}
        """
        if select_events:
            res = shareds.dservice.dr_get_family_events(
                family.uniq_id, with_places=select_places
            )
            for e in res.get("items"):
                family.events.append(e)
                src_list.append(e.uniq_id)
        """
            5 Get family and event Sources Citations and Repositories
              optionally with Notes
        """
        if select_sources:
            res = shareds.dservice.dr_get_family_sources(src_list)
            for s in res.get("items"):
                family.sources.append(s)
        """
            6 Get Notes for family and events
        """
        if select_notes:
            res = shareds.dservice.dr_get_family_notes(src_list)
            for s in res.get("items"):
                family.notes.append(s)

        return ret_results

    def get_person_families(self, uuid: str):
        """Get all families for given person in marriage date order."""
        res = shareds.dservice.dr_get_person_families_uuid(uuid)
        items = res.get("items")
        if items:
            items.sort(key=lambda x: x.dates)
            # Add translated text fields
            for family in items:
                family.rel_type_lang = translate(family.rel_type, "marr").lower()
                # As_child / As_parent
                family.role_lang = translate("As_" + family.role, "role")
                for parent in family.parents:
                    parent.role_lang = translate(parent.role, "role")
                for child in family.children:
                    child.role_lang = translate(child.sex, "child")

            return {"items": items, "status": Status.OK}
        else:
            return {
                "items": [],
                "status": Status.NOT_FOUND,
                "statustext": _("This person has no families"),
            }

    # The followind may be obsolete

    def get_children_by_id(self):
        raise ("Obsolete bl.family.FamilyReader.get_children_by_id")

    def get_family_events(self):
        """ Luetaan perheen tapahtumien tiedot """

        pid = int(self.uniq_id)
        query = """
MATCH (family:Family)-[r:EVENT]->(event:Event)
  WHERE ID(family)=$pid
RETURN r.role AS eventref_role, event.handle AS event_handles"""
        return shareds.driver.session().run(query, {"pid": pid})

    @staticmethod
    def find_family_for_event(event_uniq_id):
        """Returns Family instance which has given Event.

        NOT IN USE. For models.obsolete_datareader.get_source_with_events
        """
        query = """
MATCH (family:Family)-[r:EVENT]->(event)
  WHERE ID(event)=$pid
RETURN family"""
        result = shareds.driver.session().run(query, pid=event_uniq_id)
        for record in result:
            f = FamilyBl.from_node(record[0])
            return f
        raise LookupError(f"Family {event_uniq_id} not found")

    #     @staticmethod
    #     def get_dates_parents(tx, uniq_id): #see models.gen.family_combo.Family_combo
    #         return tx.run(Cypher_family.get_dates_parents,id=uniq_id)

    #     @staticmethod
    #     def set_dates_sortnames(tx, uniq_id, dates, father_sortname, mother_sortname): #see models.gen.family_combo.Family_combo
    #         ''' Update Family dates and parents' sortnames.

    def hide_privacy_protected_families(self, families):
        ret_families = []
        for fam in families:
            if (not fam.father or fam.father.too_new) and (
                not fam.mother or fam.mother.too_new
            ):
                continue  # do not include this family
            ret_families.append(fam)
            children2 = [c for c in fam.children if not c.too_new]
            fam.num_hidden_children = len(fam.children) - len(children2)
            fam.children = children2
        return ret_families


#     @staticmethod
#     def get_families(o_context, opt='father', limit=100): #see models.gen.family_combo.Family_combo
#         """ Find families from the database """

#     @staticmethod
#     def get_all_families(): #see models.gen.family_combo.Family_combo
#         """ Find all families from the database - not in use!

#     @staticmethod
#     def get_own_families(user=None): #see models.gen.family_combo.Family_combo
#         """ Find all families from the database - not in use!

#     @staticmethod
#     def get_marriage_parent_names(event_uniq_id): #see models.gen.family_combo.Family_combo

#     def get_parent_by_id(self, role='father'): #see models.gen.family_combo.Family_combo
#         """ Luetaan perheen isän (tai äidin) tiedot """
