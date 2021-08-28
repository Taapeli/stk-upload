#!/usr/bin/env python3

"""
Test script to create a user
"""

import argparse
import sys
from pprint import pprint

from flask_security import utils as sec_utils
from flask_security import Security
from flask import Flask

parser = argparse.ArgumentParser()
parser.add_argument("username")
parser.add_argument("password")
parser.add_argument("email")
parser.add_argument("--role", help="Default role, default='research'", default='research')
parser.add_argument("--name", help="User's real name, e.g. Mikko Repolainen, default='Test user'", default='Test user')
args = parser.parse_args()

import shareds
 
from app import app


# copied from database/accessDB.py:
user_create = """
    MATCH  (role:Role) WHERE role.name = $rolename
    CREATE (user:User 
        {username : $username, 
        password : $password,  
        email : $email, 
        name : $name,
        language : $language, 
        is_active : $is_active,
        confirmed_at : timestamp(), 
        roles : $roles,
        last_login_at : timestamp(),
        current_login_at : timestamp(),
        last_login_ip : $last_login_ip,
        current_login_ip : $current_login_ip,
        login_count : $login_count} )           
        -[:HAS_ROLE]->(role)
    CREATE (user) -[:SUPPLEMENTED]-> (prof:UserProfile
        {username : $username, 
        name : $name,
        email : $email
    })
        
        
    RETURN user
    """ 

def build_user(username, password, email, roles, name):
    with app.app_context():
        return( 
            {'username': username, 
             'password': sec_utils.hash_password(password),  
             'email': email, 
             'name': name,
             'language': 'fi',  
             'is_active': True,
             'roles': roles,
             'last_login_ip': '127.0.0.1',  
             'current_login_ip': '127.0.0.1',
             'login_count': 0            
             } )
            
def create_user(username, password, email, rolename, name):
    user = build_user(username, password, email, [rolename], name)
    #pprint(user)
    with shareds.driver.session() as session: 
        try:
            res = session.run(user_create, user, rolename=rolename).single()
            if res:
                print(f"User {user['username']} created")
            else:
                print(f"User creation FAILED")
        except Exception as e:
            print(f"User creation FAILED: {e}")
     
#roles = args.roles.split(",")    
create_user(args.username, args.password, args.email, args.role, args.name)




