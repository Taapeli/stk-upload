'''
Created on 2.5.2017 from Ged-prepare/Bus/classes/genealogy.py

@author: jm
'''

from sys import stderr
#from flask import g
import models.dbutil
import  shareds

class Note:
    """ Huomautus
            
        Properties:
                handle          
                change
                id              esim. "N0001"
                priv            str salattu tieto
                type            str huomautuksen tyyppi
                text            str huomautuksen sisältö
     """

    def __init__(self):
        """ Luo uuden note-instanssin """
        self.handle = ''
        self.change = ''
        self.id = ''
        self.priv = ''
        self.type = ''
        
        
    def get_note(self):
        """ Lukee huomautuksen tiedot tietokannasta """

        query = """
            MATCH (note:Note) WHERE ID(note)={} RETURN note
            """.format(self.uniq_id)
            
        return shareds.driver.session().run(query)
                
        
    @staticmethod
    def get_notes(uniq_id):
        """ Lukee kaikki huomautukset tietokannasta """
                        
        if uniq_id:
            where = "WHERE ID(note)={} ".format(uniq_id)
        else:
            where = ''

        query = """
            MATCH (n:Note) {0} RETURN ID(n) AS uniq_id, n ORDER BY n.type
            """.format(where)
            
        result =  shareds.driver.session().run(query)
        
        titles = ['uniq_id', 'gramps_handle', 'change', 'id', 'priv', 'type', 'text']
        notes = []
        
        for record in result:
            note_line = []
            if record['uniq_id']:
                note_line.append(record['uniq_id'])
            else:
                note_line.append('-')
            if record["n"]['gramps_handle']:
                note_line.append(record["n"]['gramps_handle'])
            else:
                note_line.append('-')
            if record["n"]['change']:
                note_line.append(record["n"]['change'])
            else:
                note_line.append('-')
            if record["n"]['id']:
                note_line.append(record["n"]['id'])
            else:
                note_line.append('-')
            if record["n"]['priv']:
                note_line.append(record["n"]['priv'])
            else:
                note_line.append('-')
            if record["n"]['type']:
                note_line.append(record["n"]['type'])
            else:
                note_line.append('-')
            if record["n"]['text']:
                note_line.append(record["n"]['text'])
            else:
                note_line.append('-')
                                
            notes.append(note_line)
                
        return (titles, notes)
        
        
    @staticmethod
    def get_total():
        """ Tulostaa huomautusten määrän tietokannassa """
                        
        query = """
            MATCH (n:Note) RETURN COUNT(n)
            """
            
        results =  shareds.driver.session().run(query)
        
        for result in results:
            return str(result[0])


    def print_data(self):
        """ Tulostaa tiedot """
        print ("*****Note*****")
        print ("Handle: " + self.handle)
        print ("Change: " + self.change)
        print ("Id: " + self.id)
        print ("Priv: " + self.priv)
        print ("Type: " + self.type)
        print ("Text: " + self.text)
        return True


    def save(self, tx):
        """ Tallettaa sen kantaan """

        try:
            query = """
                CREATE (n:Note) 
                SET n.gramps_handle='{}', 
                    n.change='{}', 
                    n.id='{}', 
                    n.priv='{}', 
                    n.type='{}', 
                    n.text='{}'
                """.format(self.handle, self.change, self.id, self.priv, self.type, self.text)
                
            return tx.run(query)
        except Exception as err:
            print("Virhe {}: {}".format(err.__class__.__name__, str(err), file=stderr))
            raise SystemExit("Stopped due to errors")    # Stop processing
