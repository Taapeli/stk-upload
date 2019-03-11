'''
Created on 22.7.2017

@author: jorma-h
'''

from sys import stderr
from models.cypher_gramps import Cypher_media_in_batch
from models.gen.cypher import Cypher_media
import shareds

class Media:
    """ Tallenne
            
        Properties:
                handle          
                change
                id              esim. "O0001"
                uniq_id         int database key
                src             str file path
                mime            str mime type
                description     str description
     """

    def __init__(self):
        """ Luo uuden media-instanssin """
        self.uniq_id = None
        self.handle = ''
        self.change = 0
        self.id = ''

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
        n = cls()
        n.uniq_id = node.id
        n.id = node['id']
        n.handle = node['handle']
        n.change = node['change']
        n.description = node['description'] or ''
        n.src = node['src'] or ''
        n.mime = node['mime'] or ''
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


    def get_data(self):
        """ Luetaan tallenteen tiedot """

        obj_result = shareds.driver.session().run(Cypher_media.get_one, rid=self.id)

        for node in obj_result:
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


    def save(self, tx):
        """ Saves this Media object to db.
        
            #TODO: Can there be Notes for media?
        """

        m_attr = {}
        try:
            m_attr = {
                "handle": self.handle,
                "change": self.change,
                "id": self.id,
                "src": self.src,
                "mime": self.mime,
                "description": self.description
            }
            result = tx.run(Cypher_media_in_batch.create, m_attr=m_attr)
            ids = []
            for record in result:
                self.uniq_id = record[0]
                ids.append(self.uniq_id)
                if len(ids) > 1:
                    print(f"iError updated multiple Medias {self.id} - {ids}, attr={m_attr}")
        except Exception as err:
            print(f"iError Media_save: {err} attr={m_attr}", file=stderr)
            raise RuntimeError(f"Could not save Media {self.id}")
