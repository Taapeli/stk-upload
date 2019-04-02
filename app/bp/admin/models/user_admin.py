'''
Created on 8.3.2019

@author: jm, TimNal
'''

import shareds
import logging
from datetime import datetime
from flask import flash
from flask_security import current_user
from flask_babelex import _
from neo4j.exceptions import ServiceUnavailable, CypherError, ClientError, ConstraintError

from .cypher_adm import Cypher_adm


class UserAdmin():
    '''
    Methods for user information maintaining
    '''

    def __init__(self, user):
        '''
        Constructor
        #TODO: Get better error code?
        #TODO: This class is not for admin user activities but for administering 
               users outside the flash_security scope and for now 
               has classmethods only.
        '''
#        self.username = user.username
#        self.roles = user.roles
        if current_user.has_role('admin'):
                return
        raise ValueError(_("User {} has not admin privileges").format(self.username))

    @classmethod
    def _build_email_from_record(cls, emailRecord):
        ''' Returns an Allowed_email class instance '''
        if emailRecord is None:
            return None
        email = shareds.allowed_email_model(**emailRecord)
#        if emailRecord['creator']:
#            email.creator = emailRecord['creator'] 
        if email.created_at:
            email.created_at = datetime.fromtimestamp(float(email.created_at)/1000) 
        if email.confirmed_at:    
            email.confirmed_at = datetime.fromtimestamp(float(email.confirmed_at)/1000)        
        return email

    @classmethod         
    def _build_user_from_record(self, userRecord):
        ''' Returns a User instance based on a user record '''
        try:
            if userRecord is None:
                return None
            user = shareds.user_model(**userRecord) 
            user.id = user.username
            user.password = ""
            user.roles = [rolenode.name for rolenode in shareds.user_datastore.find_UserRoles(user.email)]
            if user.confirmed_at:
                user.confirmed_at = datetime.fromtimestamp(float(user.confirmed_at)/1000)
            if user.last_login_at:    
                user.last_login_at = datetime.fromtimestamp(float(user.last_login_at)/1000)
            if user.current_login_at:     
                user.current_login_at = datetime.fromtimestamp(float(user.current_login_at)/1000) 
            return user
        except Exception as ex:
            print(ex)  
                 
    @classmethod
    def register_allowed_email(cls, email, role):
        try:
            with shareds.driver.session() as session:
                with session.begin_transaction() as tx:
                    tx.run(Cypher_adm.allowed_email_register, email=email, role=role, admin_name=current_user.username)
                    tx.commit()
        except ConstraintError as ex:
            logging.error('ConstraintError: ', ex.message, ' ', ex.code)            
            flash(_("Given allowed email address already exists"))                            
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
    def confirm_allowed_email(cls, tx, email):
        try:
            for record in tx.run(Cypher_adm.allowed_email_confirm, email=email):
                return(record['email'])
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
                emailRecords = session.read_transaction(cls._getAllowedEmails)
                ret = []
                for record in emailRecords:
                    node = record['email']
                    # <<Node id=105651 labels={'Allowed_email'} 
                    #    properties={'created_at': 1542095367861, 'default_role': 'member', 
                    #        'creator': 'master', 'allowed_email': 'jpek@iki.fi', 
                    #        'confirmed_at': 1544302717575}>
                    ret.append(cls._build_email_from_record(node))
                return ret
#                 if emailRecords is not None:
#                     return [cls._build_email_from_record(emailRecord['email']) for emailRecord in emailRecords] 
#                 return []
        except ServiceUnavailable as ex:
            logging.debug(ex.message)
            return []                 

    @classmethod                                              
    def _getAllowedEmails (cls, tx):
        try:
#             emailRecords = []
#             for record in tx.run(Cypher_adm.allowed_emails_get):
#                 emailRecords.append(record['email'] )
            emailRecords = [record for record in tx.run(Cypher_adm.allowed_emails_get)]    
            return(emailRecords)       
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
                emailRecord = session.read_transaction(cls._findAllowedEmail, email)
                if emailRecord:
                    return cls._build_email_from_record(emailRecord['email']) 
                return None
        except ServiceUnavailable as ex:
            logging.debug(ex.message)
            return None                 

    @classmethod                                              
    def _findAllowedEmail (cls, tx, email):
        try:
#            emailRecord = None
            return(tx.run(Cypher_adm.allowed_email_find, email=email).single())
#             if records:
#                 for record in records:
#                     emailRecord = record['email']
#                     return emailNode        
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
    def user_profile_add(cls, tx, email, username):
#        logging.debug('_put_role ', role)
        try:
            tx.run(Cypher_adm.user_profile_add, email=email, username=username) 
            return
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
    def update_user_language(cls, username, language):
        try:
            result = shareds.driver.session().run(Cypher_adm.user_update_language,
                         username=username,language=language).single()
            return result
        except ServiceUnavailable as ex:
            logging.debug(ex.message)
            return None                 

    @classmethod 
    def update_user(cls, user):
        try:
            with shareds.driver.session() as session:
                updated_user = session.write_transaction(cls._update_user, user)
                if updated_user is None:
                    return None
                return(cls._build_user_from_record(updated_user))

        except ServiceUnavailable as ex:
            logging.debug(ex.message)
            return None                 

    @classmethod                                              
    def _update_user (cls, tx, user):    

        try:
            logging.debug('user update' + user.email + ' ' + user.name)
            if user.username == 'master': 
                user.roles = ['master']
#   Identifier and history fields are not to be updated
            result = tx.run(Cypher_adm.user_update, 
                email = user.email,
 #               username = user.username,
                name = user.name, 
                language = user.language,              
                is_active = user.is_active,
                roles = user.roles)
            if user.username != 'master':
#   Find list of previous user -> role connections
                prev_roles = [rolenode.name for rolenode in shareds.user_datastore.find_UserRoles(user.email)]
#   Delete connections that are not in edited connection list            
                for rolename in prev_roles:
                    if not rolename in user.roles:
                        tx.run(Cypher_adm.user_role_delete,
                               email = user.email,
                               name = rolename) 
#   Add connections that are not in previous connection list                    
                for rolename in user.roles:
                    if not rolename in prev_roles:
                        tx.run(Cypher_adm.user_role_add, 
                               email = user.email,
                               name = rolename)        
          
            logging.info('User with email address {} updated'.format(user.email)) 
            return(result.single()['user'])
        except CypherError as ex:
            logging.error('CypherError', ex)            
            raise ex            
        except ClientError as ex:
            logging.error('ClientError: ', ex)            
            raise
        except Exception as ex:
            logging.error('Exception: ', ex)            
            raise