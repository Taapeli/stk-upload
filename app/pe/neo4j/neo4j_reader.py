'''
Created on 14.3.2020

@author: jm
'''
import shareds
from .place_cypher import CypherPlace

class DbReader():
    '''
    Place data access.
    '''

    def __init__(self, u_context):
        '''
        Constructor stores context
        '''
        self.context = u_context


    def place_list(self):
        ''' Read place list from given start point
        '''
        fw = self.context.next_name_fw()
        with shareds.driver.session() as session: 
            if self.context.use_common(): 
                #1 get approved common data
                print("Neo4jReader.DbReader.place_list: by owner with common")
                result = session.run(CypherPlace.get_common_name_hierarchies,
                                     user=self.context.user, fw=fw, 
                                     limit=self.context.count)
            else: 
                #2 get my own (no owner name needed)
                print("Neo4jReader.DbReader.place_list: by owner only")
                result = session.run(CypherPlace.get_my_name_hierarchies,
                                     user=self.context.user, fw=fw, 
                                     limit=self.context.count)
        return result
