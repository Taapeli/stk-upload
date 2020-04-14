'''
    Archive, Repository, Source and Citation classes

Created on 2.5.2017 from Ged-prepare/Bus/classes/genealogy.py

@author: Jorma Haapasalo <jorma.haapasalo@pp.inet.fi>
'''

#from sys import stderr
#import shareds
from bl.base import NodeObject


class SourceDb(NodeObject):
    """ Lähde
            
        Properties:
                handle          
                change
                id              esim. "S0001"
                stitle          str lähteen otsikko
        
        See also: bp.gramps.models.source_gramps.Source_gramps
     """

    def __init__(self):
        """ Luo uuden source-instanssin """
        NodeObject.__init__(self)
        self.stitle = ''
        self.sauthor = ''
        self.spubinfo = ''
        self.note_ref = []      # uniq_ids (previously note[])

        # For display combo
        #Todo: onko repositories, citations käytössä?
        self.repositories = []
        self.citations = []
        self.notes = []

    def __str__(self):
        return "{} '{}' '{}' '{}'".format(self.id, self.stitle, self.sauthor, self.spubinfo)


    @classmethod
    def from_node(cls, node):
        '''
        Transforms a db node to an object of type Source.
        
        <Node id=91394 labels={'Source'} 
            properties={'handle': '_d9edc4e4a9a6defc258', 'id': 'S0078', 
                'stitle': 'Kangasala syntyneet 1721-1778', 'change': '1507149115'}>
        '''
        NodeObject.from_node(node)
        s = cls()   # create a new Source
        s.uniq_id = node.id
        s.id = node['id']
        s.uuid = node['uuid']
        if 'handle' in node:
            s.handle = node['handle']
        s.stitle = node['stitle']
        s.sauthor = node['sauthor']
        s.spubinfo = node['spubinfo']
        s.change = node['change']
        return s
