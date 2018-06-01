'''
Created on 2.5.2017 from Ged-prepare/Bus/classes/genealogy.py

@author: jm
'''

from sys import stderr
from models.gramps.cypher_gramps import Cypher_note_w_handle
import shareds

class Note:
    """ Huomautus
            
        Properties:
                handle          
                change
                id              esim. "N0001"
                uniq_id         int database key
                priv            str salattu tieto
                type            str huomautuksen tyyppi
                text            str huomautuksen sisältö
     """

    def __init__(self):
        """ Luo uuden note-instanssin """
        self.uniq_id = None
        self.handle = ''
        self.change = ''
        self.id = ''
        self.priv = ''
        self.type = ''
        
        
    def get_note(self):
        """ Lukee huomautuksen tiedot tietokannasta 
            Called from models.datareader.get_person_data_by_id
        """

        note_get = """
MATCH (note:Note)    WHERE ID(note)=$nid
RETURN note"""
        return shareds.driver.session().run(note_get, nid=self.uniq_id)
                
        
    @staticmethod
    def get_notes(uniq_id):
        """ Lukee kaikki huomautukset tietokannasta 
            Called from models.datareader.get_notes for "table_of_data.html"
        """
                        
        if uniq_id:
            query = """
MATCH (n:Note) WHERE ID(note)=$nid 
RETURN ID(n) AS uniq_id, n ORDER BY n.type"""
        else:
            query = """
MATCH (n:Note)
RETURN ID(n) AS uniq_id, n ORDER BY n.type"""
            
        result =  shareds.driver.session().run(query, nid=uniq_id)
        
        titles = ['uniq_id', 'handle', 'change', 'id', 'priv', 'type', 'text']
        notes = []
        
        for record in result:
            note_line = []
            if record['uniq_id']:
                note_line.append(record['uniq_id'])
            else:
                note_line.append('-')
            if record["n"]['handle']:
                note_line.append(record["n"]['handle'])
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
        """ Creates or updates this Note object as a Note node 
            using handle
        """

        try:
            n_attr = {
                "handle": self.handle,
                "change": self.change,
                "id": self.id,
                "priv": self.priv,
                "type": self.type, 
                "text": self.text
            }
            return tx.run(Cypher_note_w_handle.create, n_attr=n_attr)

        except Exception as err:
            print("Virhe (Note.save): {0}".format(err), file=stderr)
            raise SystemExit("Stopped due to errors")    # Stop processing
            #TODO raise ConnectionError("Note.save: {0}".format(err))
