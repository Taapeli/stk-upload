# coding: utf-8 
'''
Created on 28.9.2017

@author: TimNal
'''

from flask_security import current_user
from flask_security.datastore import UserDatastore
from .seccypher import Cypher  
from neo4j.exceptions import ServiceUnavailable, CypherError, ClientError
import datetime
#import shareds
import logging
#from wtforms.validators import ValidationError
logger = logging.getLogger('neo4juserdatastore')

driver = None

class Neo4jUserDatastore(UserDatastore):
    """ User info database """

    # Uses classes Role, User, UserProfile, AllowedEmail from setups.py

    def __init__(self, driver, user_model, user_profile_model, role_model, allowed_email_model):
        self.driver = driver
        self.user_model = user_model
        self.user_profile_model = user_profile_model
        self.allowed_email_model = allowed_email_model        
        self.role_model = role_model
        self.role_dict = self.get_roles() 
        
    def _build_user_from_node(self, userNode):
        ''' Returns a list of Role class instances '''
        if userNode is None:
            return None
        user = self.user_model(**userNode.properties)
        user.id = str(userNode.id)
        user.roles = self.find_UserRoles(user.email)
        if 'confirmed_at' in userNode.properties: 
            user.confirmed_at = datetime.datetime.fromtimestamp(float(userNode.properties['confirmed_at']))
        if 'last_login_at' in userNode.properties: 
            user.last_login_at = datetime.datetime.fromtimestamp(float(userNode.properties['last_login_at']))
        if 'current_login_at' in userNode.properties: 
            user.current_login_at = datetime.datetime.fromtimestamp(float(userNode.properties['current_login_at']))                            
        return user
 
#  
#     def email_accepted(self, proposed_email):
#         return proposed_email == self.find_allowed_email(proposed_email)
#                               
        
    def put(self, model):
        with self.driver.session() as session:
            try:
                if isinstance(model, self.user_model):
                    if not model.id: 
                        return session.write_transaction(self._put_user, model)
                    else:
                        return session.write_transaction(self._update_user, model)                                         
                elif isinstance(model, self.role_model):
                    return session.write_transaction(self._put_role, model)
            except ServiceUnavailable as ex:
                logger.error(ex)            
                return None
            except Exception as ex:
                logger.error(ex)            
                raise
            
    def _put_user (self, tx, user):    # ============ New user ==============

        allowed_email = self.find_allowed_email(user.email)
        if allowed_email == None:
            return(None)
#            raise(ValidationError("Email address not accepted"))
        if len(user.roles) == 0:
            user.roles = [allowed_email.default_role]     
        user.confirmed_at = None
        user.is_active = True
        try:
            logger.debug('_put_user new', user.email, ' ', user.name, ' ', user.roles[0])                
            result = tx.run(Cypher.user_register,
                email = user.email,
                password = user.password, 
                is_active = user.is_active,
#                     confirmed_at = user.confirmed_at,            
                roles = user.roles,
                username = user.username,
                name = user.name,
                language = user.language,
                last_login_at = user.last_login_at,
                current_login_at = user.current_login_at,
                last_login_ip = user.last_login_ip,
                current_login_ip = user.current_login_ip,
                login_count = user.login_count )

            for record in result:
                userNode = (record['user'])
                logger.debug(userNode)
                self._user_profile_add(tx, userNode.id, userNode.properties['username'])
                tx.commit()
                return self._build_user_from_node(userNode)
