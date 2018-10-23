'''
Created on 23.10.2018

@author: jm
'''
from models.gen.source import Source

class Footnotes():
    ''' A structure for organizing footnotes for source citations '''

    def __init__(self, params):
        '''
        List members are SourceFootnotes
        '''
        fn_list = []
    
    def add(self, obj):
        ''' Adds the obj to Sources list 
        
            1. 
        '''


class SourceFootnote(Source):
    '''
    A structure for creating footnotes for source citations:
    
    '''

    def __init__(self, params):
        '''
        Constructor
        '''
        ref_text = ''       # src
        citations = []      # Citation objects
        repocitory = ''     # Repocitory object

