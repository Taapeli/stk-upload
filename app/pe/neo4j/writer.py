'''
Created on 23.3.2020

@author: jm
'''
import logging 
logger = logging.getLogger('stkserver')

from .place_cypher import CypherPlace

class Neo4jWriteDriver(object):
    '''
    classdocs
    '''

    def __init__(self, dbdriver, tx):
        ''' Create a writer/updater object with db driver and user context.
        '''
        self.dbdriver = dbdriver
        self.tx = tx
    
        
    def place_set_default_names(self, place_id, fi_id, sv_id):
        ''' Creates default links from Place to fi and sv PlaceNames.

            - place_id      Place object id
            - fi_id         PlaceName object id for fi
            - sv_id         PlaceName object id for sv
        '''
#         self.dbdriver.place_set_default_names(place_id, fi_id, sv_id)

        try:
            #def_names = place.find_default_names(place.names, ('fi', 'sv'))
            if fi_id == sv_id:
                result = self.tx.run(CypherPlace.link_name_lang_single, 
                                     place_id=place_id, fi_id=fi_id)
            else:
                result = self.tx.run(CypherPlace.link_name_lang, 
                                     place_id=place_id, 
                                     fi_id=fi_id, sv_id=sv_id)
            x = None
            for x, fi, sv in result:
                print(f"# Linked ({x}:Place)-['fi']->({fi}), -['sv']->({sv})")

            if not x:
                logger.warning("iError Place.find_default_names - not created "
                     f"Place {place_id}, names fi:{fi_id}, sv:{sv_id}")

        except Exception as err:
            logger.error(f"iError Place.find_default_names: {err}")
            return err

