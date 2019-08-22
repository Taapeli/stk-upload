'''
Created on 22.7.2017

@author: jorma-h
'''

from sys import stderr

from .base import NodeObject
from .cypher import Cypher_media
from models.cypher_gramps import Cypher_media_in_batch
import shareds
import os

class Media(NodeObject):
    """ A media object with description, file link and mime information.
    
        Tallenne
            
        Properties:
                handle          
                change
                id              esim. "O0001"
                uniq_id         int database key
                src             str file path
                mime            str mime type
                description     str description
     """

    def __init__(self, uniq_id=None):
        """ Luo uuden media-instanssin """
        NodeObject.__init__(self, uniq_id)

    def __str__(self):
        desc = self.description if len(self.description) < 17 else self.description[:16] + "..."
        return "{}: {} {} {!r}".format(self.id, self.mime, self.src, desc)

    @classmethod
    def from_node(cls, node):
        '''
        Transforms a db node to an object of type Media.
        
        <Node id=100441 labels={'Media'} 
            properties={'description': 'Katarina Borg (1812-1892)', 'handle': '_d78f9fb8e4f180c1212', 
            'id': 'O0005', 'src': 'Sukututkimusdata/Sibelius/katarina_borg.gif', 
            'mime': 'image/gif', 'change': 1524411014}>
        '''
        n = super(Media, cls).from_node(node)
#         n = cls()
#         n.uniq_id = node.id
#         n.id = node['id']
#         n.uuid = node['uuid']
#         n.handle = node['handle']
#         n.change = node['change']
        n.description = node['description']
        n.src = node['src']
        n.mime = node['mime']
        if n.src:
            n.name = os.path.split(n.src)[1]
        else:
            n.name = ""
        return n

    @staticmethod
    def get_medias(uniq_id):
        """ Lukee kaikki tallenteet tietokannasta """
                        
        if uniq_id:
            query = "MATCH (o:Media) WHERE ID(o)=$id RETURN ID(o) AS uniq_id, o"
            return  shareds.driver.session().run(query, id=int(uniq_id))
        else:
            query = "MATCH (o:Media) RETURN ID(o) AS uniq_id, o"
            return  shareds.driver.session().run(query)


    @staticmethod
    def from_uniq_id(uniq_id):
        """ Luetaan tallenteen tiedot """

        record = shareds.driver.session().run(Cypher_media.get_one, rid=uniq_id).single()
        if record:
            return Media.from_node(record['obj'])
        else:
            return None

    def get_data(self):
        """ Luetaan tallenteen tiedot """

        record = shareds.driver.session().run(Cypher_media.get_one, rid=self.id)

        for node in record:
            self.from_node(node)
                    
        return self.id
                
        
    @staticmethod
    def get_total():
        """ Tulostaa tallenteiden määrän tietokannassa """
                        
        query = "MATCH (o:Media) RETURN COUNT(o)"
            
        results =  shareds.driver.session().run(query)
        
        for result in results:
            return str(result[0])


    def print_data(self):
        """ Tulostaa tiedot """
        print ("***** Media *****")
        print ("Handle: " + self.handle)
        print ("Change: {}".format(self.change))
        print ("Id: " + self.id)
        print ("Src: " + self.src)
        print ("Mime: " + self.mime)
        print ("Description: " + self.description)
        return True


    def save(self, tx, batch_id=None):
        """ Saves this Media object to db.
        
            #TODO: Can there be Notes for media?
        """
        if batch_id == None:
            raise RuntimeError(f"Media.save needs batch_id for {self.id}")

        m_attr = {}
        try:
            m_attr = {
                "uuid": self.newUuid(),
                "handle": self.handle,
                "change": self.change,
                "id": self.id,
                "batch_id":batch_id,
                "src": self.src,
                "mime": self.mime,
                "description": self.description
            }
            result = tx.run(Cypher_media_in_batch.create, bid=batch_id, m_attr=m_attr)
            self.uniq_id = result.single()[0]
        except Exception as err:
            print(f"iError Media_save: {err} attr={m_attr}", file=stderr)
            raise RuntimeError(f"Could not save Media {self.id}")