#            tx.commit()
        except CypherError as ex:
            logger.error('CypherError: ', ex.message, ' ', ex.code)            
            raise      
        except ClientError as ex:
            logger.error('ClientError: ', ex.message, ' ', ex.code)            
            raise
        except Exception as ex:
            logger.error('Exception: ', ex)            
            raise

    def _update_user (self, tx, user):
            # Update user
            rolelist = []
            for role in user.roles:
                roleToAdd = (role.name if isinstance(role, self.role_model) else role)
                if not roleToAdd in rolelist:
                    rolelist.append(roleToAdd)
            try:
                logger.debug('_put_user update' + user.email + ' ' + user.name)
                confirmtime = None 
                if user.confirmed_at == None:
                    confirmtime = datetime.datetime.now()
                else:     
                    confirmtime = user.confirmed_at                                    
                result = tx.run(Cypher.user_update, 
                    id=int(user.id), 
                    email=user.email,
                    password=user.password, 
                    is_active=user.is_active,
                    confirmed_at = confirmtime.timestamp(),            
                    roles=rolelist,
                    username = user.username,
                    name = user.name,
                    language = user.language, 
                    last_login_at = user.last_login_at.timestamp(),
                    current_login_at = user.current_login_at.timestamp(),
                    last_login_ip = user.last_login_ip,
                    current_login_ip = user.current_login_ip,
                    login_count = user.login_count )

                for record in result:
                    userNode = (record['user'])
                    return self._build_user_from_node(userNode)
            except CypherError as ex:
                logger.error('CypherError', ex)            
                raise ex            
            except ClientError as ex:
                logger.error('ClientError: ', ex)            
                raise
            except Exception as ex:
                logger.error('Exception: ', ex)            
                raise
            
#        tx.commit()            
#        return user     

    def _put_role (self, tx, role):
#        logger.debug('_put_role ', role)
        try:
            roleNode = tx.run(Cypher.role_register, 
                              level = role.level, 
                              name=role.name, 
                              description=role.description,
                              timestamp = datetime.datetime.timestamp())
            return self.role_model(**roleNode.properties)
        except CypherError as ex:
            logger.error('CypherError: ', ex.message, ' ', ex.code)            
            raise      
        except ClientError as ex:
            logger.error('ClientError: ', ex.message, ' ', ex.code)            
            raise
        except Exception as ex:
            logger.error('Exception: ', ex)            
            raise 
  
     
    def _user_profile_add (self, tx, uid, username):
#        logger.debug('_put_role ', role)
        try:
            tx.run(Cypher.user_profile_add, uid=uid, username=username) 
            return
        except CypherError as ex:
            logger.error('CypherError: ', ex.message, ' ', ex.code)            
            raise      
        except ClientError as ex:
            logger.error('ClientError: ', ex.message, ' ', ex.code)            
            raise
        except Exception as ex:
            logger.error('Exception: ', ex)            
            raise


    def commit(self):
        pass
#        self.tx.commit()
 
    
    def get_user(self, id_or_email):
#        self.email = id_or_email
        try:
            with self.driver.session() as session:
                userNode = session.read_transaction(self._getUser, id_or_email) 
                logger.debug ('get_user ', id_or_email, ' ', userNode)
                return(self._build_user_from_node(userNode))
        except ServiceUnavailable as ex:
            logger.debug(ex.message)
            return None
 
                        
    def _getUser (self, tx, pemail):
            try:
                for record in tx.run(Cypher.email_or_id_find, id_or_email=pemail):            
                    userNode = (record['user'])
                    return userNode
            except CypherError as ex:
                logger.error('CypherError: ', ex.message, ' ', ex.code)            
                raise      
            except ClientError as ex:
                logger.error('ClientError: ', ex.message, ' ', ex.code)            
                raise
            except Exception as ex:
                logger.error('Exception: ', ex)            
                raise
 
        
    def get_users(self):
        try:
            with self.driver.session() as session:
                userNodes = session.read_transaction(self._getUsers)
                if userNodes is not None:
                    return [self.user_model(**userNode.properties) for userNode in userNodes] 
                return []
        except ServiceUnavailable as ex:
            logger.debug(ex.message)
            return []                 

                                               
    def _getUsers (self, tx):
        try:
            userNodes = []
            for record in tx.run(Cypher.get_users):
                userNodes.append(record['user'])
            return userNodes        
        except CypherError as ex:
            logger.error('CypherError: ', ex.message, ' ', ex.code)            
            raise      
        except ClientError as ex:
            logger.error('ClientError: ', ex.message, ' ', ex.code)            
            raise
        except Exception as ex:
            logger.error('Exception: ', ex)            
            raise
   
                
    def find_user(self, *args, **kwargs):
