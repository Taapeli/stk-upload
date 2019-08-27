'''
Created on Jul 3, 2019

@author: kari
'''

import shareds
from models.cypher_gramps import Cypher_batch

def delete_batch(username, batch_id):
    with shareds.driver.session() as session:
        result = session.run(Cypher_batch.batch_delete,
                             username=username, batch_id=batch_id)
        return result
            
def get_filename(username, batch_id):
    with shareds.driver.session() as session:
        result = session.run(Cypher_batch.get_batch_filename,
                             username=username, batch_id=batch_id).single()
        return result.get('b.file')

def get_batches():
    result = shareds.driver.session().run(Cypher_batch.batch_list_all)
    for rec in result:
        print("p",rec.get('b').items())
        yield dict(rec.get('b'))
