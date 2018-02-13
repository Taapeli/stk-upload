'''
Created on 2.5.2017 & 14.1.2018 from Ged-prepare/Bus/classes/genealogy.py

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
'''
import logging
from sys import stderr
import time
import shareds
from models.gen.cypher import Cypher

# Global allowed reference types in Refname.reftype field or use attribute in db
REFTYPES = ['basename', 'firstname', 'surname', 'patronyme', 'father', 'mother']

class Refname:
    """
        ( Refname {rid, nimi} ) -[reftype]-> (Refname)
                   reftype = (etunimi, sukunimi, patronyymi)
        Properties:                                             input source
            rid     ID() ...                                    (created in save())
            name    1st letter capitalized                      (Nimi)
            refname * the std name referenced, if exists        (RefNimi)
            reftype * which kind of reference refname points to ('firstname')
            gender  gender 'F', 'M' or ''                       (Sukupuoli)
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
# │{"name":"Gustav","gender":"M"│"BASENAME" │{"name":"Kustaa","gender":"M"│
# │,"rid":3,"lang":"sv","pos":"f│           │,"rid":4,"lang":"fi","pos":"f│
# │irstname"}                   │           │irstname"}                   │
# ├─────────────────────────────┼───────────┼─────────────────────────────┤
# │{"name":"Johansson","rid":5,"│"PARENTNAME│{"name":"Juha","gender":"M","│
# │lang":"sv","pos":"patronym"} │"          │lang":"fi","rid":6,"pos":"fir│
# │                             │           │stname"}                     │
# ├─────────────────────────────┼───────────┼─────────────────────────────┤
# │{"name":"Christian","gender":│"BASENAME" │{"name":"Risto","gender":"M",│
# │"M","rid":1,"lang":"sv","pos"│           │"rid":2,"lang":"fi","pos":"fi│
# │:"firstname"}                │           │rstname"}                    │
# └─────────────────────────────┴───────────┴─────────────────────────────┘

    def __init__(self, nimi):
        """ Creating reference name
            The name is saved with first letter capitalized
        """
        if nimi:
            self.name = nimi.strip().title()
        else:
            self.name = None
        self.rid = None


    def __eq__(self, other):
        "You may compare 'refname1 == refname2'"
        if isinstance(other, self.__class__):
            return self.name() == other.name()
        else:
            return False


    def __str__(self):
        s = "(:REFNAME id:{1}, name:'{2}'".format(self.rid, self.name)
        if 'gender' in dir(self):
            s += ", gender:{}".format(self.gender)
        if 'refname' in dir(self):
            s += ") -[{1}]-> (Refname ".format(self.reftype)
            if 'vid' in dir(self):
                s += "id:{}, ".format(self.vid)
            s += "name:'{}'".format(self.refname)
        s += ")"
        return s


    def save(self):
        """ Saving a Refname to the database. It may be - 
            - a name without other reference (A:{name:name})
            - a name with reference to a base name
                (A:{name:name}) -[:BASENAME]-> (B:{name:refname})
            - a name with reference to parent's name
                (A:{name:name}) -[:PARENTNAME]-> (B:{name:refname})
            This object must have:
            - name (Name)
            The identifier is an ID(Refname)
            - rid (int)
            Optional arguments:
            - gender ('M'/'F'/'')
            - source (str)
            - reftype (in REFTYPES)
            - reference 
              (A:Refname {nimi:'Name'})
                   -[r:BASENAME|PARENTNAME {use:'Reftype'}]-> 
                   (B:Refname {name:'Refname'})
        """
        # TODO: the source should be a new Source object
        
        if not self.name:
            raise ValueError("No name for Refname")

        # Setting attributes for 'A'
        a_attr = {'name': self.name}
        if hasattr(self, 'gender'):
            a_attr['gender'] = self.gender
        if hasattr(self, 'source'):
            a_attr['source'] = self.source
#        a_newoid = get_new_oid()

        if hasattr(self, 'refname'):
            # Create a reference (A:{name:name}) --> (B:{name:refname})
            # If any of A or B is missing, they are created, too
            if self.reftype in ['father', 'mother']:
                link_type = "PARENTNAME"
            else:   # ['firstname', 'surname', 'patronyme']
                link_type = "BASENAME"
            try:
                with shareds.driver.session() as session:
                    result = session.run(Cypher.refname_save(link_type), 
                                         use=self.reftype,
                                         a_name=self.name, a_attr=a_attr,
                                         b_name=self.refname)
        
                    logging.debug("Created {} nodes and {} relations for {}-->{}".format(\
                            result.summary().counters.nodes_created, 
                            result.summary().counters.relationships_created, 
                            self.name, self.refname))
#                     for record in result:
#                         a_oid = record["aid"]
#                         a_name = record["aname"]
#                         a_use = record['use']
#                         b_oid = record["bid"]
#                         b_name = record["bname"]
#                         logging.debug('  ({}, {}) -[{}]-> ({}, {})'.
#                                       format(a_oid, a_name, a_use, b_oid, b_name))
                    
            except Exception as err:
                print("Error: {0}".format(err), file=stderr)
                logging.warning('Could no store (a) -[:{}]-> (b): {}'.format(link_type, err))

        else:
            # Create (A:{name:name}) only (if needed)
            query="""
