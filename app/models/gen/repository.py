'''
    Archive, Repository, Source and Citation classes

Created on 2.5.2017 from Ged-prepare/Bus/classes/genealogy.py

@author: Jorma Haapasalo <jorma.haapasalo@pp.inet.fi>
'''

from sys import stderr

from bl.base import NodeObject
from models.cypher_gramps import Cypher_repository_in_batch
from .cypher import Cypher_repository
from bl.note import Note
import shareds
   

class Repository(NodeObject):
    """ Repository / Arkisto.
            
        Properties:
            uniq_id         int    db native key or None
            handle          str    Gramps handle
            change          int    timestamp
            id              str    esim. "R0001"
            rname           str    arkiston nimi
            type            str    arkiston tyyppi
            medium          str    from Source --> Repository relation.medium
            notes           Note[]
     """

    def __init__(self):
        """ Luo uuden repository-instanssin """
        NodeObject.__init__(self)
        self.type = ''
        self.rname = ''
        self.medium = ''
        self.notes = []     # contains Note instances or Note.uniq_id values

        self.sources = []   # For creating display sets (Not used??)

    def __str__(self):
        return f"{self.id} '{self.rname}' {self.medium}"


    @classmethod
    def from_node(cls, node):
        '''
        Transforms a db node to Repository object
        
        <Node id=100269 labels={'Repository'} 
            properties={'handle': '_d7910c4dfa419204848', 'id': 'R0000', 
                'rname': 'Hämeenlinnan kaupunkiseurakunnan arkisto', 
                'type': 'Archive', 'change': '1522861211'}>
        '''
        n = cls()   # Repository
        n.uniq_id = node.id
        n.id = node['id'] or ''
        n.handle = node['handle'] or None
        n.change = node['change'] or 0
        n.rname = node['rname'] or ''
        n.type = node['type'] or ''
        return n


    def get_repo_w_notes(self):
        """ Luetaan arkiston tiedot
            Get Repository with linked Notes

            returns: repo, collect(w) as notes
        """
                        
        with shareds.driver.session() as session:
            return session.run(Cypher_repository.get_w_notes, rid=self.uniq_id)


    @staticmethod
    def obsolete_get_repositories(uniq_id):
        """ Reads all Repository nodes or selected Repository node from db

            OBSOLETE: called only from models.obsolete_datareader.obsolete_get_repositories for 
            "table_of_objects.html"
        """

        result = None
        with shareds.driver.session() as session:
            if uniq_id:
                result =  session.run(Cypher_repository.get_one, rid=uniq_id)
            else:
                result =  session.run(Cypher_repository.get_all)

        titles = ['uniq_id', 'handle', 'change', 'id', 'type', 'name']
        repositories = []

        for record in result:
            # Create a Note object from db Node
            node = record['r']
            n = Repository.from_node(node)
            repositories.append(n)

        return (titles, repositories)


    @staticmethod       
    def get_w_source (uniq_id):
        """ Read repository/repositories from database with their referencing sources.

            For each repository, there may be some sources with different medium.

            Voidaan lukea repositoreja sourceneen kannasta.
        """
        with shareds.driver.session() as session:
            if uniq_id:
                return session.run(Cypher_repository.get_w_sources, rid=uniq_id)
            else:
                return session.run(Cypher_repository.get_w_sources_all)
                
    
    @staticmethod       
    def get_total():
        """ Tulostaa arkistojen määrän tietokannassa """
                        
        query = "MATCH (r:Repository) RETURN COUNT(r)"
        results =  shareds.driver.session().run(query)
        
        for result in results:
            return str(result[0])


    def print_data(self):
        """ Tulostaa tiedot """
        print ("*****Repository*****")
        print ("Handle: " + self.handle)
        print ("Change: {}".format(self.change))
        print ("Id: " + self.id)
        print ("Rname: " + self.rname)
        print ("Type: " + self.type)
        return True


    def save(self, tx,  **kwargs):
        """ Saves this Repository to db under given batch. 
        """
        if not 'batch_id' in kwargs:
            raise RuntimeError(f"Repository.save needs batch_id for {self.id}")

        self.uuid = self.newUuid()
        batch_id = kwargs.get('batch_id', None)
        r_attr = {}
        try:
            r_attr = {
                "uuid": self.uuid,
                "handle": self.handle,
                "change": self.change,
                "id": self.id,
                "rname": self.rname,
                "type": self.type,
            }
#             self.uniq_id = tx.run(Cypher_repository_w_handle.create, r_attr=r_attr).single()[0]
            result = tx.run(Cypher_repository_in_batch.create,
                            bid=batch_id, r_attr=r_attr)
            self.uniq_id = result.single()[0]
        except Exception as err:
            print(f"iError Repository_save: {err} attr={r_attr}", file=stderr)
            raise RuntimeError("Could not save Repository {}".format(self.id))
        
        try:
            # Save the notes attached to self
            if self.notes:
                Note.save_note_list(tx, parent=self, batch_id=batch_id)
        except Exception as err:
            print(f"iError Repository.save note: {err}", file=stderr)
            raise SystemExit("Stopped due to errors")    # Stop processing
            #TODO raise ConnectionError("Repository.save: {0}".format(err))

        return
