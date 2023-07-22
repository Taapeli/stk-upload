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
#import shareds

from bl.base import NodeObject, Status
from bl.person_name import Name
from bl.note import Note
from pe.dataservice import DataService

# Sex code values
SEX_UNKNOWN = 0
SEX_MALE = 1
SEX_FEMALE = 2
SEX_NOT_APPLICABLE = 9

from bl.base import PRIVACY_LIMIT

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
       attr[]                dict lisätiedot {attr_type: attr_value}
      }
    """

    def __init__(self):
        """ Creates a new Person instance. """
        NodeObject.__init__(self)
        self.priv = None
        self.sex = SEX_UNKNOWN
        self.confidence = ""
        self.sortname = ""
        self.dates = None  # Daterange: Estimated datetype, date1, date2

        self.birth_low = None
        self.death_low = None
        self.birth_high = None
        self.death_high = None
        self.attr = dict()

    def __str__(self):
        dates = self.dates if self.dates else ""
        return "{} {} {}".format(self.sex_str(), self.id, dates)

    def sex_str(self):
        " Returns person's sex as string"
        return self.convert_sex_to_str(self.sex)

    def sex_symbol(self):
        " Returns person's sex as string"
        symbols = {
            SEX_UNKNOWN: "",
            SEX_MALE: "♂",
            SEX_FEMALE: "♀",
            SEX_NOT_APPLICABLE: "-",
        }
        return symbols.get(self.sex, "?")

    def child_by_sex(self):
        " Returns person's sex as string"
        ch = {
            SEX_UNKNOWN: _("Child"),
            SEX_MALE: _("Son"),
            SEX_FEMALE: _("Daughter"),
            SEX_NOT_APPLICABLE: _("Child"),
        }
        return ch.get(self.sex, "?")

    @staticmethod
    def convert_sex_to_str(sex):
        " Returns sex code as string"

        sexstrings = {
            SEX_UNKNOWN: _("sex not known"),
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


class PersonReader(DataService):
    """
    Data reading class for Person objects with associated data without transaction.

    - Returns a Result object.
    """

    # def get_person_list(self):  # --> bl.person_reader.PersonReaderTx.get_person_search
    #     """List person data including all data needed to Persons page.
    #
    #     In version v2021.1.2 called:
    #         # --> Neo4jDriver.dr_get_person_list(user, fw_from, limit)
    #         #     --> Neo4jReadServiceTx.tx_get_person_list()
    #         #         --> CypherPerson.read_approved_persons_w_events_fw_name
    #         #         --> CypherPerson.read_my_persons_w_events_fw_name
    #         #         --> CypherPerson.get_common_events_by_refname_use
    #         #         --> CypherPerson.get_my_events_by_refname_use
    #         #         --> CypherPerson.get_common_events_by_years
    #         #         --> CypherPerson.get_my_events_by_years
    #         #        #--> Cypher_person.get_events_by_refname
    #         #        #--> Cypher_person.get_events_by_refname
    #     """
    #     print("bl.person.PersonReader.get_person_list: ERROR obsolete")
    #     return {"items": [], "status": Status.ERROR, "statustext":"obsolete get_person_list"}

    def get_surname_list(self, count=40):
        """
        List all surnames so that they can be displayed in a name cloud.
        
        If self.use_user is defined, filter by user.
        """
        ds = self.dataservice
        surnames = ds.dr_get_surname_list(self.use_user,
                                          self.user_context.material,
                                          count)
        # Returns [{'surname': surname, 'count': count},...]

        # if self.use_user:
        #     surnames = self.dataservice.dr_get_surname_list_by_user(
        #         self.use_user, count=count
        #     )
        # else:
        #     surnames = self.dataservice.dr_get_surname_list_common(count=count)
        return surnames

    def get_person_minimal(self, iid, privacy):
        """
        Get all parents of the person with given iid.
        Returns a list for compatibility with get_parents and get_children.
        """
        last_year_allowed = datetime.now().year - PRIVACY_LIMIT
        nodes = self.dataservice.dr_get_family_members_by_id(iid, which="person")
        for n in nodes:
            n["too_new"] = n["death_high"] > last_year_allowed
        if privacy:
            return [n for n in nodes if not n["too_new"]]
        else:
            return nodes

    def get_parents(self, uniq_id, privacy):
        """
        Get all parents of the person with given db uniq_id.
        Returns a list as number of parents in database is not always 0..2.
        """
        last_year_allowed = datetime.now().year - PRIVACY_LIMIT
        nodes = self.dataservice.dr_get_family_members_by_id(uniq_id, which="parents")
        for n in nodes:
            n["too_new"] = n["death_high"] > last_year_allowed
        if privacy:
            return [n for n in nodes if not n["too_new"]]
        else:
            return nodes

    def get_children(self, uniq_id, privacy):
        """
        Get all children of the person with given db uniq_id.
        Returns a list.
        """
        last_year_allowed = datetime.now().year - PRIVACY_LIMIT
        nodes = self.dataservice.dr_get_family_members_by_id(uniq_id, which="children")
        for n in nodes:
            n["too_new"] = n["death_high"] > last_year_allowed
        if privacy:
            return [n for n in nodes if not n["too_new"]]
        else:
            return nodes


