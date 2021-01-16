'''
Created on 24.3.2020

@author: jm
'''
import os

import shareds
from .base import NodeObject, Status
from pe.db_reader import DbReader


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


class MediaBl(NodeObject):
    '''
    TODO
    '''
    def __init__(self, params):
        '''
        Constructor
        '''

    @staticmethod
    def create_and_link_by_handles(uniq_id, media_refs):
        ''' Save media object and it's Note and Citation references
            using their Gramps handles.
        '''
        if media_refs:
            ds = shareds.datastore.dataservice
            ds.ds_create_link_medias_w_handles(uniq_id, media_refs)


class MediaReader(DbReader):
    '''
        Data reading class for Event objects with associated data.

        - Use pe.db_reader.DbReader.__init__(self, readservice, u_context) 
          to define the database driver and user context

        - Returns a Result object.
    '''
    def read_my_media_list(self, limit=20):
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
