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
from datetime import datetime
from flask_security import current_user
from neo4j.exceptions import ServiceUnavailable, CypherError, ClientError


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
    

class UserAdmin():
    '''
    Methods for user information maintaining
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

    @classmethod
    def _build_email_from_node(cls, emailNode):
        ''' Returns an AllowedEmail class instance '''
        if emailNode is None:
            return None
        email = shareds.allowed_email_model(**emailNode.properties)
        email.allowed_email = emailNode.properties['allowed_email']
        email.default_role = emailNode.properties['default_role']
        email.creator = emailNode.properties['creator']
        email.created_at = datetime.fromtimestamp(emailNode.properties['created_at']/1000)
        if 'registered_at' in emailNode.properties:
            email.registered_at = datetime.fromtimestamp(emailNode.properties['registered_at']/1000)        
       
        return email
    
    @classmethod
    def allowed_email_register(self, email, role):
        try:
            with shareds.driver.session() as session:
                with session.begin_transaction() as tx:
                    tx.run(Cypher_adm.allowed_email_register, email=email, role=role, admin_name=current_user.name)
                    tx.commit()
        except CypherError as ex:
            logging.error('CypherError: ', ex.message, ' ', ex.code)            
            raise      
        except ClientError as ex:
            logging.error('ClientError: ', ex.message, ' ', ex.code)            
            raise
        except Exception as ex:
            logging.error('Exception: ', ex)            
            raise

    @classmethod   
    def get_allowed_emails(cls):
        try:
            with shareds.driver.session() as session:
                emailNodes = session.read_transaction(cls._getAllowedEmails)
                if emailNodes is not None:
                    return [cls._build_email_from_node(emailNode) for emailNode in emailNodes] 
                return []
        except ServiceUnavailable as ex:
            logging.debug(ex.message)
            return []                 

    @classmethod                                              
    def _getAllowedEmails (cls, tx):
        try:
            emailNodes = []
            for record in tx.run(Cypher_adm.get_allowed_emails):
                emailNodes.append(record['email'])
            return emailNodes        
        except CypherError as ex:
            logging.error('CypherError: ', ex.message, ' ', ex.code)            
            raise      
        except ClientError as ex:
            logging.error('ClientError: ', ex.message, ' ', ex.code)            
            raise
        except Exception as ex:
            logging.error('Exception: ', ex)            
            raise
        
    @classmethod 
    def find_allowed_email(cls, email):
        try:
            with shareds.driver.session() as session:
                emailNode = session.read_transaction(cls._findAllowedEmail, email)
                if emailNode is not None:
                    return cls._build_email_from_node(emailNode) 
                return None
        except ServiceUnavailable as ex:
            logging.debug(ex.message)
            return None                 

    @classmethod                                              
    def _findAllowedEmail (self, tx, email):
        try:
            emailNode = None
            records = tx.run(Cypher_adm.allowed_email_find, email=email)
            if records:
                for record in records:
                    emailNode = record['email']
                    return emailNode        
        except CypherError as ex:
            logging.error('CypherError: ', ex.message, ' ', ex.code)            
            raise      
        except ClientError as ex:
            logging.error('ClientError: ', ex.message, ' ', ex.code)            
            raise
        except Exception as ex:
            logging.error('Exception: ', ex)            
            raise


class Cypher_adm():
    ' Cypher clauses for admin purposes'
    
    remove_all_nodes = """
MATCH (a) DETACH DELETE a
"""

    remove_data_nodes = """
MATCH (a) 
where not ( 'UserProfile' IN labels(a)
    OR 'User' IN labels(a)
    OR 'Role' IN labels(a) )
DETACH DELETE a
"""

    remove_my_nodes = """
MATCH (a)<-[r:REVISION]-(u:UserProfile {userName:$user})
DETACH DELETE a
"""

    allowed_email_register = """
CREATE email:Allowed_email {
    allowed_email: $email,
    default_role: $role,
    admin_name: $admin_name,
    timestamp: timestamp() }
"""
    
    get_allowed_emails = """
MATCH (email:Allowed_email)
RETURN DISTINCT email 
    ORDER BY email.timestamp DESC
"""    
    
    allowed_email_find = """
MATCH (email:Allowed_email)
    WHERE email.allowed_email = $email
RETURN email
"""