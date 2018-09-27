'''
Created on 2.5.2017 from Ged-prepare/Bus/classes/genealogy.py

Changed 13.6.2018/JMä: get_notes() result from list(str) to list(Note)

@author: jm
'''

from models.cypher_gramps import Cypher_note_w_handle
from models.gen.cypher import Cypher_note
import shareds

class Note:
    """ Note / Huomautus

        Properties:
                handle          str stats with '_' if comes from Gramps
                change          int timestamp from Gramps
                id              esim. "N0001"
                uniq_id         int database key
                priv            int >0 salattu tieto
                type            str huomautuksen tyyppi
                text            str huomautuksen sisältö
     """

    def __init__(self):
        """ Creates a Noteinstance in memory 
        """
        self.uniq_id = None
        self.id = ''
        self.type = ''
        self.handle = ''
        self.change = 0
        self.priv = 0


    @staticmethod
    def from_node(node):
        '''
        Transforms a db node to an object of type Note.
        '''
        n = Note()
        n.uniq_id = node.id
        n.handle = node['handle']
        n.change = node['change']
        n.id = node['id'] or ''
        n.priv = node['priv'] or ''
        n.type = node['type'] or ''
        n.text = node['text'] or ''
        return n


    @staticmethod       
    def get_persons_notes (uniq_id):
        """ Read 'Person -> Event -> Note' and 'Person -> Note' paths

            Haetaan henkilön Citationit, suoraan tai välisolmujen kautta
            
            Returns list of Citations and list of Source ids
        ╒══════╤══════╤══════╤════════════════════════════════════════════════╕
        │"p_id"│"e_id"│"n_id"│"n"                                             │
        ╞══════╪══════╪══════╪════════════════════════════════════════════════╡
        │99833 │81393 │78943 │{"handle":"_dea2effe2b579e6d11c157b268c","text":│
        │      │      │      │"Tornion tuomiokunnan tuomari","id":"N0089","pri│
        │      │      │      │v":"","type":"Event Note","change":1529946203}  │
        ├──────┼──────┼──────┼────────────────────────────────────────────────┤
        │99833 │81409 │78936 │{"handle":"_dea5b1e04a32efc4f77eb368d87","text":│
        │      │      │      │"Kuopion tuomiokunnan 1822","id":"N2057","priv":│
        │      │      │      │"","type":"Event Note","change":1530020220}     │
        └──────┴──────┴──────┴────────────────────────────────────────────────┘
        """
        
        result = shareds.driver.session().run(Cypher_note.get_person_notes, 
                                              pid=uniq_id)
        notes = []
        for record in result:
            pass

        return notes
 
    @staticmethod
    def get_notes(uniq_ids):
        """ Reads Note nodes data from db using given uniq_ids

            Called from models.datareader.get_person_data_by_id
        """

        notes = []
        with shareds.driver.session() as session:
            notes_get = """
MATCH (n:Note)    WHERE ID(n) in $nid
RETURN ID(n) AS uniq_id, n"""
            result = session.run(notes_get, nid=uniq_ids)
            for record in result:
                # Create a Note object from record
                node = record['n']
                n = Note.from_node(node)
                notes.append(n)

        return notes

    @staticmethod
    def get_note_list(uniq_id):
        """ Reads all Note nodes or selected Note node from db

            Called only from models.datareader.get_notes for "table_of_data.html"
        """

        result = None
        with shareds.driver.session() as session:
            if uniq_id:
                query = """
MATCH (n:Note) WHERE ID(note)=$nid
RETURN ID(n) AS uniq_id, n"""
                result =  session.run(query, nid=uniq_id)
            else:
                query = """
MATCH (n:Note)
RETURN ID(n) AS uniq_id, n 
ORDER BY n.type"""
                result =  session.run(query)

        titles = ['uniq_id', 'handle', 'change', 'id', 'priv', 'type', 'text']
        notes = []

        for record in result:
            # Create a Note object from record
            node = record['n']
            n = Note.from_node(node)
            notes.append(n)

        return (titles, notes)


    @staticmethod
    def get_total():
        """ Tulostaa huomautusten määrän tietokannassa """

        with shareds.driver.session() as session:
            results =  session.run("MATCH (n:Note) RETURN COUNT(n)")
            for result in results:
                return str(result[0])

        return '0'

    def __str__(self):
        """ Tulostaa tiedot """
#         print ("*** Note ***")
#         print ("Handle: " + self.handle)
#         print ("Change: " + self.change)
#         #print ("Id: " + self.id)
#         #print ("Priv: " + self.priv)
#         #print ("Type: " + self.type)
#         #print ("Text: " + self.text)
        t = self.text if len(self.text) < 41 else self.text[:37] + '...'
        return ("Note id={}, type={}, priv={} '{}'".\
                format(self.id, self.type, self.priv, t))


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
