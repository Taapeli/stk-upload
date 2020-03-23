'''
Created on 23.3.2020

@author: jm
'''
import logging 
logger = logging.getLogger('stkserver')


class DBwriter(object):
    '''
    classdocs
    '''

    def __init__(self, dbdriver):
        ''' Create a writer/updater object with db driver and user context.
        '''
        self.dbdriver = dbdriver
    
        
    def place_set_default_names(self, place, def_names:dict):
        ''' Creates default links from Place to fi and sv PlaceNames.
        
            The objects are referred with database id numbers.

            - place         Place object
            - - .names      PlaceName objects
            - def_names     dict {lang, uid} uniq_id's of PlaceName objects
        '''

        self.dbdriver.place_set_default_names(place.uniq_id, 
                                              def_names['fi'], def_names['sv'])

