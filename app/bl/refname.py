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
Created on 2.5.2017 & 14.1.2018 / JMä

@author: jm

I.  To a Person node there can be different references from Refnames:
    1) Any First name generates link (example 'Per')
        (p:Person) <-[l:REFNAME {reftype:'firstname'}]- (r:Refname {name:'Per'})

    2) Any Surname generates link 
        (p:Person) <-[l:REFNAME {reftype:'surname'}]- (r:Refname)

    3) Any Patronyme name generates link (example 'Persson')
        (p:Person) <-[l:REFNAME {reftype:'patronyme'}]- (r:Refname {name:'Persson'})

II. Between Refnames there can be different references:
    4) A link from a name variation to basename
        (r:Refname {name:'Per'}) -[b:BASENAME]-> (s:Refname {name:'Pekka'})
        (r:Refname {name:'Persson'}) -[b:BASENAME]-> (s:Refname {name:'Pekanpoika'})

    5) A link from a patronyme to the first name from witch it is derived from
        (r:Refname {name:'Persson'}) -[b:PARENTNAME]-> (s:Refname {name:'Per'})

The I links are created, when new Person nodes are inserted.
The II links are created, when reference names are added from a cvs file.
"""
# blacked 2021-05-01 JMä
from sys import stderr
import time
import logging

logger = logging.getLogger("stkserver")

import shareds
from bl.base import NodeObject  # , Status
from pe.neo4j.cypher.cy_refname import CypherRefname
from .person import Person, SEX_UNKOWN

# Global allowed reference types in Refname.reftype field or use attribute in db
REFTYPES = ["basename", "firstname", "surname", "patronyme", "father", "mother"]


class Refname(NodeObject):
    """
    ( Refname {uniq_id, nimi} ) -[reftype]-> (Refname)
               reftype = (etunimi, sukunimi, patronyymi)
    Properties:                                             input source
        uniq_id     ID() ...                                    (created in save())
        name    1st letter capitalized                      (Nimi)
        refname * the std name referenced, if exists        (RefNimi)
        reftype * which kind of reference refname points to ('firstname')
        sex  '2', '1' or '0'                                (Sukupuoli)
        source  points to Source                            (Lähde)

    * Note: refnamea ja reftypeä ei talleteta tekstinä, vaan kannassa tehdään
            viittaus tyyppiä reftype ko Refname-olioon
    """

    # TODO: source pitäisi olla viite lähdetietoon, nyt sinne on laitettu lähteen nimi

    label = "Refname"

    #   Samasta nimestä "Persson" voisi olla linkki 'surname' nimeen "Pekanpoika"
    #   ja 'patronyme' nimeen "Pekka".
    #   __REFNAMETYPES = ['undef', 'fname', 'lname', 'patro', 'place', 'occu']

    # TODO: Refname.pos tilalle .reftype; .rid tilalle ID(a)
    # MATCH (f:Refname)-[l]->(t:Refname) RETURN f AS basename, TYPE(l) AS base_ref, t AS refname
    # ╒═════════════════════════════╤═══════════╤═════════════════════════════╕
    # │"basename"                   │"base_ref" │"refname"                    │
    # ╞═════════════════════════════╪═══════════╪═════════════════════════════╡
    # │{"name":"Gustav","sex":"1"   │"BASENAME" │{"name":"Kustaa","sex":"1"   │
    # │,"rid":3,"lang":"sv","pos":"f│           │,"rid":4,"lang":"fi","pos":"f│
    # │irstname"}                   │           │irstname"}                   │
    # ├─────────────────────────────┼───────────┼─────────────────────────────┤
    # │{"name":"Johansson","rid":5,"│"PARENTNAME│{"name":"Juha","sex":"1","   │
    # │lang":"sv","pos":"patronym"} │"          │lang":"fi","rid":6,"pos":"fir│
    # │                             │           │stname"}                     │
    # ├─────────────────────────────┼───────────┼─────────────────────────────┤
    # │{"name":"Christian","sex":   │"BASENAME" │{"name":"Risto","sex":"1",   │
    # │"1","rid":1,"lang":"sv","pos"│           │"rid":2,"lang":"fi","pos":"fi│
    # │:"firstname"}                │           │rstname"}                    │
    # └─────────────────────────────┴───────────┴─────────────────────────────┘

    def __init__(self, nimi=None):
        """Creating reference name
        The name is saved with first letter capitalized
        """
        if nimi:
            self.name = nimi.strip().title()
        else:
            self.name = None
        self.uniq_id = None

    def __eq__(self, other):
        "You may compare 'refname1 == refname2'"
        if isinstance(other, self.__class__):
            return self.name() == other.name()
        else:
            return False

    def __str__(self):
        s = "(:REFNAME id:{}, name:'{}'".format(self.uniq_id, self.name)
        if "sex" in dir(self) and self.sex:
            s += ", sex:{}".format(self.sex)
        if "refname" in dir(self):
            s += ") -[{}]-> (Refname ".format(self.reftype)
            if "vid" in dir(self):
                s += "id:{}, ".format(self.vid)
            s += "name:'{}'".format(self.refname)
        s += ")"
        return s

    @classmethod
    def from_node(cls, node):
        """
        Transforms a db node to an object of type Refname.

        <Node ... >
        """
        n = cls()
        n.uniq_id = node.id
        n.id = node["id"] or ""
        n.name = node["name"]
        n.source = node["source"]
        if "sex" in node:
            n.sex = node["sex"]
        else:
            n.sex = SEX_UNKOWN

        return n

    def sex_str(self):
        " Returns sex as string"
        return Person.convert_sex_to_str(self.sex)

    def save(self, tx=None):
        """Saving a Refname to the database (with optional transaction).
        Self (a Refname) may be -
        - a name without other reference (A:{name:name})
        - a name with reference to a base name
            (A:{name:name}) -[:BASENAME]-> (B:{name:refname})
        - a name with reference to parent's name
            (A:{name:name}) -[:PARENTNAME]-> (B:{name:refname})
        This object must have:
        - name (Name)
        The identifier is an ID(Refname)
        - uniq_id (int)
        Optional arguments:
        - gender ('M'/'F'/'')
        - source (str)
        - reftype (in REFTYPES)
        - reference
          (A:Refname {nimi:'Name'})
               -[r:BASENAME|PARENTNAME {use:'Reftype'}]->
               (B:Refname {name:'Refname'})
        """
        # TODO: the source should be a new Source object?

        if not self.name:
            raise ValueError("No name for Refname")

        if tx:  # Use transaction
            session = tx
        else:  # No transaction
            session = shareds.driver.session()

        # Setting attributes for 'A'
        a_attr = {"name": self.name}
        if hasattr(self, "sex"):
            a_attr["sex"] = self.sex
        if hasattr(self, "source"):
            a_attr["source"] = self.source

        if hasattr(self, "refname"):
            # Create a reference (A:{name:name}) --> (B:{name:refname})
            # If any of A or B is missing, they are created, too
            if self.reftype in ["father", "mother"]:
                query = CypherRefname.link_parentname
            else:  # ['firstname', 'surname', 'patronyme']
                query = CypherRefname.link_basename
            try:
                result = session.run(
                    query,
                    use=self.reftype,
                    a_name=self.name,
                    a_attr=a_attr,
                    b_name=self.refname,
                )

                #                 logging.debug("Created {} nodes and {} relations for {}-->{}".format(\
                #                         result.consume().counters.nodes_created,
                #                         result.consume().counters.relationships_created,
                #                         self.name, self.refname))
                counters = shareds.db.consume_counters(result)
                logger.debug(f"For {self.name}-->{self.refname} created {counters}")
            #                     for record in result:
            #                         a_oid = record["aid"]
            #                         a_name = record["aname"]
            #                         a_use = record['use']
            #                         b_oid = record["bid"]
            #                         b_name = record["bname"]
            #                         logger.debug('  ({}, {}) -[{}]-> ({}, {})'.
            #                                       format(a_oid, a_name, a_use, b_oid, b_name))

            except Exception as err:
                print("iError: {0}".format(err), file=stderr)
                logger.warning(
                    "Could no store (a) -[:{}]-> (b): {}".format(self.reftype, err)
                )

        else:
            # Create (A:{name:name}) only (if needed)
            try:
                result = session.run(
                    CypherRefname.save_single, a_name=self.name, a_attr=a_attr
                )

                #                 logging.debug("Created {} node for {}".format(\
                #                         result.consume().counters.nodes_created,
                #                         self.name))
                counters = shareds.db.consume_counters(result)
                logger.debug(f"For {self.name} created {counters}")
            #                 for record in result:
            #                     a_oid = record["aid"]
            #                     a_name = record["aname"]
            #                     logging.debug('  ({}, {})'.format(a_oid, a_name))

            except Exception as err:
                # Ei ole kovin fataali, ehkä jokin attribuutti hukkuu?
                print("iError: {0}".format(err), file=stderr)
                logger.warning("Lisääminen (a) ei onnistunut: {}".format(err))

    # Moved to -> pe.neo4j.updateservice.Neo4jUpdateService.ds_build_refnames / 2021 JMä
    #     @staticmethod
    #     def link_to_refname(tx, pid, name, reftype):
    #         # Connects a reference name of type reftype to Person(pid)

    @staticmethod
    def recreate_refnames():
        """Deletes all refnames and their relations and
        defines unique constraint for refnames."""

        with shareds.driver.session() as session:
            try:
                # Remove all Refnames
                t0 = time.time()
                result = session.run(CypherRefname.delete_all)
                counters = shareds.db.consume_counters(result)
                logger.info(
                    "Deleted all Refnames: {}; {} sek".format(
                        counters, time.time() - t0
                    )
                )
            except Exception as e:
                logger.error(f"Refname delete failed: {e.__class__.__name__}, {e}")

            try:
                # Create unique constrain for Refnames
                t0 = time.time()
                result = session.run(CypherRefname.set_constraint)
                counters = shareds.db.consume_counters(result)
                logger.info(
                    "Set unique constraint for Refnames: {}; {} sek".format(
                        counters, time.time() - t0
                    )
                )
            except Exception as e:  # ClientError in neo4j 4.0
                logger.info(
                    f"Unique constraint for Refnames ok: {e.__class__.__name__}"
                )

    # Removed / 2021 JMä
    #     @staticmethod
    #     def get_refname(name):
    #         """ Find a reference name for given name (for ex. 'Aaron')
    #     @staticmethod
    #     def get_name_reference(name):
    #     @staticmethod
    #     def get_typed_refnames(reftype=""):
    #         """ Read all refnames and a list of names, which refer them.

    @staticmethod
    def get_refnames():
        """Get all Refnames
                    Returns a list of Refname objects, with referenced names, reftypes
                    and count of usages.
        # ╒═══════╤═══════════════════════╤═══════════════════════╤═════════════╤══════╕
        # │"ID(n)"│"n"                    │"r_ref"                │"l_uses"     │"uses"│
        # ╞═══════╪═══════════════════════╪═══════════════════════╪═════════════╪══════╡
        # │32348  │{"sex":"1","name":"A   │[[null,null,null]]     │[]           │0     │
        # │       │lex","source":"Pojat 19│                       │             │      │
        # │       │90-luvulla"}           │                       │             │      │
        # ├───────┼───────────────────────┼───────────────────────┼─────────────┼──────┤
        # │32352  │{"sex":"1","name":"A   │[["BASENAME","firstname│["firstname"]│3     │
        # │       │lexander","source":"Mes│",{"sex":"1","name":   │             │      │
        # │       │su- ja kalenteri"}     │"Aleksi","source":"Mess│             │      │
        # │       │                       │u- ja kalenteri"}]]    │             │      │
        # ├───────┼───────────────────────┼───────────────────────┼─────────────┼──────┤
        # │61368  │{"name":"Persson"}     │[["PARENTNAME","father"│[]           │0     │
        # │       │                       │,{"sex":"1","name":"   │             │      │
        # │       │                       │Pekka","source":"Pojat"│             │      │
        # │       │                       │}],["BASENAME",null,{"n│             │      │
        # │       │                       │ame":"Pekanpoika"}]]   │             │      │
        # └───────┴───────────────────────┴───────────────────────┴─────────────┴──────┘
        """
        try:
            ret = []
            results = shareds.driver.session().run(CypherRefname.get_all)
            for result in results:
                node = result["n"]
                rn = Refname.from_node(node)
                reftypes = []
                refnames = []
                for typ, role, r_node in result["r_ref"]:
                    # Referenced name exists
                    if typ:
                        # in ('REFNAME', 'BASENAME', 'PARENTNAME'):
                        # print(f'# {rn} -> {role} {r_node["name"]} -> {result["l_uses"]}')
                        if role:
                            reftypes.append(role)
                        if r_node:
                            refnames.append(r_node["name"])
                rn.usecount = result["uses"]
                if rn.usecount > 0:
                    # References from a Person exists
                    for l in result["l_uses"]:
                        if not l in reftypes:
                            reftypes.append(l)
                    reftypes.reverse()
                rn.refname = ", ".join(refnames)
                rn.reftype = ", ".join(reftypes)
                ret.append(rn)
            return ret

        except Exception as err:
            print("iError (Refname.get_refnames): {0}".format(err), file=stderr)
            return []


class RefnameReader:
    """
    NOT YET IN USE. Abstracted Reference name datastore for reading.

    Data reading class for Refname objects with associated data.

    - Returns a Result object which includes the items and eventuel error object.

    #TODO: Should move Refname.get_refnames() here
    """

    def __init__(self, readservice, u_context):
        """Initiate datastore.

        :param: readservice   pe.neo4j.readservice.Neo4jReadService
        :param: u_context     ui.user_context.UserContext object
        """
        self.readservice = readservice
        self.driver = readservice.driver
        self.user_context = u_context
