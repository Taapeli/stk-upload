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
import flask_security
import shareds


class User:
    """ Käyttäjä
            
        Properties:            example
                userid         User123
                name           "Matti Mainio"
                roles[]        ?
     """
    def __init__(self, userid):
        self.userid = flask_security.current_user.username
        self.name = None
        self.roles = []

    def __str__(self):
        return "{}: {} {}".format(self.user_id, self.name, self.roles)

    def save(self):
        """ Käyttäjä tallennetaan kantaan, jos hän ei jo ole siellä"""

        try:
            query = "MERGE (u:User { userid: {uid} }) SET u.name={name}"
            shareds.driver.session().run(query, {"uid": self.userid, "name": self.name})
    
        except Exception as err:
            print("Virhe: {0}".format(err), file=sys.stderr)
            raise
            
        
    def get_ids_and_refnames_of_people_of_user(self):
        """ TODO Korjaa: refname-kenttää ei ole, käytä Refname-nodea
            Etsi kaikki käyttäjän henkilöt"""
        
        query = """
MATCH (u:User)-[r:REVISION]->(p:Person)-[s:NAME]->(n:Name) 
WHERE u.userid='{}'
RETURN ID(p) AS id, n.refname AS refname
            """.format(self.userid)
        return shareds.driver.session().run(query)
        
        
    def get_refnames_of_people_of_user(self):
        """ TODO Korjaa: refname-kenttää ei ole, käytä Refname-nodea
            Etsi kaikki käyttäjän henkilöt"""
        
        query = """
MATCH (u:User)-[r:REVISION]->(p:Person)-[s:NAME]->(n:Name) 
WHERE u.userid='{}'
RETURN p.handle AS handle, n.refname AS refname
            """.format(self.userid)
        return shareds.driver.session().run(query)
        
        
    def get_revisions_of_the_user(self):
        """ Etsi kaikki käyttäjän versiot"""
        
        query = """
MATCH (u:User)-[r:REVISION]->() 
WHERE u.userid='{}'
RETURN distinct r.date AS date ORDER BY r.date
            """.format(self.userid)
        return shareds.driver.session().run(query)
        
        
    @staticmethod       
    def get_all():
        """ Listaa kaikki käyttäjätunnukset"""
        
        query = """
MATCH (u:User) 
RETURN u.userid AS userid, u.name AS name
ORDER BY u.userid
            """
        return shareds.driver.session().run(query)

                
    
    @staticmethod       
    def beginTransaction():
        """ Aloittaa transaction """
                        
        tx = shareds.driver.session().begin_transaction()

        return tx


    @staticmethod       
    def endTransaction(tx):
        """ Lopettaa transaction """
                        
        tx.commit()

