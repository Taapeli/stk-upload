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
            