#   Isotammi Geneological Service for combining multiple researchers' results.
#   Created in co-operation with the Genealogical Society of Finland.
#
#   Copyright (C) 2016-2021  Juha Mäkeläinen, Jorma Haapasalo, Kari Kujansuu, 
#                            Timo Nallikari, Pekka Valta
#
#   See the LISENCE file.

'''

    VANHENTUNUT TOTEUTUSMALLI???
    
    Toiminnot pitäisi siirtää pe.neo4j.dataservice.Neo4jWriteDriver -luokkaan
    
Created on 23.3.2020

@author: jm
'''
import logging 
logger = logging.getLogger('stkserver')
import shareds

from bl.base import Status
#from bl.person import PersonBl
from bl.place import PlaceBl
from pe.db_reader import DbReader


class DbWriter(DbReader):
    '''
    Services to write business objects using transaction.

    Enables transaction processing and offer services for accessing database.
    
    The __init__ dbdriver argument defines, which database is used.
    
    Transaction processing, see:
    https://neo4j.com/docs/api/python-driver/current/api.html#explicit-transactions
    
    '''

#     def __init__(self, dbdriver):
#         ''' Create a database write driver object and start a transaction.
#         '''
#         self.dbdriver = dbdriver
#         self.dbdriver.dw
        

#     def create_batch(self, obj):
#         ''' Start transaction for writing.
#         
#             - obj    Batch object
#         '''
#         from bl.batch import Batch
#         
#         if not isinstance(obj, Batch):
#             raise TypeError(f'pe.db_writer.DbWriter.create_batch: invalid argument')
#         attr = {
#             "id": obj.id,
#             "user": obj.user,
#             "file": obj.file,
#             "mediapath": obj.mediapath,
#             #timestamp": <to be set in cypher>,
#             #id: <uniq_id from result>,
#             "status": obj.status
#         }
#         res = self.dbdriver.dw_batch_save(obj)
#         return res


    def commit(self, rollback=False):
        """ Commit or rollback transaction.
        
            Returns 0 or error message, if commit failed.
        """
        if rollback:
            self.dbdriver.ds_rollback()
            print("Transaction discarded")
            logger.info(f'-> bp.gramps.xml_dom_handler.DOM_handler.ds_commit/rollback f="{self.file}"')
            self.blog.log_event({'title': _("Database save failed"), 'level':"ERROR"})
            return 0

            try:
                return self.dbdriver.ds_commit()
                logger.info(f'-> bp.gramps.xml_dom_handler.DOM_handler.commit/ok f="{self.file}"')
                print("Transaction committed")
                return 0
            except Exception as e:
                msg = f'{e.__class__.__name__}, {e}'
                logger.info('-> bp.gramps.xml_dom_handler.DOM_handler.ds_commit/fail"')
                print("pe.db_writer.DbWriter.commit: Transaction failed "+ msg)
                self.blog.log_event({'title':_("Database save failed due to {}".\
                                     format(msg)), 'level':"ERROR"})
                return True

#     def save_and_link_obj(self, obj, **kwargs):   # batch_id=None, parent_id=None):
#         """ Saves given object to database
#             - if  obj.parent_id is given, link (parent) --> (obj)  
#             - elif obj.batch_id is given, link (batch) --> (obj)
#         """
#         obj.save(**kwargs)


#     def place_set_default_names(self, place, def_names:dict):
#         ''' Creates default links from Place to fi and sv PlaceNames.
#         
#             The objects are referred with database id numbers.
# 
#             - place         Place object
#             - - .names      PlaceName objects
#             - def_names     dict {lang, uid} uniq_id's of PlaceName objects
#         '''
# 
#         self.dbdriver.dw_place_set_default_names(place.uniq_id, 
#                                                  def_names['fi'], def_names['sv'])


#     def media_save_w_handles(self, uniq_id, media_refs):
#         ''' Save media object and it's Note and Citation references
#             using their Gramps handles.
#         '''
#         if media_refs:
#             self.dbdriver.dw_media_save_w_handles(uniq_id, media_refs)


#     def mergeplaces(self, id1, id2): #-> pe.neo4j.dataservice.Neo4jDataService.dw_mergeplaces
#         with shareds.driver.session() as session:
#             self.dbdriver.tx = session
#             place, names = self.dbdriver.dw_mergeplaces(id1,id2)
#             # Select default names for default languages
#             def_names = PlaceBl.find_default_names(names, ['fi', 'sv'])
#             # Update default language name links
#             if def_names:
#                 self.place_set_default_names(place, def_names)
#             return place

#     def update_person_confidences(self, tx, person_ids:list): #-> bl.person.PersonBl.update_person_confidences
#         """ Sets a quality rate for given list of Person.uniq_ids.
