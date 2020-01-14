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
        self.description = ""
        self.src = None
        self.mime = None
        self.name = ""

    def __str__(self):
        desc = self.description if len(self.description) < 17 else self.description[:16] + "..."
        return f"{self.id}: {self.mime} {self.src} {desc!r}"

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
    def get_medias(uniq_id=None, o_filter=None, limit=100):
        """ Lukee kaikki tallenteet tietokannasta """
                        
        if uniq_id:
            query = "MATCH (o:Media) WHERE ID(o)=$id RETURN o"
            return  shareds.driver.session().run(query, id=uniq_id)
        elif o_filter:
            user = o_filter.user
            query = "MATCH (prof:UserProfile) -[:HAS_LOADED]-> (b:Batch) -[:OWNS]-> (o:Media) WHERE  prof.username = $user RETURN o ORDER BY o.description LIMIT $limit"
            return  shareds.driver.session().run(query, user=user, limit=limit)
        else:
            query = "MATCH (o:Media) RETURN o"
            return  shareds.driver.session().run(query)


    @staticmethod
    def get_one(oid):
        """ Read a Media object, selected by UUID or uniq_id.
        
            Luetaan tallenteen tiedot
        """
        if oid:
            with shareds.driver.session() as session:
                if isinstance(oid, int):
                    # User uniq_id
                    record = session.run(Cypher_media.get_by_uniq_id,
                                         rid=oid).single()
                else:
                    # Use UUID
                    record = session.run(Cypher_media.get_by_uuid,
                                         rid=oid).single()

                if record:
                    return Media.from_node(record['obj'])
        return None

        
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


    def save(self, tx, **kwargs):   # batch_id=None):
        """ Saves this new Media object to db.
        
            #TODO: Process also Notes for media?

        """
        if not 'batch_id' in kwargs:
            raise RuntimeError(f"Media.save needs batch_id for parent {self.id}")

        self.uuid = self.newUuid()
        m_attr = {}
        try:
            ##print(f'#Creating Media {self.uuid} {self.src}')
            m_attr = {
                "handle": self.handle,
                "change": self.change,
                "id": self.id,
                "src": self.src,
                "mime": self.mime,
                "description": self.description
            }
            if 'batch_id' in kwargs:
                m_attr['batch_id'] = kwargs['batch_id']
            result = tx.run(Cypher_media_in_batch.create, 
                            bid=kwargs['batch_id'], uuid=self.uuid, m_attr=m_attr)
            self.uniq_id = result.single()[0]
        except Exception as err:
            print(f"iError Media_save: {err.title}\n:** {err} attr={m_attr}", file=stderr)
            raise RuntimeError(f"Could not save Media {self.id}")
