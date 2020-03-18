'''
Created on 14.3.2020

@author: jm
'''
# import shareds
# from .place_cypher import CypherPlace

class DbReader():
    '''
    Place data access.
    '''

    def __init__(self, u_context):
        '''
        Constructor stores context
        '''
        self.context = u_context