MERGE (a:Refname {name: $a_name}) SET a = $a_attr
RETURN ID(a) AS aid, a.name AS aname"""
            try:
                with shareds.driver.session() as session:
                    result = session.run(query, 
                                         a_name=self.name, a_attr=a_attr)

                    logging.debug("Created {} nodes for {}".format(\
                            result.summary().counters.nodes_created, 
                            self.name))
#                 for record in result:
#                     a_oid = record["aid"]
#                     a_name = record["aname"]
#                     logging.debug('  ({}, {})'.format(a_oid, a_name))
                    
            except Exception as err:
                # Ei ole kovin fataali, ehkä jokin attribuutti hukkuu?
                print("Error: {0}".format(err), file=stderr)
                logging.warning('Lisääminen (a) ei onnistunut: {}'.format(err))


    @staticmethod
    def link_to_refname(pid, name, reftype):
        # Connects reference name of type reftype to Person(pid)

        if not name > "":
            logging.warning("Missing name {} for {} - not added".format(reftype, name))
            return
        if not (reftype in REFTYPES):
            raise ValueError("Invalid reftype {}".format(reftype))

        try:
            with shareds.driver.session() as session:
                result = session.run(Cypher.refname_link_to, 
                                     pid=pid, name=name, use=reftype)

                logging.debug("Created {} nodes for {}".format(\
                        result.summary().counters.nodes_created, name))

        except Exception as err:
            # Ei ole kovin fataali, ehkä jokin attribuutti hukkuu?
            print("Error: {0}".format(err), file=stderr)


    @staticmethod
    def recreate_refnames():
        # Deletes all refnames and their relations and
        # defines unique constraint for refnames

        with shareds.driver.session() as session:
            try:
                # Remove all Refnames
                t0 = time.time()
                result = session.run(Cypher.refnames_delete_all)
                counters = result.summary().counters
                logging.info("Deleted all Refnames: {}; {} sek".\
                              format(counters, time.time()-t0))

                # Create unique constrain for Refnames
                t0 = time.time()
                result = session.run(Cypher.refnames_set_constraint)
                counters = result.summary().counters
                logging.info("Set unique constraint for Refnames: {}; {} sek".\
                              format(counters, time.time()-t0))

            except Exception as err:
                logging.error("Error: {0}".format(err))



#     @staticmethod   
#     def get_refname(name):
#         """ Find a reference name for given name (for ex. 'Aaron')
#         ╒═══════╕
#         │"rname"│
#         ╞═══════╡
#         │"Aaro" │
#         └───────┘
#         """
#         query="""
# MATCH (a:Refname {name:$mn}) -[:BASENAME*]-> (b) 
# RETURN b.name AS rname
# LIMIT 1"""
#         try:
#             return shareds.driver.session().run(query, nm=name)
#         except Exception as err:
#             print("Virhe: {0}".format(err), file=stderr)
#             logging.warning('Kannan lukeminen ei onnistunut: {}'.format(err))
#             return None
            
            
#     @staticmethod   
#     def get_name_reference(name):
#         """ Haetaan referenssinimi
#         """
#         query="""
#             MATCH (a:Refname)-[r:REFFIRST]->(b:Refname) WHERE b.name='{}'
#             RETURN a.name AS aname, b.name AS bname;""".format(name)
#             
#         try:
#             return shareds.driver.session().run(query, name=name)
#         
#         except Exception as err:
#             print("Virhe: {0}".format(err), file=stderr)
#             logging.warning('Kannan lukeminen ei onnistunut: {}'.format(err))
        
        
#     @staticmethod
#     def get_typed_refnames(reftype=""):
#         """ Read all refnames and a list of names, which refer them.
#             No in use!
# 
#             Palautetaan referenssinimen attribuutteja sekä lista nimistä, 
#             jotka suoraan tai ketjutetusti viittaavat ko. referenssinimeen
#             [Kutsu: datareader.lue_refnames()]
#         """
#         query="""
# MATCH (a:Refname)
#   OPTIONAL MATCH (m:Refname)-[:{0}*]->(a:Refname)
#   OPTIONAL MATCH (a:Refname)-[:{1}]->(n:Refname)
# RETURN a.id, a.name, a.gender, a.source,
#   COLLECT ([ID(n), n.name, n.gender]) AS base,
#   COLLECT ([ID(m), m.name, m.gender]) AS other
# ORDER BY a.name""".format(reftype, reftype)
#         return shareds.driver.session().run(query)


    @staticmethod
    def get_refnames():
        """ Get all Refnames
            Returns a list of Refname objects, with referenced names, reftypes
            and count of usages.
            [Call: datareader.read_refnames()]
# ╒═══════╤═══════════════════════╤═══════════════════════╤═════════════╤══════╕
# │"ID(n)"│"n"                    │"r_ref"                │"l_uses"     │"uses"│
# ╞═══════╪═══════════════════════╪═══════════════════════╪═════════════╪══════╡
# │32348  │{"gender":"M","name":"A│[[null,null,null]]     │[]           │0     │
# │       │lex","source":"Pojat 19│                       │             │      │
# │       │90-luvulla"}           │                       │             │      │
# ├───────┼───────────────────────┼───────────────────────┼─────────────┼──────┤
# │32352  │{"gender":"M","name":"A│[["BASENAME","firstname│["firstname"]│3     │
# │       │lexander","source":"Mes│",{"gender":"M","name":│             │      │
# │       │su- ja kalenteri"}     │"Aleksi","source":"Mess│             │      │
# │       │                       │u- ja kalenteri"}]]    │             │      │
# ├───────┼───────────────────────┼───────────────────────┼─────────────┼──────┤
# │61368  │{"name":"Persson"}     │[["PARENTNAME","father"│[]           │0     │
# │       │                       │,{"gender":"M","name":"│             │      │
# │       │                       │Pekka","source":"Pojat"│             │      │
# │       │                       │}],["BASENAME",null,{"n│             │      │
# │       │                       │ame":"Pekanpoika"}]]   │             │      │
# └───────┴───────────────────────┴───────────────────────┴─────────────┴──────┘
        """
        try:
            ret = []
            results = shareds.driver.session().run(Cypher.refnames_get)
            for result in results:
                rn = Refname(result['n']["name"])
                rn.rid = result['n'].id
                rn.gender = result['n']["gender"]
                rn.source = result['n']["source"]
                reftypes = []
                refnames = []
                for r in result['r_ref']:
                    # Referenced name exists
                    # r[0] is in ('BASENAME', 'PARENTNAME')
                    if r[1]:
                        reftypes.append(r[1])
                    if r[2]:
                        refnames.append(r[2]["name"])
                rn.usecount = result["uses"]
                if rn.usecount > 0:
                    # References from a Person exists
                    for l in result['l_uses']:
                        if not l in reftypes:
                            reftypes.append(l)
                rn.refname = ", ".join(refnames)
                rn.reftype = ", ".join(reftypes)
                ret.append(rn)
            return ret

        except Exception as err:
            print("Error (Refname.get_refnames): {0}".format(err), file=stderr)
            return []
