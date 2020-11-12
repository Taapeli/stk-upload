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
from neo4j.exceptions import ServiceUnavailable, ConstraintError

from .cypher_adm import Cypher_adm

logger = logging.getLogger('stkserver')


class UserProfile():
    """ Object describing dynamic user properties """
    name = ''
    email = ''
    username = ''
    language = ''
    GSF_membership = ''
    research_years = ''
    software = ''
    researched_names = ''
    researched_places = ''
    text_message = ''
    created_at = None
    approved_at = None

    def __init__(self, **kwargs):
        self.username = kwargs.get('username')
        self.name = kwargs.get('name')
        self.email = kwargs.get('email')
        self.language = kwargs.get('language')
        self.GSF_membership = kwargs.get('GSF_membership')
        self.research_years = kwargs.get('research_years')
        self.software = kwargs.get('software')
        self.researched_names = kwargs.get('researched_names')
        self.researched_places = kwargs.get('researched_places')
        self.text_message = kwargs.get('text_message')

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
    def _build_profile_from_record(cls, userProfile):
        ''' Returns an UserProfile class instance '''
        if userProfile is None:
            return None
        profile = UserProfile(**userProfile)
#        email.default_role = emailRecord['default_role'] 
        if profile.created_at:
            profile.created_at = datetime.fromtimestamp(float(profile.created_at)/1000) 
        if profile.approved_at:    
            profile.approved_at = datetime.fromtimestamp(float(profile.approved_at)/1000)        
        return profile

    @classmethod         
    def _build_user_from_node(self, userRecord):
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
    def register_applicant(cls, profile, role):
        try:
            with shareds.driver.session() as session:
                with session.begin_transaction() as tx:
                    tx.run(Cypher_adm.user_profile_register,   
                        name = profile.name,
                        email = profile.email,
                        username = profile.username,
                        language = profile.language,
                        research_years = profile.research_years,
                        software = profile.software,
                        researched_names = profile.researched_names,
                        researched_places = profile.researched_places,
                        text_message = profile.text_message)
                    
                    tx.commit()
            return(True)        
        except ConstraintError as ex:
            logging.error('ConstraintError: ', ex.message, ' ', ex.code)            
            flash(_("Given allowed email address already exists"))                            
        except Exception as e:
            logging.error(f'UserAdmin.register_applicant: {e.__class__.__name__}, {e}')            
            raise      
 
    @classmethod
    def update_user_profile(cls, profile):
        try:
            with shareds.driver.session() as session:
                with session.begin_transaction() as tx:
                    tx.run(Cypher_adm.user_profile_update,  
                        name = profile.name,
                        email = profile.email,
                        username = profile.username,
                        language = profile.language,
                        research_years = profile.research_years,
                        software = profile.software,
                        researched_names = profile.researched_names,
                        researched_places = profile.researched_places,
                        text_message = profile.text_message)
                    tx.commit()
            return(True)        
        except Exception as e:
            logging.error(f'UserAdmin.update_applicant: {e.__class__.__name__}, {e}')          
            raise

    @classmethod
    def user_profile_add(cls, tx, email, username):
#        logging.debug('_put_role ', role)
        try:
            tx.run(Cypher_adm.user_profile_add, email=email, username=username) 
            return
        except Exception as e:
            logging.error(f'UserAdmin.user_profile_add: {e.__class__.__name__}, {e}')          
            raise  

    @classmethod   
    def get_user_profiles(cls):
        try:
            with shareds.driver.session() as session:
                profileRecords = session.read_transaction(cls._getProfileRecords)
                result = []
                for record in profileRecords:
                    node = record['profile']
                    result.append(cls._build_profile_from_record(node))
                return result

        except ServiceUnavailable as ex:
            logging.debug(ex.message)
            return []                 

    @classmethod                                              
    def _getUserProfiles(cls, tx):
        try:
            profileRecords = [record for record in tx.run(Cypher_adm.user_profiles_get)]    
            return(profileRecords)       
        except Exception as e:
            logging.error(f'UserAdmin._getUserProfiles: {e.__class__.__name__}, {e}')          
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
    def update_user_email(cls, username, email):
        try:
#             result = shareds.driver.session().run(Cypher_adm.user_update_language,
#                          username=username,language=language).single()
#             return result
            print("*** Update user is not done! ***")
            return("Ok")
        except ServiceUnavailable as ex:
            logging.debug(ex.message)
            return None                 

    @classmethod 
    def confirm_updated_email(cls, username, email):
        try:
#             result = shareds.driver.session().run(Cypher_adm.user_update_language,
#                          username=username,language=language).single()
#             return result
            print("*** Update user is not done! ***")
            return("Ok")
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
                return(cls._build_user_from_node(updated_user))

        except ServiceUnavailable as ex:
            logging.debug(ex.message)
            return None                 

    @classmethod                                              
    def _update_user (cls, tx, user):    

        try:
            logging.debug(f'user update {user.email} {user.name}')
            if user.username == 'master': 
                user.roles = ['master']
            if user.username == 'guest': 
                user.roles = ['guest']    
#   Identifier and history fields are not to be updated
            result = tx.run(Cypher_adm.user_update, 
                email = user.email,
 #               username = user.username,
                name = user.name, 
                language = user.language,              
                is_active = user.is_active,
                roles = user.roles)
            if user.username not in {'master', 'guest'}:
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
        except Exception as e:
            logging.error(f'UserAdmin._update_user: {e.__class__.__name__}, {e}')          
            raise  

    @staticmethod 
    def get_accesses():
        try:
            rsp = []
            for rec in shareds.driver.session().run(Cypher_adm.list_accesses):
                user = dict(rec.get("user"))
                batch = dict(rec.get("batch"))
                batch["file"] = batch["file"].split("/")[-1].\
                    replace("_clean.gramps",".gramps").replace("_clean.gpkg",".gpkg")
                #rel = dict(rec.get("r"))
                rel_id = rec.get("rel_id")
                cnt_own = rec.get("cnt")
                access = dict(user=user, batch=batch, rel_id=rel_id, cnt=cnt_own)
                print("access:", access)
                rsp.append(access)
            logger.info(f"-> bp.admin.models.user_admin.UserAdmin.get_accesses n={len(rsp)}")
            return rsp

        except ServiceUnavailable as ex:
            logging.debug(ex.message)
            return None                 

    
    @staticmethod
    def add_access(username, batchid):
        try:
            logger.info(f"-> bp.admin.models.user_admin.UserAdmin.add_access u={username} b={batchid}")
            rsp = shareds.driver.session().run(Cypher_adm.add_access,username=username,batchid=batchid).single()
            return rsp
        except ServiceUnavailable as ex:
            logging.debug(ex.message)
            return None                 
    
    @staticmethod
    def delete_accesses(idlist):
        try:
            logger.info(f"-> bp.admin.models.user_admin.UserAdmin.delete_accesses i={idlist}")
            rsp = shareds.driver.session().run(Cypher_adm.delete_accesses,idlist=idlist).single()
            return rsp
        except ServiceUnavailable as ex:
            logging.debug(ex.message)
            return None                 
    
    
    
        