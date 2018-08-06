'''
Created on 2.3.2018

@author: jm
'''
import shareds
import logging

class DataAdmin():
    '''
    Methods for database maintain
    '''


    def __init__(self, user):
        '''
        Constructor
        #TODO: Get better error code?
        '''
        self.username = user.username
        self.roles = user.roles
        if user.has_role('admin'):
                return
        raise ValueError("User {} has not admin privileges".format(self.username))


    def db_reset(self, opt=None):
        if opt == "total":
            """ Koko kanta tyhjennetään """
            msg = "All data is deleted. "
            logging.info(msg)
            result = shareds.driver.session().run(Cypher_adm.remove_all_nodes)
        elif opt == "save_users":
            msg = "All data but users and roles are removed."
            logging.info(msg)
            result = shareds.driver.session().run(Cypher_adm.remove_data_nodes)
        elif opt == "my_own":
            msg = "All persons and event by {} are removed. ".format(self.username)
            logging.info(msg)
            result = shareds.driver.session().run(Cypher_adm.remove_my_nodes, 
                                                  user=self.username)
            
        counters = result.consume().counters
        msg2 = "Poistettu {} solmua, {} relaatiota".\
              format(counters.nodes_deleted, counters.relationships_deleted)
        logging.info(msg2)
        return '\n'.join((msg, msg2))


class Cypher_adm():
    ' Cypher clauses for admin purposes'
    
    remove_all_nodes = """
MATCH (a) DETACH DELETE a
"""
    remove_data_nodes = """
match (a) 
where not ( 'UserProfile' IN labels(a)
    or 'User' IN labels(a)
    or 'Role' IN labels(a) )
detach delete a"""
    remove_my_nodes = """
match (a)<-[r:REVISION]-(u:UserProfile {userName:$user})
detach delete a"""
