'''
Created on 22.8.2019

@author: jm
'''
import uuid

class NodeObject():
    '''
    Class representing Neo4j node type objects
    '''


    def __init__(self, uniq_id=None):
        '''
        Constructor
        '''
        self.uniq_id = uniq_id
        self.handle = ''
        self.change = 0
        self.id = ''

    @classmethod
    def from_node(cls, node):
        '''
        Starts Transforming a db node to an undefined type object.
        Call from an inherited class, f.ex. n = Media.from_node(node)
        
        '''
        n = cls()
        n.uniq_id = node.id
        n.id = node['id']
        n.uuid = node['uuid']
        n.handle = node['handle']
        n.change = node['change']
        return n
    
    
    def newUuid(self):
        ''' Generates a new uuid key.
        
            See. https://docs.python.org/3/library/uuid.html
        '''
        return uuid.uuid4().hex
