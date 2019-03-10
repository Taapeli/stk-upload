'''
Created on 2.3.2018

@author: jm

    Administrator model methods

    stk_upload/
        admin/
            templates/
                admin/
                    index.html
            __init__.py
            form.py
            models.py
            routes.py
'''
import shareds
import logging
from flask_babelex import _

from .cypher_adm import Cypher_adm


class DataAdmin():
    '''
    Methods for database maintaining
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
        raise ValueError(_("User {} has not admin privileges").format(self.username))


    def db_reset(self, opt=None):
        if opt == "total":
            """ Koko kanta tyhjennetään """
            msg = _("All data is deleted. ")
            logging.info(msg)
            result = shareds.driver.session().run(Cypher_adm.remove_all_nodes)
        elif opt == "save_users":
            msg = _("All data but users and roles are removed.")
            logging.info(msg)
            result = shareds.driver.session().run(Cypher_adm.remove_data_nodes)
        elif opt == "my_own":
            #return "NOT COMPLETED! Todo: Can not remove user's data nodes"
            msg = _(f"All persons and event by {self.username} are removed. ")
            logging.info(msg)
            result = shareds.driver.session().run(Cypher_adm.remove_my_nodes, 
                                                  user=self.username)
            
        counters = result.consume().counters
        msg2 = "Poistettu {} solmua, {} relaatiota".\
              format(counters.nodes_deleted, counters.relationships_deleted)
        logging.info(msg2)
        return '\n'.join((msg, msg2))

        