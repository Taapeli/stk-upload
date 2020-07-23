# coding: utf-8 
'''
Created on 28.9.2017

@author: TimNal
'''

#from flask_security import current_user
from flask_security.datastore import UserDatastore
from .seccypher import Cypher  
from neo4j.exceptions import ServiceUnavailable, ClientError, ConstraintError
from datetime import datetime
#import shareds
import logging
import traceback
logger = logging.getLogger('neo4juserdatastore')

driver = None

from bp.admin.models.user_admin import UserAdmin

class Neo4jUserDatastore(UserDatastore):
    """ User info database designed after a Flask-security UserDatastore and observed Flask-security behavior:
    
    class flask_security.datastore.UserDatastore(user_model, role_model)
        Abstracted user datastore.
        Parameters
           • user_model – A user model class definition
           • role_model – A role model class definition
           
        activate_user(user)
           Activates a specified user. Returns True if a change was made.
           Parameters user – The user to activate
           
        add_role_to_user(user, role)
           Adds a role to a user.
           Parameters
              • user – The user to manipulate
              • role – The role to add to the user

        create_role(**kwargs)
           Creates and returns a new role from the given parameters.
           
        create_user(**kwargs)
           Creates and returns a new user from the given parameters.
           
        deactivate_user(user)
           Deactivates a specified user. Returns True if a change was made.
           Parameters user – The user to deactivate
           
        delete_user(user)
           Deletes the specified user.
           Parameters user – The user to delete
           
        find_or_create_role(name, **kwargs)
           Returns a role matching the given name or creates it with any additionally provided parameters.
           
        find_role(*args, **kwargs)
           Returns a role matching the provided name.
           
        find_user(*args, **kwargs)
           Returns a user matching the provided parameters.
           
        get_user(id_or_email)
           Returns a user matching the specified ID or email address.
           
        remove_role_from_user(user, role)
           Removes a role from a user.
           Parameters
              • user – The user to manipulate
              • role – The role to remove from the user
              
        toggle_active(user)
           Toggles a user’s active status. Always returns True.
    """

    # Uses classes Role, User, UserProfile from setups.py

    def __init__(self, driver, user_model, user_profile_model, role_model):
        self.driver = driver
        self.user_model = user_model
        self.user_profile_model = user_profile_model
#        self.allowed_email_model = allowed_email_model        
        self.role_model = role_model
#       self.role_dict = self.get_roles() 
        
    def _build_user_from_record(self, userRecord):
        ''' Returns a User class based on a user type node '''
        try:
            if userRecord is None:
                return None
            user = self.user_model(**userRecord)
#            print(userRecord.id)
            user.id = user.username
            user.roles = self.find_UserRoles(user.email)
            
#             user.confirmed_at = 0
#             user.last_login_at = 0
#             user.current_login_at = 0
            if user.confirmed_at:
                user.confirmed_at = datetime.fromtimestamp(float(user.confirmed_at)/1000)
            if user.last_login_at:    
                user.last_login_at = datetime.fromtimestamp(float(user.last_login_at)/1000)
            if user.current_login_at:     
                user.current_login_at = datetime.fromtimestamp(float(user.current_login_at)/1000)  
            return user
        except Exception as ex:
            print(ex)
            traceback.print_exc()
#  
#     def email_accepted(self, proposed_email):
#         return proposed_email == self.find_allowed_email(proposed_email)
#                               
        
    def put(self, model):
        
            try:
                if isinstance(model, self.user_model):
                    userRecord = None
                    if not model.id:    # New user to insert
                        with self.driver.session() as session:
                            userRecord = session.write_transaction(self._put_user, model)
                    else:               # Old user to update
                        with self.driver.session() as session:                        
                            userRecord = session.write_transaction(self._update_user, model) 
                    return(self._build_user_from_record(userRecord))                                        
                elif isinstance(model, self.role_model):
                    return session.write_transaction(self._put_role, model)
            except ServiceUnavailable as ex:
                logger.error(ex)            
                return None
            except Exception as ex:
                logger.error(ex)            
                raise
            
    def _put_user (self, tx, user):    # ============ New user ==============

        if not user.username == 'guest':
            allowed_email = UserAdmin.find_allowed_email(user.email)
            if (allowed_email == None) or (allowed_email.approved != True):
                return(None)
        if len(user.roles) == 0:
            user.roles = [allowed_email.default_role] 
