'''
    Connecting database and user administration

Created on 2.5.2017 from Ged-prepare/Bus/classes/genealogy.py

@author: Juha Mäkeläinen <jpek@iki.fi> and Jorma Haapasalo <jorma.haapasalo@pp.inet.fi>

    Genealogy database objects are described as a series of class instances
    (which all have previously been included in this genealogy.py):

    genealogy.User, genealogy.Date
    person.Person, person.Name
    family.Family
    place.Place
    event.Event
    note.Note
    refname.Refname
'''

import sys
import logging
from neo4j.v1 import GraphDatabase, basic_auth
from flask import g
import instance.config as config


def connect_db():
    """ Opens a new database connection if there is none yet for the
        current application context.

        Ks. http://neo4j.com/docs/developer-manual/current/#driver-manual-index
    """

    #logging.debug("-- config = {}".format(dir(config)))
    if hasattr(g, 'session'):
        print ("connect_db - already done")
        return g.session

    if hasattr(config,'DB_HOST_PORT'):
        print ("connect_db - server {}".format(config.DB_HOST_PORT))
        driver = GraphDatabase.driver(config.DB_HOST_PORT, \
                                      auth=basic_auth(config.DB_USER, \
                                                      config.DB_AUTH))
        g.session = driver.session()
        #authenticate(config.DB_HOST_PORT, config.DB_USER, config.DB_AUTH)
        #graph = Graph('http://{0}/db/data/'.format(config.DB_HOST_PORT))
    else:
        print ("connect_db - default local – EI TUETTU?")
        driver = GraphDatabase.driver("bolt://localhost", auth=basic_auth("neo4j", "localTaapeli"))
        g.session = driver.session()
    print("connect_db - Sessio {} avattu".format(g.session.connection.server[1]))
    return g.session.connection.server.address
    
    
def alusta_kanta():
    """ Koko kanta tyhjennetään """
    logging.info('Tietokanta tyhjennetään!')
    
#TODO: Korjaa tämä: sch määrittelemättä
#     # Poistetaan vanhat rajoitteet ja indeksit
#     for uv in sch.get_uniqueness_constraints('Refname'):
#         try:
#             sch.drop_uniqueness_constraint('Refname', uv)
#         except:
#             logging.warning("drop_uniqueness_constraint ei onnistunut:", 
#                 sys.exc_info()[0])
#     for iv in sch.get_indexes('Refname'):
#         try:
#             sch.drop_index('Refname', iv)
#         except:
#             logging.warning("drop_index ei onnistunut:", sys.exc_info()[0])
# 
#     # Luodaan Refname:n rajoitteet ja indeksit    
#     refname_uniq = ["oid", "name"]
#     refname_index = ["reftype"]
#     for u in refname_uniq:
#         sch.create_uniqueness_constraint("Refname", u)
#     for i in refname_index:
#         sch.create_index("Refname", i)


class User:
    """ Käyttäjä
            
        Properties:
                userid          esim. User123
     """
     
    @staticmethod       
    def create_user(userid):
        """ Käyttäjä tallennetaan kantaan, jos hän ei jo ole siellä"""

        try:
            record = None
            query = """
                MATCH (u:User) WHERE u.userid='{}' RETURN u.userid
                """.format(userid)
                
            result = g.session.run(query)
            
            for record in result:
                continue
            
            if not record:
                # User doesn't exist in db, the userid should be stored there
                try:
                    query = """
                        CREATE (u:User) 
                        SET u.userid='{}'
                        """.format(userid)
                        
                    g.session.run(query)
            
                except Exception as err:
                    print("Virhe: {0}".format(err), file=sys.stderr)
            
        except Exception as err:
            print("Virhe: {0}".format(err), file=sys.stderr)
        
        
    def get_ids_and_refnames_of_people_of_user(self):
        """ Etsi kaikki käyttäjän henkilöt"""
        
        query = """
            MATCH (u:User)-[r:REVISION]->(p:Person)-[s:NAME]->(n:Name) WHERE u.userid='{}'
                RETURN ID(p) AS id, n.refname AS refname
            """.format(self.userid)
        return g.session.run(query)
        
        
    def get_refnames_of_people_of_user(self):
        """ Etsi kaikki käyttäjän henkilöt"""
        
        query = """
            MATCH (u:User)-[r:REVISION]->(p:Person)-[s:NAME]->(n:Name) WHERE u.userid='{}'
                RETURN p.gramps_handle AS handle, n.refname AS refname
            """.format(self.userid)
        return g.session.run(query)
        
        
    def get_revisions_of_the_user(self):
        """ Etsi kaikki käyttäjän versiot"""
        
        query = """
            MATCH (u:User)-[r:REVISION]->() WHERE u.userid='{}'
                RETURN distinct r.date AS date ORDER BY r.date
            """.format(self.userid)
        return g.session.run(query)
        
        
    @staticmethod       
    def get_all_userids():
        """ Listaa kaikki käyttäjätunnukset"""
        
        query = """
            MATCH (u:User) RETURN u.userid AS userid ORDER BY u.userid
            """
        return g.session.run(query)


class Date():
    """ Päivämäärän muuntofunktioita """

    @staticmethod       
    def range_str(aikamaare):
        """ Karkea aikamäären siivous, palauttaa merkkijonon
        
            Aika esim. '1666.02.20-22' muunnetaan muotoon '1666-02-20 … 22':
            * Tekstin jakaminen sarakkeisiin käyttäen välimerkkiä ”-” 
              tai ”,” (kentät tekstimuotoiltuna)
            * Päivämäärän muotoilu ISO-muotoon vaihtamalla erottimet 
              ”.” viivaksi
         """
        t = aikamaare.replace('-','|').replace(',','|').replace('.', '-')
        if '|' in t:
            osat = t.split('|')
            # osat[0] olkoon tapahtuman 'virallinen' päivämäärä
            t = '%s … %s' % (osat[0], osat[-1])
            if len(osat) > 2:
                logging.warning('Aika korjattu: {} -> {}'.format(aikamaare, t))

        t = t.replace('.', '-')
        return t


