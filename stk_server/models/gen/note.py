'''
Created on 2.5.2017 from Ged-prepare/Bus/classes/genealogy.py

@author: jm
'''

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
        """ Reads Note node data by self.uniq_id

            Called from models.datareader.get_person_data_by_id
        """

        with shareds.driver.session() as session:
            note_get = """
MATCH (note:Note)    WHERE ID(note)=$nid
RETURN note"""
            return session.run(note_get, nid=self.uniq_id)


    @staticmethod
    def get_notes(uniq_id):
        """ Reads all Note nodes or selected Note node from db

            Called from models.datareader.get_notes for "table_of_data.html"
        """

        result = None
        with shareds.driver.session() as session:
            if uniq_id:
                query = """
MATCH (n:Note) WHERE ID(note)=$nid
RETURN ID(n) AS uniq_id, n ORDER BY n.type"""
                result =  session.run(query, nid=uniq_id)
            else:
                query = """
MATCH (n:Note)
RETURN ID(n) AS uniq_id, n ORDER BY n.type"""
                result =  session.run(query)

        titles = ['uniq_id', 'handle', 'change', 'id', 'priv', 'type', 'text']
        notes = []

        for record in result:
            # Fill with hyphen for missing information
            note_line = ['-'] * len(titles)
            if record['uniq_id']:
                note_line[0] = record['uniq_id']
            record_n = record['n']
            if record_n['handle']:
                note_line[1] = record_n['handle']
            if record_n['change']:
                note_line[2] = record_n['change']
            if record_n['id']:
                note_line[3] = record_n['id']
            if record_n['priv']:
                note_line[4] = record_n['priv']
            if record_n['type']:
                note_line[5] = record_n['type']
            if record_n['text']:
                note_line[5] = record_n['text']

            notes.append(note_line)

        return (titles, notes)


    @staticmethod
    def get_total():
        """ Tulostaa huomautusten määrän tietokannassa """

        with shareds.driver.session() as session:
            results =  session.run("MATCH (n:Note) RETURN COUNT(n)")
            for result in results:
                return str(result[0])

        return '0'

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
            #print("Virhe (Note.save): {0}".format(err), file=stderr)
            # raise SystemExit("Stopped due to errors")    # Stop processing
            raise ConnectionError("Note.save: {}".format(err))
