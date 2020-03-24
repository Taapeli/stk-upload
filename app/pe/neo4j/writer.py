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
            for x, _fi, _sv in result:
                #print(f"# Linked ({x}:Place)-['fi']->({fi}), -['sv']->({sv})")
                pass

            if not x:
                logger.warning("eo4jWriteDriver.place_set_default_names: not created "
                     f"Place {place_id}, names fi:{fi_id}, sv:{sv_id}")

        except Exception as err:
            logger.error(f"Neo4jWriteDriver.place_set_default_names: {err}")
            return err


    def media_save_w_handles(self, uniq_id:int, media_refs:list):
        ''' Save media object and it's Note and Citation references
            using their Gramps handles.
            
            media_handle:
                media_handle        # Media object handle
                crop              # Four coordinates
                note_handles      # list of Note object handles
                citation_handles  # list of Citation object handles

            TODO: Save Note and Citetion references, too
        '''
        doing = "?"
        try:
            order = 0
            for resu in media_refs:
                doing = f"{uniq_id}->Media {resu.media_handle}"
                r_attr = {'order':order}
                if resu.crop:
                    r_attr['left'] = resu.crop[0]
                    r_attr['upper'] = resu.crop[1]
                    r_attr['right'] = resu.crop[2]
                    r_attr['lower'] = resu.crop[3]
                result = self.tx.run(CypherObjectWHandle.link_media, 
                                     root_id=uniq_id, handle=resu.media_handle, 
                                     r_attr=r_attr)
                media_id = result.single()[0]
                order =+ 1 

                for handle in resu.note_handles:
                    doing = f"{media_id}->Note {handle}"
#                     result = self.tx.run('MATCH (s), (t) WHERE ID(s)=$root_id and t.handle=$handle RETURN s,t', 
#                         root_id=media_id, handle=handle)
#                     for s,t in result: print(f"\nMedia {s}\n"Note {t}")
                    self.tx.run(CypherObjectWHandle.link_note, 
                                root_id=media_id, handle=handle)

                for handle in resu.citation_handles:
                    doing = f"{media_id}->Citation {handle}"
#                     result = self.tx.run('MATCH (s), (t) WHERE ID(s)=$root_id and t.handle=$handle RETURN s,t', 
#                         root_id=media_id, handle=handle)
#                     for s,t in result: print(f"\nMedia {s}\nCite {t}")
                    self.tx.run(CypherObjectWHandle.link_citation, 
                                root_id=media_id, handle=handle)

        except Exception as err:
            logger.error(f"Neo4jWriteDriver.media_save_w_handles {doing}: {err}")


