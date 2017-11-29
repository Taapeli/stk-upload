# -*- coding: utf-8 -*-
'''
Created on 28.9.2017

@author: TimNal
'''

from flask_security.datastore import UserDatastore
from .seccypher import Cypher  
from neo4j.exceptions import ServiceUnavailable
#import copy
import datetime

driver = None

class Neo4jUserDatastore(UserDatastore):
 
#===============================================================================
#     class Role():
#         name = ''
#         description = ''
# 
#     class User():
#         email = ''
# #        self.name = kwargs['email']
#         password = ''
#         is_active = True
#         confirmed_at = ''
#         roles = []
#===============================================================================
    
    def __init__(self, driver, user_model, role_model):
        self.driver = driver
        self.user_model = user_model
        self.role_model = role_model
        self.role_dict = self.get_roles() 
        
    def _build_user_from_node(self, userNode):
        if userNode is not None:
            user = self.user_model(**userNode.properties)
            user.id = str(userNode.id)
            user.roles = [self.role_model(name=rolename, description='', timestamp=datetime.datetime.now()) for rolename in user.roles]
            if 'confirmed_at' in userNode.properties: 
                timestamp = float(userNode.properties['confirmed_at'])
                user.confirmed_at = datetime.datetime.fromtimestamp(timestamp)
            return user
        return None   
                       
        
    def put(self, model):
        with self.driver.session() as session:
            try:
                if isinstance(model, self.user_model):
                    return session.write_transaction(self._put_user, model)                    
                elif isinstance(model, self.role_model):
                    return session.write_transaction(self._put_role, model)
            except ServiceUnavailable as ex:
                print(ex.format())            
                return None
            
    def _put_user (self, tx, user):
#        print('_put_user ', user.email, ' ', user.name)
        if not user.id:         # New user
            if len(user.roles) == 0:
                user.roles.append('user')
            user.confirmed_at = None
            user.is_active = True
            result = tx.run(Cypher.user_register,
                email = user.email,
                password = user.password, 
                is_active = user.is_active,
                confirmed_at = user.confirmed_at,            
                roles = user.roles,
                username = user.username,
                name = user.name,
                language = user.language )
            for record in result:
                userNode = (record['user'])
                user.id = str(userNode.id)
                return user
        else:               # Update user
            rolelist = []
            for role in user.roles:
                if isinstance(role, self.role_model):
                    rolelist.append(role.name)
                else: 
                    rolelist.append(role)
            tx.run(Cypher.user_update, 
                id=int(user.id), 
                email=user.email,
                password=user.password, 
                is_active=user.is_active,
                confirmed_at=int(user.confirmed_at.timestamp()),            
                roles=rolelist,
                username = user.username,
                name = user.name,
                language = user.language )
        tx.commit()            
        return user     
        

    
    def _put_role (self, tx, role):
#        print('_put_role ', role)
        roleNode = tx.run(Cypher.role_register, name=role.name, 
            description=role.description)
#        return self.user_model(**roleNode.properties)
        return self.role_model(**roleNode.items())

    def commit(self):
        pass
#        self.tx.commit()
    
    def get_user(self, id_or_email):
#        self.email = id_or_email
        try:
            with self.driver.session() as session:
                userNode = session.read_transaction(self._getUser, id_or_email) 
                print ('get_user ', id_or_email, ' ', userNode)
                return(self._build_user_from_node(userNode))
        except ServiceUnavailable as ex:
            print(ex.format())
            return None
                        
    def _getUser (self, tx, pemail):
        for record in tx.run(Cypher.email_or_id_find, id_or_email=pemail):
            userNode = (record['user'])
            return userNode
        
    def get_users(self):
        try:
            with self.driver.session() as session:
                userNodes = session.read_transaction(self._getUsers)
                if userNodes is not None:
                    return [self._build_user_from_node(userNode) for userNode in userNodes] 
                return []
        except ServiceUnavailable as ex:
            print(ex.format())
            return []                 
                                                
    def _getUsers (self, tx):
        userNodes = []
        for record in tx.run(Cypher.get_users):
            userNodes.append(record['user'])
        return userNodes        

                
    def find_user(self, *args, **kwargs):
#        print('find_user ', args, ' ', kwargs)
        try:
            with self.driver.session() as session:
                userNode = session.read_transaction(self._findUser, kwargs['id']) 
#                print('find_user (node) ', userNode)
                return(self._build_user_from_node(userNode))
        except ServiceUnavailable as ex:
            print(ex.format())
            return None
        
    def _findUser (self, tx, arg):
        rid = int(arg)
#        print('rid=', rid)
        for record in tx.run(Cypher.id_find, id=rid):
            user = (record['user'])
            return user        
            
    def _findUserRoles (self, tx, pemail):
        roles = []
        for record in tx.run(Cypher.user_roles_find, email=pemail):
            roles.append(record['role'])
        print ('_findUserRoles ', pemail, roles)    
        return roles
        
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
            print(ex.format())
            return None
        
    def _findRole (self, tx, roleName):
        for record in tx.run(Cypher.role_find, name=roleName):
            return (record['role'])                
                                
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
            print(ex.format())
            return None
                        
    def _getRole (self, tx, rid):
        for record in tx.run(Cypher.role_get, id=rid):
            return (record['role'])        

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
            print(ex.format())
            return None
                                
    def _getRoles (self, tx):
        roles = []        
        for record in tx.run(Cypher.roles_get):
            roles.append(record['role'])
        return roles        

#This is a classmethod and doesn't need username        
    @classmethod
    def confirm_email(cls, email):
        with driver.session() as session:
            with session.begin_transaction() as tx:
                tx.run(Cypher.confirm_email, email=email)
                tx.commit()
                
#This is a classmethod and doesn't need username
    @classmethod
    def password_reset(cls, eml, psw):
        with driver.session() as session:
            with session.begin_transaction() as tx:
                tx.run(Cypher.password_reset, email=eml, password=psw)
                tx.commit()
#                tx.run(Cypher.password_reset, email=email, password=bcrypt.encrypt(password))
       
        
        
        
        
        
        
        