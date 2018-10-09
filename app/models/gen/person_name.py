'''

    Person Name class

Created on 10.9.2018

@author: jpek@iki.fi
'''

import shareds
from .cypher import Cypher_person

class Name:
    """ Nimi

        Properties:
                type            str nimen tyyppi
                alt             str muun nimen numero
                firstname       str etunimi
                surname         str sukunimi
                suffix          str patronyymi
    """

    def __init__(self, givn='', surn='', suff=''):
        """ Luo uuden name-instanssin """
        self.type = ''
        self.alt = ''
        self.firstname = givn
        self.surname = surn
        self.suffix = suff

    def __str__(self):
        return "{}/{}/{}".format(self.firstname, self.surname, self.suffix)

    @classmethod
    def from_node(cls, node):
        '''
        Transforms a db node to an object of type Name
        
        <Node id=80308 labels={'Name'} 
            properties={'firstname': 'Brita Helena', 'suffix': '', 'alt': '', 
                'surname': 'Klick', '': 'Birth Name'}>
        '''
        n = cls()
        n.uniq_id = node.id
        n.id = node.id
        n.type = node['type']
        n.firstname = node['firstname']
        n.suffix = node['suffix']
        n.surname = node['surname']
        n.alt = node['alt']
        return n


    @staticmethod
    def get_people_with_refname(refname):
        """ TODO Korjaa: refname-kenttää ei ole, käytä Refname-nodea
            Etsi kaikki henkilöt, joiden referenssinimi on annettu"""

        query = """
            MATCH (p:Person)-[r:NAME]->(n:Name) WHERE n.refname STARTS WITH '{}'
                RETURN p.handle AS handle
            """.format(refname)
        return shareds.driver.session().run(query)


    @staticmethod
    def get_people_with_same_name():
        """ Etsi kaikki henkilöt, joiden nimi on sama"""

        query = """
            MATCH (p1:Person)-[r1:NAME]->(n1:Name)
            MATCH (p2:Person)-[r2:NAME]->(n2:Name) WHERE ID(p1)<ID(p2)
                AND n2.surname = n1.surname AND n2.firstname = n1.firstname
                RETURN COLLECT ([ID(p1), p1.est_birth, p1.est_death,
                n1.firstname, n1.suffix, n1.surname,
                ID(p2), p2.est_birth, p2.est_death,
                n2.firstname, n2.suffix, n2.surname]) AS ids
            """.format()
        return shareds.driver.session().run(query)


    @staticmethod
    def get_ids_of_people_with_refname_and_user_given(userid, refname):
        """ TODO Korjaa: refname-kenttää ei ole, käytä Refname-nodea
            Etsi kaikki käyttäjän henkilöt, joiden referenssinimi on annettu"""

        query = """
            MATCH (u:User)-[r:REVISION]->(p:Person)-[s:NAME]->(n:Name)
                WHERE u.userid='{}' AND n.refname STARTS WITH '{}'
                RETURN ID(p) AS id
            """.format(userid, refname)
        return shareds.driver.session().run(query)

    @staticmethod
    def get_people_with_surname(surname):
        """ Etsi kaikki henkilöt, joiden sukunimi on annettu"""

        query = """
            MATCH (p:Person)-[r:NAME]->(n:Name) WHERE n.surname='{}'
                RETURN DISTINCT ID(p) AS uniq_id
            """.format(surname)
        return shareds.driver.session().run(query)


    @staticmethod
    def get_clearname(uniq_id=None):
        """ Lists all Name versions of this Person as single cleartext
        """
        result = Name.get_personnames(None, uniq_id)
        names = []
        for record in result:
            fn = record['fn']
            sn = record['sn']
            pn = record['pn']
            names.append("{} {} {}".format(fn, pn, sn))
        return ' • '.join(names)


    @staticmethod
    def get_personnames(tx=None, uniq_id=None):
        """ Picks all Name versions of this Person or all persons
    # ╒═════╤════════════════════╤══════════╤══════════════╤═════╕
    # │"ID" │"fn"                │"sn"      │"pn"          │"sex"│
    # ╞═════╪════════════════════╪══════════╪══════════════╪═════╡
    # │30796│"Björn"             │""        │"Jönsson"     │"M"  │
    # ├─────┼────────────────────┼──────────┼──────────────┼─────┤
    # │30858│"Catharina Fredrika"│"Åkerberg"│""            │"F"  │
    # └─────┴────────────────────┴──────────┴──────────────┴─────┘
        Sex field is not used currently - Remove?
        """
        if not tx:
            tx = shareds.driver.session()

        if uniq_id:
            return tx.run(Cypher_person.get_names, pid=uniq_id)
        else:
            return tx.run(Cypher_person.get_all_persons_names)


    @staticmethod
    def get_surnames():
        """ Listaa kaikki sukunimet tietokannassa """

        query = """
            MATCH (n:Name) RETURN distinct n.surname AS surname
                ORDER BY n.surname
            """
        return shareds.driver.session().run(query)


    @staticmethod
    def set_refname(tx, uniq_id, refname):
        """ TODO Korjaa: refname-kenttää ei ole, käytä Refname-nodea
            Asetetaan etunimen referenssinimi  """

        query = """
MATCH (n:Name) WHERE ID(n)=$id
SET n.refname=$refname
            """
        return tx.run(query, id=uniq_id, refname=refname)