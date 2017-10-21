'''
Created on 2.5.2017 from Ged-prepare/Bus/classes/genealogy.py

@author: jm
'''
import logging
from sys import stderr
from flask import g

class Refname:
    """
        ( Refname {oid, nimi} ) -[reftype]-> (Refname)
                   reftype = (etunimi, sukunimi, patronyymi)
        Properties:                                             input source
            oid     1, 2 ...                                    (created in save())
            name    1st letter capitalized                      (Nimi)
            refname * the std name referenced, if exists        (RefNimi)
            reftype * which kind of reference refname points to ('REFFIRST')
            gender  gender 'F', 'M' or ''                       (Sukupuoli)
            source  points to Source                            (Lähde)
            
        * Note: refnamea ja reftypeä ei talleteta tekstinä, vaan kannassa tehdään
                viittaus tyyppiä reftype ko Refname-olioon
    """
    # TODO: source pitäisi olla viite lähdetietoon, nyt sinne on laitettu lähteen nimi

    label = "Refname"
    REFTYPES = ['REFFIRST', 'REFLAST', 'REFPATRO']

#   Type-property poistettu tarpeettomana. Esim. samasta nimestä "Persson" voisi
#   olla linkki REFLAST nimeen "Pekanpoika" ja REFPATRO nimeen "Pekka".
#   Ei tarvita useita soluja.
#   __REFNAMETYPES = ['undef', 'fname', 'lname', 'patro', 'place', 'occu']

    def __init__(self, nimi):
        """ Luodaan referenssinimi
            Nimi talletetaan alkukirjain isolla, alku- ja loppublankot poistettuna
        """
        if nimi:
            self.name = nimi.strip().title()
        else:
            self.name = None


    def __eq__(self, other):
        "Mahdollistaa vertailun 'refname1 == refname2'"
        if isinstance(other, self.__class__):
            return self.name() == other.name()
        else:
            return False


    def __str__(self):
        s = "(Refname {0}oid={1}, name='{2}'".format('{', self.oid, self.name)
        if 'gender' in dir(self):
            s += ", gender={}".format(self.gender)
        if 'refname' in dir(self):
            s += "{0}) -[{1}]-> (Refname {2}".format('}', self.reftype, '{')
            if 'vid' in dir(self):
                s += "oid={}, ".format(self.vid)
            s += "name='{}'".format(self.refname)
        s += "{})".format('}')
        return s


    def save(self):
        """ Referenssinimen tallennus kantaan. Kysessä on joko 
            - nimi ilman viittausta, olkoon (A:{name=name})
            - nimi ja viittaus, (A:{name=name})-->(B:{name=refname})
            Edellytetään, että tälle oliolle on asetettu:
            - name (Nimi)
            Tunniste luodaan tai käytetään sitä joka löytyi kannasta
            - oid (int)
            Lisäksi tallennetaan valinnaiset tiedot:
            - gender (Sukupuoli='M'/'N'/'')
            - source (Lähde merkkijonona)
            - reference 
              (a:Refname {nimi='Nimi'}) -[r:Reftype]-> (b:Refname {nimi='RefNimi'})
        """
        # TODO: source pitäisi tallettaa Source-objektina
        
        
        # Pakolliset tiedot
        if not self.name:
            raise NameError
        
        # Asetetaan A:n attribuutit
        a_attr = "{name:'" + self.name + "'"
        if hasattr(self, 'gender'):
            a_attr += ", gender:'{}'".format(self.gender)
        if hasattr(self, 'source'):
            a_attr += ", source:'{}'".format(self.source)
        a_attr += '}'
#        a_newoid = get_new_oid()

        if hasattr(self, 'refname'):
            # Luodaan viittaus (A:{name=name})-->(B:{name=refname})
            # Jos A tai B puuttuvat kannasta, ne luodaan
            b_attr = "{name:'" + self.refname + "'}"