#        user.confirmed_at = None
        user.is_active = True
        try:
            logger.info('_put_user new %s %s', user.username, user.roles[0])                
            result = tx.run(Cypher.user_register,
                email = user.email,
                password = user.password, 
                is_active = user.is_active,
                confirmed_at = user.confirmed_at,            
                roles = user.roles,
                username = user.username,
                name = user.name,
                language = user.language,
                last_login_at = user.last_login_at,
                current_login_at = user.current_login_at,
                last_login_ip = user.last_login_ip,
                current_login_ip = user.current_login_ip,
                login_count = user.login_count )

            node = result.single()
            if node:
                userRecord = node['user']
                if user.username == 'guest':
                    status = None
                else:    
                    status = allowed_email.approved
                if (status == None) or (status == True):
#                userNode = (record['user'])
#                logger.debug(userNode)
                    UserAdmin.user_profile_add(tx, userRecord['email'], userRecord['username'])
                   
#                tx.commit()
                logger.info(f'User with email address {user.email} registered') 
                
                return(userRecord)
            else:
                logger.info(f'put_user: Cannot register user with {user.email}') 
                raise RuntimeError(f'Could not register user with {user.email}')
                
#            tx.commit()
        except Exception as e:
            logging.error(f'Neo4jUserDatastore._put_user: {e.__class__.__name__}, {e}')            
            raise      

    def _update_user (self, tx, user):         # ============ User update ==============

#         print(user.email, user.confirmed_at)

        confirmtime = int(user.confirmed_at.timestamp() * 1000) if user.confirmed_at else None   
 
        if user.username == 'master': 
            rolelist = ['master']
        else:    
            rolelist = []
#   Build a list of updated user role names        
            for role in user.roles:
                roleToAdd = (role.name if isinstance(role, self.role_model) else role)
                if not roleToAdd in rolelist:
                    rolelist.append(roleToAdd)
        try:
            logger.debug('_put_user update' + user.email + ' ' + user.name)

            result = tx.run(Cypher.user_update, 
                id=user.username, 
                email=user.email,
                password=user.password, 
                is_active=user.is_active,
                #confirmed_at = int(user.confirmed_at.timestamp() * 1000),            
                confirmed_at = confirmtime,            
                roles=rolelist,
                username = user.username,
                name = user.name,
                language = user.language, 
                last_login_at = int(user.last_login_at.timestamp() * 1000) if user.last_login_at else None,
                current_login_at = int(user.current_login_at.timestamp() * 1000) if user.current_login_at else None,
                last_login_ip = user.last_login_ip,
                current_login_ip = user.current_login_ip,
                login_count = user.login_count )
            userRecord = result.single()['user']
#   Find list of previous user -> role connections
            prev_roles = [rolenode.name for rolenode in self.find_UserRoles(user.email)]
#   Delete connections that are not in edited connection list            
            for rolename in prev_roles:
                if not rolename in rolelist:
                    tx.run(Cypher.user_role_delete,
                           email = user.email,
                           name = rolename) 
#   Add connections that are not in previous connection list                    
            for rolename in rolelist:
                if not rolename in prev_roles:
                    tx.run(Cypher.user_role_add, 
                           email = user.email,
                           name = rolename)        
            logger.info('User with email address {} updated'.format(user.email))
#   Confirm time is copied to allowed email         
            if user.confirmed_at:
                UserAdmin.confirm_allowed_email(tx, user.email, confirmtime)   

            return (userRecord)
        
        except Exception as e:
            logging.error(f'Neo4jUserDatastore._update_user: {e.__class__.__name__}, {e}')            
            raise      

#        tx.commit()            
#        return user     

    def _put_role (self, tx, role):             # ============ New role ==============
        try:
            roleNode = tx.run(Cypher.role_register, 
                              level = role.level, 
                              name=role.name, 
                              description=role.description)
        #                      timestamp = datetime.datetime.timestamp())
            return self.role_model(**roleNode._properties)
        except Exception as e:
            logging.error(f'Neo4jUserDatastore._put_role: {e.__class__.__name__}, {e}')            
            raise      

    
    def commit(self):
        pass
#        self.tx.commit()
 
    
    def get_user(self, id_or_email):
#        self.email = id_or_email
        try:
            with self.driver.session() as session:
                userNode = session.read_transaction(self._getUser, id_or_email)
                return(self._build_user_from_record(userNode) if userNode else None)
        except ServiceUnavailable as ex:
            logger.debug(ex.message)
            return None

    def _getUser (self, tx, pemail):
            try:
                result = tx.run(Cypher.email_or_id_find, id_or_email=pemail).single()
                return(result['user'] if result else None)
            except Exception as e:
                logging.error(f'Neo4jUserDatastore._getUser: {e.__class__.__name__}, {e}')            
                raise      

        
    def get_users(self):
        try:
            with self.driver.session() as session:
                userNodes = session.read_transaction(self._getUsers)
                if userNodes is not None:
                    return [self.user_model(**userNode) for userNode in userNodes] 
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
        except Exception as e:
            logging.error(f'Neo4jUserDatastore._getUsers: {e.__class__.__name__}, {e}')            
            raise      

                
    def find_user(self, *args, **kwargs):