#        print('find_user ', args, ' ', kwargs)
        try:
            with self.driver.session() as session:
                userNode = session.read_transaction(self._findUser, kwargs['id']) 
#                print('find_user (node) ', userNode)
                return(self._build_user_from_node(userNode))
        except ServiceUnavailable as ex:
            logger.debug(ex.message)
            return None
        
    def _findUser (self, tx, arg):
        try:
            rid = int(arg)
#            print('rid=', rid)
            for record in tx.run(Cypher.id_find, id=rid):
                user = (record['user'])
                return user        
        except CypherError as ex:
            logger.error('CypherError: ', ex.message, ' ', ex.code)            
            raise      
        except ClientError as ex:
            logger.error('ClientError: ', ex.message, ' ', ex.code)            
            raise
        except Exception as ex:
            logger.error('Exception: ', ex)            

            raise

    def find_UserRoles(self, email):
        try:
            with self.driver.session() as session:
                userRoles = session.read_transaction(self._findUserRoles, email) 
                if len(userRoles) > 0:
                    return [self.role_model(**roleNode.properties) for roleNode in userRoles] 
                return None
        except ServiceUnavailable as ex:
            logger.debug(ex.message)
            raise
            
    def _findUserRoles (self, tx, pemail):
        try:
            roles = []
            for record in tx.run(Cypher.user_roles_find, email=pemail):
                roles.append(record['role'])
    #        print ('_findUserRoles ', pemail, roles)    
            return roles
        except CypherError as ex:
            logger.error('CypherError: ', ex.message, ' ', ex.code)            
            raise      
        except ClientError as ex:
            logger.error('ClientError: ', ex.message, ' ', ex.code)            
            raise
        except Exception as ex:
            logger.error('Exception: ', ex)            
            raise
 
        
    def find_role(self, roleName):
        try:
            with self.driver.session() as session:
                roleNode = session.read_transaction(self._findRole, roleName) 
                if roleNode is not None:
                    role =  self.role_model(**roleNode.properties)
                    role.id = str(roleNode.id)
                    return role
                return None
        except ServiceUnavailable as ex:
            logger.debug(ex.message)
            return None
        
    def _findRole (self, tx, roleName):
        try:
            for record in tx.run(Cypher.role_find, name=roleName):
                return (record['role'])                
        except CypherError as ex:
            logger.error('CypherError: ', ex.message, ' ', ex.code)            
            raise      
        except ClientError as ex:
            logger.error('ClientError: ', ex.message, ' ', ex.code)            
            raise
        except Exception as ex:
            logger.error('Exception: ', ex)            
            raise   
   
                                  
    def get_role(self, rid):
        self.id = rid
        try:
            with self.driver.session() as session:
                roleNode = session.read_transaction(self._getRole, id) 
#                print ('get_role ', rid, ' ', roleNode)
                if roleNode is not None:
                    role =  self.role_model(**roleNode.properties)
                    role.id = str(roleNode.id)
                    return role
                return None
        except ServiceUnavailable as ex:
            logger.debug(ex.message)
            return None
                        
    def _getRole (self, tx, rid):
        try:
            for record in tx.run(Cypher.role_get, id=rid):
                return (record['role'])        
        except CypherError as ex:
            logger.error('CypherError: ', ex.message, ' ', ex.code)            
            raise      
        except ClientError as ex:
            logger.error('ClientError: ', ex.message, ' ', ex.code)            
            raise
        except Exception as ex:
            logger.error('Exception: ', ex)            
            raise


    def get_roles(self):
        try:
            with self.driver.session() as session:
                roles = {}
                roleNodes = session.read_transaction(self._getRoles) 
