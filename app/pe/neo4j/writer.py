'''
Created on 23.3.2020

@author: jm
'''
import logging 
logger = logging.getLogger('stkserver')

from .place_cypher import CypherPlace
from .gramps_cypher import CypherObjectWHandle


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
        try:
            if fi_id == sv_id:
                result = self.tx.run(CypherPlace.link_name_lang_single, 
                                     place_id=place_id, fi_id=fi_id)
            else:
                result = self.tx.run(CypherPlace.link_name_lang, 
                                     place_id=place_id, fi_id=fi_id, sv_id=sv_id)
            x = None
            for x, fi, sv in result:
                print(f"# Linked ({x}:Place)-['fi']->({fi}), -['sv']->({sv})")

            if not x:
                logger.warning("eo4jWriteDriver.place_set_default_names: not created "
                     f"Place {place_id}, names fi:{fi_id}, sv:{sv_id}")

        except Exception as err:
            logger.error(f"Neo4jWriteDriver.place_set_default_names: {err}")
            return err


    def media_save_w_handles(self, uniq_id:int, media_refs:list):
        ''' Save media object and it's Note and Citation references
            using their Gramps handles.
            
            TODO: Save Note and Citetion references, too
        '''
#         media_href = media_refs.media_href
#         crop = media_refs.crop                          # Four coordinates
#         note_handles = media_refs.note_handles          # list of note handles
#         citation_handles = media_refs.citation_handles  # list of citation handles
# 
#         self.dbdriver.media_save_w_handles(root_handle, media_href, crop, 
#                                            note_handles, citation_handles)
        try:
            order = 0
            for resu in media_refs:
                r_attr = {'order':order}
                if resu.crop:
                    r_attr['left'] = resu.crop[0]
                    r_attr['upper'] = resu.crop[1]
                    r_attr['right'] = resu.crop[2]
                    r_attr['lower'] = resu.crop[3]
                self.tx.run(CypherObjectWHandle.link_media, 
                            root_id=uniq_id, m_handle=resu.handle, 
                            r_attr=r_attr)
                order = +1 # Make relation to the Media nodes

        except Exception as err:
            logger.error(f"Neo4jWriteDriver.media_save_w_handles: {err}")


