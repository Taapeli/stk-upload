'''
Created on 24.3.2020

@author: jm
'''
import os

#import shareds
from .base import NodeObject, Status
from bl.person import PersonBl
from bl.family import FamilyBl
from bl.place import PlaceBl
from bl.event import EventBl

from pe.db_reader import DbReader
from pe.neo4j.cypher.cy_media import CypherMedia


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


class MediaBl(Media):
    '''
    Media file object for pictures and documents.
    '''
    def __init__(self):
        '''
        Constructor
        '''
        self.description = ""
        self.src = None
        self.mime = None
        self.name = ""


    def save(self, tx, **kwargs):   # batch_id=None):
        """ Saves this new Media object to db.
        
            #TODO: Process also Notes for media?
            #TODO: Use MediaWriteService
        """
        if not 'batch_id' in kwargs:
            raise RuntimeError(f"Media.save needs batch_id for parent {self.id}")

        self.uuid = self.newUuid()
        m_attr = {}
        try:
            m_attr = {
                "handle": self.handle,
                "change": self.change,
                "id": self.id,
                "src": self.src,
                "mime": self.mime,
                "name": self.name,
                "description": self.description
            }
            m_attr['batch_id'] = kwargs['batch_id']
            result = tx.run(CypherMedia.create_in_batch, 
                            bid=kwargs['batch_id'], uuid=self.uuid, m_attr=m_attr)
            self.uniq_id = result.single()[0]
        except Exception as e:
            print(f"MediaBl.save: {e.__class__.__name__} {e}, id={self.id}")
            raise RuntimeError(f"Could not save Media {self.id}")
        return


class MediaReader(DbReader):
    '''
        Data reading class for Event objects with associated data.

        - Use pe.db_reader.DbReader.__init__(self, readservice, u_context) 
          to define the database driver and user context

        - Returns a Result object.
    '''
    def read_my_media_list(self):
        """ Read Media object list using u_context.
        """
        medias = []
        fw = self.user_context.first     # next name
        user = self.user_context.batch_user()
        limit = self.user_context.count
        ustr = "for user " + user if user else "approved "
        print(f"MediaReader.read_my_media_list: Get max {limit} medias {ustr}starting {fw!r}")

        res = self.readservice.dr_get_media_list(self.use_user, fw, limit)
        #res = Media.get_medias(uniq_id=None, o_context=self.user_context, limit=limit)
        if Status.has_failed(res): return res
        for record in res.get('recs', None): 
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
            self.user_context.update_session_scope('media_scope', 
                medias[0].description, medias[-1].description, limit, len(medias))
            return {'status':Status.OK, 'items':medias}
        return {'status':Status.NOT_FOUND}


    def get_one(self, oid):
        """ Read a Media object, selected by UUID or uniq_id.
        """
        class MediaReferrer():
            ''' Carrier for a referee of media object. '''
            def __init__(self):
                # Referencing object, label, cropping
                self.obj = None
                self.label = None
                self.crop = None
                # If the referring obj is Event, there is a list of connected objects
                self.next_objs = []
            def __str__(self):
                s = ''
                if self.obj:
                    if self.next_objs:
                        s = ' '.join([x.id for x in self.next_objs]) + '-> '
                    s += f' {self.label} {self.obj.id} -{self.crop}-> (Media)'
                return s

        # Example database items: 
        #    MATCH (media:Media) <-[r:MEDIA]- (ref) <-[:EVENT]- (ref2)
        #  media     r (crop)             ref                           ref2
        # (media) <-[crop()]-            (Person 'I0026' id=21532) <-- (None)
        # (media) <-[crop(47,67,21,91)]- (Person 'I0026' id=21532) <-- (None)
        # (media) <-[crop(20,47,22,53)]- (Person 'I0029' id=21535) <-- (None)
        # (media) <-[crop()]-   (Event  'E9999' id=99999) <-- (Person 'I9999' id=999)
    
        user = self.user_context.batch_user()
        res = self.readservice.dr_get_media_single(user, oid)
        # returns {status, items}
        if Status.has_failed(res): return res

        media = None
        #media_refs = []     # The nodes pointing to this Media
        event_refs = {}     # The Person or Family nodes behind referencing Event
        items = res.get('items')
        for media_node, crop, ref_node, ref2_node in items:
            # - Media node
            # - cropping
            # - referring Person, Family or Event
            # - optional Person or Family behind the referring Event

            if not media:
                media = Media.from_node(media_node)
                media.ref = []

            #   The referring object

            mref = MediaReferrer()
            #mref.next_objs = []
            mref.label, = ref_node.labels   # Get the 1st label
            if mref.label == 'Person':
                mref.obj = PersonBl.from_node(ref_node)
            elif mref.label == 'Place':
                mref.obj = PlaceBl.from_node(ref_node)
            elif mref.label == 'Event':
                mref.obj = EventBl.from_node(ref_node)
            mref.obj.label = mref.label
            media.ref.append(mref)

            # Has the relation cropping properties?
            left = crop.get('left')
            if not left is None:
                upper = crop.get('upper')
                right = crop.get('right')
                lower = crop.get('lower')
                mref.crop = (left, upper, right, lower)

            #    The next object behind the Event

            if ref2_node:
                if ref2_node.id in event_refs:
                    obj2 = event_refs[ref2_node.id]
                else:
                    if "Person" in ref2_node.labels:
                        obj2 = PersonBl.from_node(ref2_node)
                        obj2.label = "Person"
                    elif "Family" in ref2_node.labels:
                        obj2 = FamilyBl.from_node(ref2_node)
                        obj2.label = "Family"
                    else:
                        raise TypeError(f'MediaReader.get_one: unknown type {list(ref2_node.labels)}')
                    event_refs[obj2.uniq_id] = obj2

                mref.next_objs.append(obj2)

        return {'item':media, 'status':Status.OK}


class MediaWriter:
    def __init__(self, writeservice, u_context=None):
        '''
        :param: writeservice    Neo4jDataService
        :param: u_context       #TODO Use user information from here
        '''
        self.writeservice = writeservice
        self.u_context = u_context

    def create_and_link_by_handles(self, uniq_id, media_refs):
        ''' Save media object and it's Note and Citation references
            using their Gramps handles.
        '''
        if media_refs:
            #ds = shareds.datastore.dataservice
            self.writeservice.ds_create_link_medias_w_handles(uniq_id, media_refs)



class MediaRefResult():
    ''' Gramps media reference result object.
    
        Includes Note and Citation references and crop data.
        Used in bp.gramps.xml_dom_handler.DOM_handler
    '''
    def __init__(self):
        self.media_handle = None
        self.media_order = 0        # Media reference order nr
        self.crop = []              # Four coordinates
        self.note_handles = []      # list of note handles
        self.citation_handles = []  # list of citation handles

    def __str__(self):
        s = f'{self.media_handle} [{self.media_order}]'
        if self.crop: s += f' crop({self.crop})'
        if self.note_handles: s += f' notes({self.note_handles})'
        if self.citation_handles: s += f' citations({self.citation_handles})'
        return s
