'''
Created on 22.7.2017

@author: jorma-h
'''

from sys import stderr

from bl.base import NodeObject
from .cypher import Cypher_media
from .person import Person
from .place import Place
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
        n.description = node['description']
        n.src = node['src']
        n.mime = node['mime']
        if n.src:
            n.name = os.path.split(n.src)[1]
        else:
            n.name = ""
        return n


    @staticmethod
    def read_my_media_list(u_context, limit):
        """ Read Media object list using u_context.
        """
        medias = []
        result = Media.get_medias(uniq_id=None, o_context=u_context, limit=limit)
        for record in result: 
            # <Record o=<Node id=393949 labels={'Media'}
            #        properties={'src': 'Users/Pekan Book/OneDrive/Desktop/Sibelius_kuvat/Aino Järnefelt .jpg',
            #            'batch_id': '2020-01-02.001', 'mime': 'image/jpeg',
            #            'change': 1572816614, 'description': 'Aino Järnefelt (1871-) nro 1',
            #            'id': 'O0001', 'uuid': 'b4b11fbd8c054252b51703769e7a6850'}>
            #    credit='juha'
            #    batch_id='2020-01-02.001'
            #    count=1>
            node = record['o']
            m = Media.from_node(node)
            m.conn = record.get('count', 0)
            m.credit = record.get('credit')
            m.batch = record.get('batch_id')
            medias.append(m)
        
    # Update the page scope according to items really found
        if medias:
            u_context.update_session_scope('media_scope', 
                medias[0].description, medias[-1].description, limit, len(medias))
        return medias
    
    @staticmethod
    def get_medias(uniq_id=None, o_context=None, limit=100):
        """ Reads Media objects from user batch or common data using context. """
                        
        if uniq_id:
            query = "MATCH (o:Media) WHERE ID(o)=$id RETURN o"
            return  shareds.driver.session().run(query, id=uniq_id)
        elif o_context:
            user = o_context.user
            fw_from = o_context.next_name_fw()     # next name
            show_common = o_context.use_common()
            if show_common:
                # Show approved common data
                return shareds.driver.session().run(Cypher_media.read_common_media,
                                                    user=user, start_name=fw_from, limit=limit)
            else:
                # Show user Batch
                return  shareds.driver.session().run(Cypher_media.read_my_own_media,
                                                     start_name=fw_from, user=user, limit=limit)
        else:
            return  shareds.driver.session().run(Cypher_media.get_all)

    @staticmethod
    def get_one(oid):
        """ Read a Media object, selected by UUID or uniq_id.
        
            Luetaan tallenteen tiedot
        """
        if oid:
            with shareds.driver.session() as session:
#                 if isinstance(oid, int):
#                     # User uniq_id
#                     record, record2 = session.run(Cypher_media.get_by_uniq_id,
#                                          rid=oid).single()
#                 else:
                # Use UUID
                record, record2 = session.run(Cypher_media.get_by_uuid,
                                              rid=oid).single()

                if record:
                    # <Node id=435174 labels={'Media'}
                    #    properties={'src': 'Albumi-Silius/kuva002.jpg', 'batch_id': '2020-02-14.001',
                    #        'mime': 'image/jpeg', 'change': 1574187478, 'description': 'kuva002',
                    #        'id': 'O0024', 'uuid': 'fa2e240493434912986c2540b52a9464'}>
                    media = Media.from_node(record)
                    media.ref = []
                    for node, prop in record2:
                        # node = <Node id=435368 labels={'Person'}
                        #    properties={'sortname': 'Silius#Carl Gustaf#', ...}>
                        # ref = {'order': 1, 'right': 100, 'left': 0, 'lower': 96, 'upper': 15}
                        label, = node.labels   # Get the 1st label
                        if label == 'Person':
                            obj = Person.from_node(node)
                        elif label == 'Place':
                            obj = Place.from_node(node)
                        else:
                            obj = None
                        # Has the relation cropping properties?
                        left = prop.get('left')
                        if left != None:
                            upper = prop.get('upper')
                            right = prop.get('right')
                            lower = prop.get('lower')
                            crop = (left, upper, right, lower)
                        else:
                            crop = None

                        # A list [object label, object, relation properties]
                        media.ref.append([label,obj,crop])
                    return (media)
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
