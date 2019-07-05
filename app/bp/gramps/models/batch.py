'''
Created on Jul 3, 2019

@author: kari
'''

import shareds
from models.cypher_gramps import Cypher_batch

def delete_batch(username, batch_id):
   result = shareds.driver.session().run(Cypher_batch.batch_delete, 
                                      username=username,batch_id=batch_id)
   return result
            
def get_filename(username, batch_id):
   result = shareds.driver.session().run(Cypher_batch.batch_find, batch_id=batch_id).single()
   return result.get('b').get('file')

