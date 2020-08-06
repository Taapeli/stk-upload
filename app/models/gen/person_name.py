'''

    Person Name class

Created on 10.9.2018

@author: jpek@iki.fi
'''
from sys import stderr

import shareds
from .cypher import Cypher_person
from .cypher import Cypher_name

class Name:
    """ Person name.

        Properties:
                type                str Name type: 'Birth name', ...
                order               int name order of Person etc. (from Gramps xml)
                firstname           str etunimi
                surname             str sukunimi
                prefix              str etuliite
                suffix              str patronyme / patronyymi
                citation_handles[]  str gramps handles for citations
                citation_ref[]      int uniq_ids of citation nodes
    """

    def __init__(self, givn='', surn='', pref='', suff=''):
        """ Luo uuden name-instanssin """
        self.type = ''
        self.order = None
        self.firstname = givn
        self.surname = surn
        self.prefix = pref
        self.suffix = suff
        # For gramps xml?
        self.citation_handles = []
        # For person page
        self.citation_ref = []

    def __str__(self):
        # Gedcom style key
        return "{}/{}/{}/{}".format(self.firstname, self.prefix, self.surname, self.suffix)

    def key_surname(self):
        # Standard sort order key "Klick#Brita Helena#Jönsdotter"
        return f"{self.surname}#{self.firstname}#{self.suffix}"

    @classmethod
    def from_node(cls, node):
        '''
        Transforms a db node to an object of type Name
        
        <Node id=80308 labels={'Name'} 
            properties={'firstname': 'Brita Helena', 'suffix': '', 'order': 0, 
                'surname': 'Klick', '': 'Birth Name'}>
        '''
        n = cls()
        n.uniq_id = node.id
        #n.id = node.id    # Name has no id "N0000"
        n.type = node['type']
        n.firstname = node.get('firstname', '')
        n.prefix = node.get('prefix', '')
        n.suffix = node.get('suffix', '')
        n.surname = node.get('surname', '')
        n.order = node['order']
        return n

    def save(self, tx, **kwargs):   #parent_id=None):
        """ Creates or updates this Name node. (There is no handle)
            If parent_id is given, a link (parent) -[:NAME]-> (Name) is created 

            #TODO: Check, if this name exists; then update or create new
        """
        if not 'parent_id' in kwargs:
            raise ValueError("Name.save: no base person defined")

        try:
            n_attr = {
                "order": self.order,
                "type": self.type,
                "firstname": self.firstname,
                "surname": self.surname,
                "prefix": self.prefix,
                "suffix": self.suffix
            }
            tx.run(Cypher_name.create_as_leaf,
                   n_attr=n_attr, parent_id=kwargs['parent_id'], 
                   citation_handles=self.citation_handles)
        except ConnectionError as err:
            raise SystemExit("Stopped in Name.save: {}".format(err))
        except Exception as err:
            print("iError (Name.save): {0}".format(err), file=stderr)            


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
            # <Node id=210189 labels={'Name'} 
            #    properties={'firstname': 'Jan Erik', 'type': 'Birth Name', 
            #        'suffix': 'Jansson', 'surname': 'Mannerheim', 'order': 0}>
            node = record['name']
            fn = node.get('firstname', '')
            vn = node.get('prefix', '')
            sn = node.get('surname', '')
            pn = node.get('suffix', '')
            names.append("{} {} {} {}".format(fn, pn, vn, sn))
        return ' • '.join(names)


    @staticmethod
    def get_personnames(tx=None, uniq_id=None):
        """ Picks all Name versions of this Person or all persons.
        
            Use optionally refnames or sortname for person selection
        """
        if not tx:
            tx = shareds.driver.session()

        if uniq_id:
            result = tx.run(Cypher_person.get_names, pid=uniq_id)
        else:
            result = tx.run(Cypher_person.get_all_persons_names)

        names = []
        for record in result:
            # <Record
            #    pid=82
            #    name=<Node id=83 labels=frozenset({'Name'})
            #        properties={'firstname': 'Jan Erik', 'surname': 'Mannerheimo',
            #            'prefix': '', 'suffix': 'Jansson', 'type': 'Birth Name', 'order': 0}
            # >  >
            node = record['name']
            name = Name.from_node(node)
            name.person_uid =  record['pid']
            names.append(name)
        return names
            

    @staticmethod
    def get_surnames():
        """ Listaa kaikki sukunimet tietokannassa """

        query = """
            MATCH (n:Name) RETURN distinct n.surname AS surname
                ORDER BY n.surname
            """
        return shareds.driver.session().run(query)