#            b_newoid = get_new_oid()
            query="""
MERGE (a:Refname {})
MERGE (b:Refname {})
CREATE UNIQUE (a)-[:REFFIRST]->(b)
RETURN a.id AS aid, a.name AS aname, b.id AS bid, b.name AS bname;""".format(a_attr, b_attr)
                
            try:
                result = g.driver.session().run(query)
        
                for record in result:
                    a_oid = record["aid"]
                    a_name = record["aname"]
                    b_oid = record["bid"]
                    b_name = record["bname"]
                    
                    logging.debug('Luotiin (a {}:{})'.format(a_oid, a_name))
                    logging.debug('Luotiin (b {}:{})'.format(b_oid, b_name))
                    logging.debug('Luotiin ({}:{})-->({}:{})'.format(a_oid, a_name, b_oid, b_name))
                    
            except Exception as err:
                print("Virhe: {0}".format(err), file=stderr)
                logging.warning('Lisääminen (a)-->(b) ei onnistunut: {}'.format(err))

        else:
            # Luodaan (A:{name=name}) ilman viittausta B:hen
            # Jos A puuttuu kannasta, se luodaan
            query="""
                 MERGE (a:Refname {})
                 RETURN a.id AS aid, a.name AS aname;""".format(a_attr)
            try:
                result = g.driver.session().run(query)
        
                for record in result:
                    a_oid = record["aid"]
                    a_name = record["aname"]
                    
                    logging.debug('Luotiin{} ({}:{})'.format(a_attr,  a_oid, a_name))
                    
            except Exception as err:
                # Ei ole kovin fataali, ehkä jokin attribuutti hukkuu?
                print("Virhe: {0}".format(err), file=stderr)
                logging.warning('Lisääminen (a) ei onnistunut: {}'.format(err))


    @staticmethod   
    def get_refname(name):
        """ Haetaan nimeä (esim. 'Aaron') vastaava referenssi-etunimi
        ╒═══════╕
        │"rname"│
        ╞═══════╡
        │"Aaro" │
        └───────┘
        """
        query="""
MATCH (a:Refname)-[r:REFFIRST]->(b:Refname) WHERE a.name=$nm
RETURN b.name AS rname
LIMIT 1"""
        try:
            return g.driver.session().run(query, nm=name)
        except Exception as err:
            print("Virhe: {0}".format(err), file=stderr)
            logging.warning('Kannan lukeminen ei onnistunut: {}'.format(err))
            return None
            
            
    @staticmethod   
    def get_name(name):
        """ Haetaan referenssinimi
        """
        query="""
            MATCH (a:Refname)-[r:REFFIRST]->(b:Refname) WHERE b.name='{}'
            RETURN a.name AS aname, b.name AS bname;""".format(name)
            
        try:
            return g.driver.session().run(query, name=name)
        
        except Exception as err:
            print("Virhe: {0}".format(err), file=stderr)
            logging.warning('Kannan lukeminen ei onnistunut: {}'.format(err))
        
        
    @staticmethod
    def get_typed_refnames(reftype=""):
        """ Haetaan kannasta kaikki referenssinimet sekä lista nimistä, jotka
            viittaavat ko refnameen. 
            Palautetaan referenssinimen attribuutteja sekä lista nimistä, 
            jotka suoraan tai ketjutetusti viittaavat ko. referenssinimeen
            [Kutsu: datareader.lue_refnames()]
        """
        query="""
MATCH (a:Refname)
  OPTIONAL MATCH (m:Refname)-[:{0}*]->(a:Refname)
  OPTIONAL MATCH (a:Refname)-[:{1}]->(n:Refname)
RETURN a.id, a.name, a.gender, a.source,
  COLLECT ([n.oid, n.name, n.gender]) AS base,
  COLLECT ([m.oid, m.name, m.gender]) AS other
ORDER BY a.name""".format(reftype, reftype)
        return g.driver.session().run(query)


    @staticmethod
    def getrefnames():
        """ Haetaan kannasta kaikki Refnamet 
            Palautetaan lista Refname-olioita, johon on haettu myös mahdollisen
            viitatun referenssinimen nimi ja tyyppi.
            [Kutsu: datareader.lue_refnames()]
        """
        query = """
MATCH (n:Refname)
OPTIONAL MATCH (n:Refname)-[r]->(m)
RETURN n,r,m
ORDER BY n.name"""
        try:
            results = g.driver.session().run(query)
            return Refname._triples_to_objects(results)
        except Exception as err:
            print("Virhe (Refname.getrefnames): {0}".format(err), file=stderr)
            return []


    @staticmethod
    def _triples_to_objects(results):
        # n = <Node id=17378 labels={'Refname'} 
        #      properties={'name': 'Aabeli', 'source': 'harvinainen'}>
        # r = <Relationship id=259 start=17378 end=17439 type='REFFIRST'
        #      properties={}>
        # m = <Node id=17439 labels={'Refname'} 
        #      properties={'name': 'Aapeli', 'gender': 'M', 
        #                  'source': 'Messu- ja kalenteri'}>
        ret = []
        for result in results:
            rn = Refname(result['n']["name"])
            rn.oid = result['n'].id
            rn.gender = result['n']["gender"]
            rn.source = result['n']["source"]
            if result['m']:
                # Referenced name exists
                rn.reftype = result['r'].type
                rn.refname = result['m']["name"]
            ret.append(rn)
        return ret
