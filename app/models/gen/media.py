'''
Created on 22.7.2017

@author: jorma-h
'''

from sys import stderr

from bl.base import NodeObject #, Status
from bl.event import EventBl
from bl.place import PlaceBl
from bl.family import FamilyBl
from bl.person import PersonBl

#from .cypher import Cypher_media
from .person import Person
#from .place import Place
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


#     @staticmethod
#     def read_my_media_list(u_context, limit):
#         """ Read Media object list using u_context.
#         """
#         medias = []
#         res = Media.get_medias(uniq_id=None, o_context=u_context, limit=limit)
#         #if Status.has_failed(res): return res
#         for record in res.get('recs', None): 
#             # <Record o=<Node id=393949 labels={'Media'}
#             #        properties={'src': 'Users/Pekan Book/OneDrive/Desktop/Sibelius_kuvat/Aino Järnefelt .jpg',
#             #            'batch_id': '2020-01-02.001', 'mime': 'image/jpeg',
#             #            'change': 1572816614, 'description': 'Aino Järnefelt (1871-) nro 1',
#             #            'id': 'O0001', 'uuid': 'b4b11fbd8c054252b51703769e7a6850'}>
#             #    credit='juha'
#             #    batch_id='2020-01-02.001'
#             #    count=1>
#             node = record['o']
#             m = Media.from_node(node)
#             m.conn = record.get('count', 0)
#             m.credit = record.get('credit')
#             m.batch = record.get('batch_id')
#             medias.append(m)
#         
#     # Update the page scope according to items really found
#         if medias:
#             u_context.update_session_scope('media_scope', 
#                 medias[0].description, medias[-1].description, limit, len(medias))
#         return medias
    
#     @staticmethod
#     def get_medias(uniq_id=None, o_context=None, limit=100):
#         """ Reads Media objects from user batch or common data using context. """
#                         
#         with shareds.driver.session(default_access_mode='READ') as session: 
#             if uniq_id:
#                 query = "MATCH (o:Media) WHERE ID(o)=$id RETURN o"
#                 result = session.run(query, id=uniq_id)
# 
#             elif o_context:
#                 #user = o_context.user
#                 user = o_context.batch_user()
#                 fw_from = o_context.first  # From here forward
#                 if user == None:
#                     # Show approved common data
#                     result = session.run(Cypher_media.read_common_media,
#                                          user=user, start_name=fw_from, limit=limit)
#                 else:
#                     # Show user Batch
#                     result =  session.run(Cypher_media.read_my_own_media,
#                                           start_name=fw_from, user=user, limit=limit)
#             else:
#                 result = session.run(Cypher_media.get_all)
# 
#             recs = []
#             for record in result: 
#                 recs.append(record)
#             return {'recs':recs, 'status':Status.OK}

    @staticmethod
    def get_one(oid):
        """ Read a Media object, selected by UUID or uniq_id.
        
            Luetaan tallenteen tiedot
        """
        class MediaReferee():
            ''' Carrier for a referee of media object. '''
            def __init__(self):
                # Referencing object label, object
                self.obj = None
                self.label = None
                self.crop = None
                # If the referring object is Event, also list of:
                # - connected objects
                self.next_objs = []


        if not oid:
            return None

        with shareds.driver.session(default_access_mode='READ') as session:
            # Use UUID
            record = session.run(Cypher_media.get_by_uuid, rid=oid).single()
            # RETURN media,
            #     COLLECT(DISTINCT [properties(r), n]) as m_ref, # Referring event or object
            #     COLLECT(DISTINCT [ID(n), m]) AS e_ref          # Event Person or Family
            if not record:
                return None

            #Record[0]: the Media object
            # <Node id=435174 labels={'Media'}
            #    properties={'src': 'Albumi-Silius/kuva002.jpg', 'batch_id': '2020-02-14.001',
            #        'mime': 'image/jpeg', 'change': 1574187478, 'description': 'kuva002',
            #        'id': 'O0024', 'uuid': 'fa2e240493434912986c2540b52a9464'}>
            media = Media.from_node(record['media'])
            referees = record['m_ref']
            referees_next = record['e_ref']

            # 1. If referrer is an Event, there is also secundary next objects
            event_refs = {}
            for referee_id, node_next in referees_next:
                #record[2]: Indirectly referring Person and Families
                # [  [29373, 
                #     <Node id=29387 labels=frozenset({'Person'})
                #        properties={'sortname': 'Silius#Carl Gustaf#', 'death_high': 1911, 
                #            'sex': 1, 'change': 1557753049, 'confidence': '2.0', 'birth_low': 1852, 
                #            'birth_high': 1852, 'id': 'I0036', 'uuid': '9fdcfc81bd17435e8e051325ac3e6eae', 
                #            'death_low': 1911}>],
                #    [29373, <Node id=30773 labels=frozenset({'Person'}) properties={...}>]
                # ]
                if not node_next:
                    continue
                if "Person" in node_next.labels:
                    obj_next = Person.from_node(node_next)
                    obj_next.label = "Person"
                elif "Family" in node_next.labels:
                    obj_next = FamilyBl.from_node(node_next)
                    obj_next.label = "Family"
                else:
                    print(f'models.gen.media.Media.get_one: unknown type {list(obj_next.labels)}')
                    continue
                if not referee_id in event_refs.keys():
                    # A new Event having indirect referees
                    event_refs[referee_id] = [obj_next]
                else:
                    event_refs[referee_id].append(obj_next)

            # 2. Gather the directly referring objects
            media.ref = []
            for prop, node in referees:
                #Record[1]:
                # [ [{'order': 0},
                #        <Node id=29373 labels=frozenset({'Event'})
                #            properties={'datetype': 4, 'change': 1515865582, 'description': '', 
                #                'id': 'E0858', 'date2': 1999040, 'date1': 1928384, 
                #                'type': 'Burial', 'uuid': '934415b2ccf4476fa9d8d9f4d93938b7'}>
                # ] ]
                if not node:
                    continue
                mref = MediaReferee()
                mref.label, = node.labels   # Get the 1st label
                if mref.label == 'Person':
                    mref.obj = PersonBl.from_node(node)
                    mref.obj.label = "Person"
                elif mref.label == 'Place':
                    mref.obj = PlaceBl.from_node(node)
                    mref.obj.label = "Place"
                elif mref.label == 'Event':
                    mref.obj = EventBl.from_node(node)
                    mref.obj.label = "Event"
                # Has the relation cropping properties?
                left = prop.get('left')
                if left != None:
                    upper = prop.get('upper')
                    right = prop.get('right')
                    lower = prop.get('lower')
                    mref.crop = (left, upper, right, lower)
                # Eventuel next objects for this Event
                mref.next_objs = event_refs.get(mref.obj.uniq_id,[])
#                 # A list [object label, object, relation properties]
#                 media.ref.append([label,obj,crop])
                media.ref.append(mref)
            return media


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
