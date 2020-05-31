'''
Created on 22.8.2019

@author: jm
'''
import uuid

class Status():
    """ Status code values for result dictionary.
    
        Result dictionary may have
        - item / items    data
        - status          int code
        - statustext      error message
        etc
        
        example: {"items":events, "status":Status.OK}
    """
    OK = 0
    NOT_FOUND = 1
    ERROR = 2


class NodeObject():
    '''
    Class representing Neo4j node type objects
    '''

    def __init__(self, uniq_id=None):
        '''
        Constructor. 
        
        Optional uniq_id may be uuid identifier (str) or database key (int).
        '''
        self.uuid = None        # UUID
        self.uniq_id = None     # Neo4j object id
        self.change = 0         # Object change time
        self.id = ''            # Gedcom object id like "I1234"
        self.handle = ''       # Gramps handle (?)
        if uniq_id:
            if isinstance(uniq_id, int):
                self.uniq_id = uniq_id
            else:
                self.uuid = uniq_id

    def __str__(self):
        uuid = self.uuid if self.uuid else '-'
        return f'(NodeObject {uuid}/{self.uniq_id}/{self.id} date {self.dates})"'

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
        if node['handle']:
            n.handle = node['handle']
        n.change = node['change']
        return n


    '''
        Compare 
            self.dates <op> other.dates = True?

        See also: models.gen.dates.DateRange.__lt__()

        - None as other.dates is always considered the 1st in order
        - None as self.dates  is always considered last in order
    '''

    def __lt__(self, other):
        if self.dates:
            return self.dates < other.dates
        return True
    def __le__(self, other):
        if self.dates:
            return self.dates <= other.dates
        return True
    def __eq__(self, other):
        if self.dates:
            return self.dates == other.dates
        return False
    def __ge__(self, other):
        if self.dates:
            return self.dates >= other.dates
        return False
    def __gt__(self, other):
        if self.dates:
            return self.dates > other.dates
        return False
    def __ne__(self, other):
        if self.dates:
            return self.dates != other.dates
        return False

    
    @staticmethod       
    def newUuid():
        ''' Generates a new uuid key.
        
            See. https://docs.python.org/3/library/uuid.html
        '''
        return uuid.uuid4().hex
        
    def uuid_short(self):
        ''' Display uuid in short form. '''
        if self.uuid:
            return self.uuid[:6]
        else:
            return ""

    def uuid_str(self):
        ''' Display uuid in short form, or show self.uniq_id is missing. '''
        if self.uuid:
            return self.uuid[:6]
        else:
            return f'({self.uniq_id})'
