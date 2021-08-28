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
args = parser.parse_args()

import shareds
 
from app import app

user_delete = """
    MATCH (user:User {username : $username})
    OPTIONAL MATCH (prof:UserProfile{username : $username})
    DETACH DELETE user, prof
    RETURN user
    """ 

def delete_user(username):
    with shareds.driver.session() as session: 
        res = session.run(user_delete, username=username).single()
        if res:
            print(f"User {username} deleted")
        else:
            print(f"User deletion FAILED")
    

delete_user(args.username)




