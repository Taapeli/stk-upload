'''
Created on 23.3.2020

@author: jm
'''
import logging 
import shareds
from bl.place import PlaceBl
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


    def media_save_w_handles(self, uniq_id, media_refs):
        ''' Save media object and it's Note and Citation references
            using their Gramps handles.
        '''

        if media_refs:
            self.dbdriver.media_save_w_handles(uniq_id, media_refs)

    def mergeplaces(self, id1, id2):
        with shareds.driver.session() as session:
            self.dbdriver.tx = session
            place, names = self.dbdriver.mergeplaces(id1,id2)
            # Select default names for default languages
            def_names = PlaceBl.find_default_names(names, ['fi', 'sv'])
            # Update default language name links
            if def_names:
                self.place_set_default_names(place, def_names)
            return place