#                print ('get_role ', rid, ' ', roleNode)
                if roleNodes is not None:
                    for roleNode in roleNodes:
                        role =  self.role_model(**roleNode.properties)
                        role.id = str(roleNode.id)
                        roles[role.name]=role
                    return roles
                return None
        except ServiceUnavailable as ex:
            logger.debug(ex.message)
            raise
                                
    def _getRoles (self, tx):
        try:
            roles = []        
            for record in tx.run(Cypher.roles_get):
                roles.append(record['role'])
            return roles        
        except CypherError as ex:
            logger.error('CypherError: ', ex.message, ' ', ex.code)            
            raise      
        except ClientError as ex:
            logger.error('ClientError: ', ex.message, ' ', ex.code)            
            raise
        except Exception as ex:
            logger.error('Exception: ', ex)            
            raise


    def allowed_email_register(self, email, role):
        try:
            with self.driver.session() as session:
                with session.begin_transaction() as tx:
                    tx.run(Cypher.allowed_email_register, email=email, role=role, admin_name=current_user.name)
                    tx.commit()
        except CypherError as ex:
            logger.error('CypherError: ', ex.message, ' ', ex.code)            
            raise      
        except ClientError as ex:
            logger.error('ClientError: ', ex.message, ' ', ex.code)            
            raise
        except Exception as ex:
            logger.error('Exception: ', ex)            
            raise


    def get_allowed_emails(self):
        try:
            with self.driver.session() as session:
                emailNodes = session.read_transaction(self._getAllowedEmails)
                if emailNodes is not None:
                    return [self.allowed_email_model(**emailNode.properties) for emailNode in emailNodes] 
                return []
        except ServiceUnavailable as ex:
            logger.debug(ex.message)
            return []                 
                                              
    def _getAllowedEmails (self, tx):
        try:
            emailNodes = []
            for record in tx.run(Cypher.get_allowed_emails):
                emailNodes.append(record['email'])
            return emailNodes        
        except CypherError as ex:
            logger.error('CypherError: ', ex.message, ' ', ex.code)            
            raise      
        except ClientError as ex:
            logger.error('ClientError: ', ex.message, ' ', ex.code)            
            raise
        except Exception as ex:
            logger.error('Exception: ', ex)            
            raise

    def find_allowed_email(self, email):
        try:
            with self.driver.session() as session:
                emailNode = session.read_transaction(self._findAllowedEmail, email)
                if emailNode is not None:
                    return self.allowed_email_model(**emailNode.properties) 
                return None
        except ServiceUnavailable as ex:
            logger.debug(ex.message)
            return None                 

    @classmethod                                              
    def _findAllowedEmail (self, tx, email):
        try:
            emailNode = None
            records = tx.run(Cypher.allowed_email_find, email=email)
            if records:
                for record in records:
                    emailNode = record['email']
                    return emailNode        
        except CypherError as ex:
            logger.error('CypherError: ', ex.message, ' ', ex.code)            
            raise      
        except ClientError as ex:
            logger.error('ClientError: ', ex.message, ' ', ex.code)            
            raise
        except Exception as ex:
            logger.error('Exception: ', ex)            
            raise


#This is a classmethod and doesn't need username        
    @classmethod
    def confirm_email(cls, email):
        try:
            with driver.session() as session:
                with session.begin_transaction() as tx:
                    tx.run(Cypher.confirm_email, email=email)
                    tx.commit()
        except CypherError as ex:
            logger.error('CypherError: ', ex.message, ' ', ex.code)            
            raise      
        except ClientError as ex:
            logger.error('ClientError: ', ex.message, ' ', ex.code)            
            raise
        except Exception as ex:
            logger.error('Exception: ', ex)            
            raise

                
#This is a classmethod and doesn't need username
    @classmethod
    def password_reset(cls, eml, psw):
        try:
            with driver.session() as session:
                with session.begin_transaction() as tx:
                    tx.run(Cypher.password_reset, email=eml, password=psw)
                    tx.commit()
        except CypherError as ex:
            logger.error('CypherError: ', ex.message, ' ', ex.code)            
            raise      
        except ClientError as ex:
            logger.error('ClientError: ', ex.message, ' ', ex.code)            
            raise
        except Exception as ex:
            logger.error('Exception: ', ex)            
            raise
       
        
        