#        print('find_user ', args, ' ', kwargs)
        try:
            with self.driver.session() as session:
                userNode = session.read_transaction(self._findUser, kwargs['id'])
                return(self._build_user_from_record(userNode) if userNode else None)
        except ServiceUnavailable as ex:
            logger.debug(ex.message)
            return None
        
    def _findUser (self, tx, arg):
        try:
            result = tx.run(Cypher.id_find, id=arg).single()
            return(result['user'] if result else None)               
        except Exception as e:
            logging.error(f'Neo4jUserDatastore._findUser: {e.__class__.__name__}, {e}')            
            raise      

    def find_UserRoles(self, email):
        try:
            with self.driver.session() as session:
                userRoles = session.read_transaction(self._findUserRoles, email) 
                if len(userRoles) > 0:
                    return [self.role_model(**roleRecord) for roleRecord in userRoles] 
                return None
        except ServiceUnavailable as ex:
            logger.debug(ex.message)
            raise
 
            
    def _findUserRoles (self, tx, pemail):
        try:
            records = tx.run(Cypher.user_roles_find, email=pemail)
            return([record['role'] for record in records])
        except Exception as e:
            logging.error(f'Neo4jUserDatastore._findUserRoles: {e.__class__.__name__}, {e}')            
            raise      

        
    def find_role(self, roleName):
        try:
            with self.driver.session() as session:
                roleRecord = session.read_transaction(self._findRole, roleName) 
                if roleRecord is not None:
                    role =  self.role_model(**roleRecord)
                    role.id = str(roleRecord.id)
                    return role
                return None
        except ServiceUnavailable as ex:
            logger.debug(ex.message)
            return None
        
    def _findRole (self, tx, roleName):
        try:
            return(tx.run(Cypher.role_find, name=roleName).single())
        except Exception as e:
            logging.error(f'Neo4jUserDatastore._findRole: {e.__class__.__name__}, {e}')            
            raise      

                                  
    def get_role(self, rid):
        self.id = rid
        try:
            with self.driver.session() as session:
                roleRecord = session.read_transaction(self._getRole, id) 
#                print ('get_role ', rid, ' ', roleNode)
                if roleRecord is not None:
                    role =  self.role_model(**roleRecord)
                    role.id = str(roleRecord.id)
                    return role
                return None
        except ServiceUnavailable as ex:
            logger.debug(ex.message)
            return None
                        
    def _getRole (self, tx, rid):
        try:
            return(tx.run(Cypher.role_get, id=rid).single())
        except Exception as e:
            logging.error(f'Neo4jUserDatastore._getRole: {e.__class__.__name__}, {e}')            
            raise      


    def get_roles(self):
        try:
            with self.driver.session() as session:
                roles = {}
                roleRecords = session.read_transaction(self._getRoles) 
#                print ('get_role ', rid, ' ', roleNode)
                if len(roleRecords) > 0:
                    for roleRecord in roleRecords:
                        role =  self.role_model(**roleRecord)
                        role.id = str(roleRecords.id)
                        roles[role.name]=role
                    return roles
                return None
        except ServiceUnavailable as ex:
            logger.debug(ex.message)
            raise
                                
    def _getRoles (self, tx):
        try:
            return([record['role'] for record in tx.run(Cypher.roles_get)])
        except Exception as e:
            logging.error(f'Neo4jUserDatastore._getRoles: {e.__class__.__name__}, {e}')            
            raise      


    def _confirm_email(self, email, confirmtime):
        try:
            with driver.session() as session:
                with session.begin_transaction() as tx:
                    tx.run(Cypher.confirm_email, email=email)
                    UserAdmin.confirm_allowed_email(tx, email['email'], email['confirmed__at'])   
                    tx.commit()
            logger.info('Email address {} confirmed'.format(email))                            
        except Exception as e:
            logging.error(f'Neo4jUserDatastore._confirm_email: {e.__class__.__name__}, {e}')            
            raise      

                
    def password_reset(self, eml, psw):
        try:
            with driver.session() as session:
                with session.begin_transaction() as tx:
                    tx.run(Cypher.password_reset, email=eml, password=psw)
                    tx.commit()
        except Exception as e:
            logging.error(f'Neo4jUserDatastore.password_reset: {e.__class__.__name__}, {e}')            
            raise      
        
