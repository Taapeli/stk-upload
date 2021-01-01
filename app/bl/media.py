'''
Created on 24.3.2020

@author: jm
'''
import shareds
from .base import NodeObject

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
            ds._create_link_medias_w_handles(uniq_id, media_refs)


class MediaRefResult():
    ''' Gramps media reference result object.
    
        Includes Note and Citation references and crop data
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