class PersonWriter(DataService):
    """
    Person data store for update possibly without transaction.
    """

    def __init__(self, service_name: str, u_context=None, tx=None):
        super().__init__(service_name, u_context, tx=tx)
        self.dataservice.tx = None

    def set_primary_name(self, iid, old_order):
        self.dataservice.dr_set_primary_name(iid, old_order)

    def set_name_orders(self, uid_list):
        self.dataservice.dr_set_name_orders(uid_list)

    def set_name_type(self, uniq_id, nametype):
        self.dataservice.dr_set_name_type(uniq_id, nametype)

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
        for pid, name_node in self.dataservice.ds_get_personnames(uniq_id):
            from pe.neo4j.nodereaders import Name_from_node # import here to avoid import cycle
            name = Name_from_node(name_node)
            name.person_uid = pid
            names.append(name)

        if do_refnames:
            for name in names:
                # Create links and nodes from given person: (:Person) --> (r:Refname)
                res = self.dataservice.ds_build_refnames(name.person_uid, name)
                refname_count += res.get("count", 0)
        if do_sortname:
            for name in names:
                if name.order == 0:
                    # If default name, store sortname key to Person node
                    sortname = name.key_surname()
                    res = self.dataservice.ds_set_person_sortname(
                        name.person_uid, sortname
                    )
                    sortname_count += 1
                    break

        return {
            "refnames": refname_count,
            "sortnames": sortname_count,
            "status": Status.OK,
        }

    def set_people_lifetime_estimates(self, uids=[]):
        """Sets estimated lifetimes to Person.dates for given person.uniq_ids.

        Stores dates as Person properties: datetype, date1, and date2

        :param: uids  list of uniq_ids of Person nodes; empty = all lifetimes

        Called from bp.gramps.xml_dom_handler.DOM_handler.set_estimated_dates
        and models.dataupdater.set_estimated_dates
        """
        res = self.dataservice.ds_set_people_lifetime_estimates(uids)

        #print(f"Estimated lifetime for {res['count']} persons")
        return res

    def update_person_confidences(self, person_ids: list):
        """Sets a quality rating for given list of Person.uniq_ids.

        Person.confidence is calculated as a mean of confidences in
        all Citations used for Person's Events.
        """
        counter = 0
        for uniq_id in person_ids:
            res = self.dataservice.ds_update_person_confidences(uniq_id)
            # returns {confidence, status, statustext}
            stat = res.get("status")
            if stat == Status.UPDATED:
                counter += 1
            elif stat != Status.OK:
                return {"status": stat, "statustext": res.get("statustext")}

        return {"status": Status.OK, "count": counter}


class PersonBl(Person):
    def __init__(self):
        """
        Constructor creates a new PersonBl intance.
        """
        Person.__init__(self)
        self.names = []
        self.events = []  # bl.event.EventBl
        self.notes = []
