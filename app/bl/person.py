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
    Person and Name classes

    Person hierarkiasuunnitelma 10.9.2018/JMä

    class bl.Person(): 
        Person-noden parametrit 
         - uniq_id
         - properties { handle:"_dd2c613026e7528c1a21f78da8a",
                        id:"I0000",
                        priv:None,
                        sex:"2",
                        confidence:"2.0",
                        sortname:"Floor#Hans-Johansdotter#Katarina",
                        datetype:20, date1:1863872, date2:1868992,
                        change:1536324580}

        - __init__()
        - __str__()
        - from_node(cls, node, obj=None) Creates/updates Person object from 
                                        neo4j Node object

Created on 6.10.2020

@author: jm
"""
#blacked 2021-05-01 JMä
from flask_babelex import _
from datetime import datetime
import logging

logger = logging.getLogger("stkserver")
import shareds

from bl.base import NodeObject, Status
from bl.person_name import Name
from pe.dataservice import DataService
from pe.neo4j.cypher.cy_person import CypherPerson

from models.gen.note import Note

# Privacy rule: how many years after death
PRIVACY_LIMIT = 0

# Sex code values
SEX_UNKOWN = 0
SEX_MALE = 1
SEX_FEMALE = 2
SEX_NOT_APPLICABLE = 9


class Person(NodeObject):
    """Person object

    - uniq_id                int database key
    - Node properties: {
       handle                str "_dd2c613026e7528c1a21f78da8a"
       id                    str "I0000"
       priv                  int 1 = merkitty yksityiseksi
       sex                   str "1", "2", "0" sukupuoli
       confidence            float "2.0" tietojen luotettavuus
       sortname              str default name as "surname#suffix#firstname"
       datetype,date1,date2  DateRange dates # estimated life time
       birth_low             int lifetime years estimate limits like 1720
       death_low             int
       birth_high            int
       death_high            int
       change                int 1536324580
      }
    """

    def __init__(self):
        """ Creates a new Person instance. """
        NodeObject.__init__(self)
        self.priv = None
        self.sex = SEX_UNKOWN
        self.confidence = ""
        self.sortname = ""
        self.dates = None  # Daterange: Estimated datetype, date1, date2

        self.birth_low = None
        self.death_low = None
        self.birth_high = None
        self.death_high = None

    def __str__(self):
        dates = self.dates if self.dates else ""
        return "{} {} {}".format(self.sex_str(), self.id, dates)

    def sex_str(self):
        " Returns person's sex as string"
        return self.convert_sex_to_str(self.sex)

    def sex_symbol(self):
        " Returns person's sex as string"
        symbols = {
            SEX_UNKOWN: "",
            SEX_MALE: "♂",
            SEX_FEMALE: "♀",
            SEX_NOT_APPLICABLE: "-",
        }
        return symbols.get(self.sex, "?")

    def child_by_sex(self):
        " Returns person's sex as string"
        ch = {
            SEX_UNKOWN: _("Child"),
            SEX_MALE: _("Son"),
            SEX_FEMALE: _("Daughter"),
            SEX_NOT_APPLICABLE: _("Child"),
        }
        return ch.get(self.sex, "?")

    @staticmethod
    def convert_sex_to_str(sex):
        " Returns sex code as string"

        sexstrings = {
            SEX_UNKOWN: _("sex not known"),
            SEX_MALE: _("male"),
            SEX_FEMALE: _("female"),
            SEX_NOT_APPLICABLE: _("sex not applicable"),
        }
        return sexstrings.get(sex, "?")

    @staticmethod
    def sex_from_str(s):
        # Converts gender strings to ISO/IEC 5218 codes
        ss = s[:1].upper()
        if ss == "M" or ss == str(SEX_MALE):
            return SEX_MALE
        if ss == "F" or ss == "N" or ss == str(SEX_FEMALE):
            return SEX_FEMALE
        return 0

    @classmethod
    def from_node(cls, node, obj=None):
        """
        Transforms a db node to an object of type Person.

        Youc can create a Person or Person_node instance. (cls is the class
        where we are, either Person or PersonBl)

        <Node id=80307 labels={'Person'}
            properties={'id': 'I0119', 'confidence': '2.5', 'sex': '2', 'change': 1507492602,
            'handle': '_da692a09bac110d27fa326f0a7', 'priv': 1}>
        """
        if not obj:
            obj = cls()
        obj.uuid = node.get("uuid")
        obj.uniq_id = node.id
        obj.id = node["id"]
        obj.sex = node.get("sex", "UNKNOWN")
        obj.change = node["change"]
        obj.confidence = node.get("confidence", "")
        obj.sortname = node["sortname"]
        obj.priv = node["priv"]
        obj.birth_low = node["birth_low"]
        obj.birth_high = node["birth_high"]
        obj.death_low = node["death_low"]
        obj.death_high = node["death_high"]
        last_year_allowed = datetime.now().year - PRIVACY_LIMIT
        #         if obj.death_high < 9999:
        #             print('ok? uniq_id=',obj.uniq_id,obj.death_high)
        obj.too_new = obj.death_high > last_year_allowed
        return obj


class PersonReader(DataService):
    """
    Data reading class for Person objects with associated data without transaction.

    - Returns a Result object.
    """

    def get_person_list(self):
        """List person data including all data needed to Person page.

        Calls Neo4jDriver.dr_get_person_list(user, fw_from, limit)
        """
        context = self.user_context
        res_dict = {}
        args = {
            "use_user": self.use_user,
            "fw": context.first,  # From here forward
            "limit": context.count,
        }
        res = shareds.dservice.dr_get_person_list(args)
        # {'items': persons, 'status': Status.OK}
        if Status.has_failed(res):
            return {
                "items": None,
                "status": res["status"],
                "statustext": _("No persons found"),
            }

        # Update the page scope according to items really found
        persons = res["items"]
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
        res_dict["status"] = Status.OK

        res_dict["num_hidden"] = num_hidden
        res_dict["items"] = persons2
        return res_dict

    def get_surname_list(self, count=40):
        """
        List all surnames so that they can be displayed in a name cloud.
        """
        if self.use_user:
            surnames = shareds.dservice.dr_get_surname_list_by_user(
                self.use_user, count=count
            )
        else:
            surnames = shareds.dservice.dr_get_surname_list_common(count=count)
        # [{'surname': surname, 'count': count},...]
        return surnames

    def get_person_minimal(self, uuid):
        """
        Get all parents of the person with given uuid.
        Returns a list for compatibility with get_parents and get_children.
        """
        return self.dataservice.dr_get_family_members_by_id(uuid, which="person")

    def get_parents(self, uniq_id):
        """
        Get all parents of the person with given db uniq_id.
        Returns a list as number of parents in database is not always 0..2.
        """
        return self.dataservice.dr_get_family_members_by_id(uniq_id, which="parents")

    def get_children(self, uniq_id):
        """
        Get all children of the person with given db uniq_id.
        Returns a list.
        """
        return self.dataservice.dr_get_family_members_by_id(uniq_id, which="children")


class PersonWriter(DataService):
    """
    Person datastore for update without transaction.
    """

    def __init__(self, service_name: str, u_context=None, tx=None):
        super().__init__(service_name, u_context, tx=tx)
        shareds.dservice.tx = None

    def set_primary_name(self, uuid, old_order):
        shareds.dservice.dr_set_primary_name(uuid, old_order)

    def set_name_orders(self, uid_list):
        shareds.dservice.dr_set_name_orders(uid_list)

    def set_name_type(self, uniq_id, nametype):
        shareds.dservice.dr_set_name_type(uniq_id, nametype)

    def set_person_name_properties(self, uniq_id=None, ops=["refname", "sortname"]):
        """Set Refnames to all Persons or one Person with given uniq_id;
        also sets Person.sortname using the default name

        Called from bp.gramps.xml_dom_handler.DOM_handler.set_family_calculated_attributes,
                    bp.admin.routes.set_all_person_refnames
        """
        sortname_count = 0
        refname_count = 0
        do_refnames = "refname" in ops
        do_sortname = "sortname" in ops
        names = []

        # Get each Name object (with person_uid)
        for pid, name_node in shareds.dservice.ds_get_personnames(uniq_id):
            name = Name.from_node(name_node)
            name.person_uid = pid
            names.append(name)

        if do_refnames:
            for name in names:
                # Create links and nodes from given person: (:Person) --> (r:Refname)
                res = shareds.dservice.ds_build_refnames(name.person_uid, name)
                if Status.has_failed(res):
                    return res
                refname_count += res.get("count", 0)
        if do_sortname:
            for name in names:
                if name.order == 0:
                    # If default name, store sortname key to Person node
                    sortname = name.key_surname()
                    res = shareds.dservice.ds_set_person_sortname(
                        name.person_uid, sortname
                    )
                    if Status.has_failed(res):
                        return res
                    sortname_count += 1
                    break

        return {
            "refnames": refname_count,
            "sortnames": sortname_count,
            "status": Status.OK,
        }

    def set_estimated_lifetimes(self, uids=[]):
        """Sets estimated lifetimes to Person.dates for given person.uniq_ids.

        Stores dates as Person properties: datetype, date1, and date2

        :param: uids  list of uniq_ids of Person nodes; empty = all lifetimes

        Called from bp.gramps.xml_dom_handler.DOM_handler.set_estimated_dates
        and models.dataupdater.set_estimated_dates
        """
        res = shareds.dservice.ds_set_people_lifetime_estimates(uids)

        print(f"Estimated lifetime for {res['count']} persons")
        return res


class PersonBl(Person):
    def __init__(self):
        """
        Constructor creates a new PersonBl intance.
        """
        Person.__init__(self)
        self.user = None  # Researcher batch owner, if any
        self.names = []  # models.gen.person_name.Name

        self.events = []  # bl.event.EventBl
        self.notes = []  #

    def save(self, tx, **kwargs):  # batch_id):
        """Saves the Person object and possibly the Names, Events ja Citations.

        On return, the self.uniq_id is set

        @todo: Remove those referenced person names, which are not among
               new names (:Person) --> (:Name)
        """

        if "batch_id" in kwargs:
            batch_id = kwargs["batch_id"]
        else:
            raise RuntimeError(f"Person_gramps.save needs batch_id for {self.id}")
        self.uuid = self.newUuid()
        # Save the Person node under UserProfile; all attributes are replaced
        p_attr = {}
        try:
            p_attr = {
                "uuid": self.uuid,
                "handle": self.handle,
                "change": self.change,
                "id": self.id,
                "priv": self.priv,
                "sex": self.sex,
                "confidence": self.confidence,
                "sortname": self.sortname,
            }
            if self.dates:
                p_attr.update(self.dates.for_db())

            result = tx.run(
                CypherPerson.create_to_batch, batch_id=batch_id, p_attr=p_attr
            )  # , date=today)
            ids = []
            for record in result:
                self.uniq_id = record[0]
                ids.append(self.uniq_id)
                if len(ids) > 1:
                    print(
                        "iError updated multiple Persons {} - {}, attr={}".format(
                            self.id, ids, p_attr
                        )
                    )
                # print("Person {} ".format(self.uniq_id))
            if self.uniq_id == None:
                print("iWarning got no uniq_id for Person {}".format(p_attr))

        except Exception as err:
            logger.error(f"Person_gramps.save: {err} in Person {self.id} {p_attr}")
            # print("iError: Person_gramps.save: {0} attr={1}".format(err, p_attr), file=stderr)
            raise

        # Save Name nodes under the Person node
        for name in self.names:
            name.save(tx, parent_id=self.uniq_id)

        # Save web urls as Note nodes connected under the Person
        if self.notes:
            Note.save_note_list(tx, self)

        """ Connect to each Event loaded from Gramps """
        try:
            # for i in range(len(self.eventref_hlink)):
            for event_handle, role in self.event_handle_roles:
                tx.run(
                    CypherPerson.link_event,
                    p_handle=self.handle,
                    e_handle=event_handle,
                    role=role,
                )
        except Exception as err:
            logger.error(
                f"Person_gramps.save: {err} in linking Event {self.handle} -> {self.handle_role}"
            )
            # print("iError: Person_gramps.save events: {0} {1}".format(err, self.id), file=stderr)

        # Make relations to the Media nodes and it's Note and Citation references
        if self.media_refs:
            shareds.dservice.ds_create_link_medias_w_handles(
                self.uniq_id, self.media_refs
            )

        # The relations to the Family node will be created in Family.save(),
        # because the Family object is not yet created

        # Make relations to the Note nodes
        try:
            for handle in self.note_handles:
                tx.run(CypherPerson.link_note, p_handle=self.handle, n_handle=handle)
        except Exception as err:
            logger.error(
                f"Person_gramps.save: {err} in linking Notes {self.handle} -> {handle}"
            )

        # Make relations to the Citation nodes
        try:
            for handle in self.citation_handles:
                tx.run(
                    CypherPerson.link_citation, p_handle=self.handle, c_handle=handle
                )
        except Exception as err:
            logger.error(
                f"Person_gramps.save: {err} in linking Citations {self.handle} -> {handle}"
            )
        return

    @staticmethod
    def update_person_confidences(person_ids: list):
        """Sets a quality rate for given list of Person.uniq_ids.

        Person.confidence is calculated as a mean of confidences in
        all Citations used for Person's Events.
        """
        counter = 0
        for uniq_id in person_ids:
            res = shareds.dservice.ds_update_person_confidences(uniq_id)
            # returns {confidence, status, statustext}
            stat = res.get("status")
            if stat == Status.UPDATED:
                counter += 1
            elif stat != Status.OK:
                # Update failed
                return {"status": stat, "statustext": res.get("statustext")}

        return {"status": Status.OK, "count": counter}

    #     @staticmethod --> bl.person.PersonWriter.set_person_name_properties
    #     def set_person_name_properties(uniq_id=None, ops=['refname', 'sortname']):
    #     @staticmethod --> pe.neo4j.updateservice.Neo4jUpdateService ??
    #     def get_confidence (uniq_id=None):
    #     def set_confidence (self, tx):
    #     @staticmethod # --> bl.person.PersonWriter.set_estimated_lifetimes
    #     def estimate_lifetimes(uids=[]):

    def remove_privacy_limit_from_families(self):
        """Clear privacy limitations from self.person's families.

        Origin from models.person_reader
        """
        for family in self.families_as_child:
            family.remove_privacy_limits()
        for family in self.families_as_parent:
            family.remove_privacy_limits()
