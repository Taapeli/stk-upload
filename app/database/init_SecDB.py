'''
Copy this file to your instance folder where you have the instance config.py 
and execute it to initialize the started database for flask-security roles
'''

import sys
import os
import datetime
import config

from neo4j.v1 import GraphDatabase
from neo4j.exceptions import ConstraintError

#neo4j config
uri = config.NEO4J_URI
auth = (config.NEO4J_USERNAME, config.NEO4J_PASSWORD)
driver = GraphDatabase.driver(uri, auth=auth)

#inputs

ROLES = ({'level':'0', 'name':'guest', 'description':'Guest user with limited read permissions'},
         {'level':'1', 'name':'user', 'description':'Basic user with read/write permissions to own trees'},
         {'level':'4', 'name':'audit', 'description':'Auditor with read permission to everything'},
         {'level':'8', 'name':'admin', 'description':'Administrator with all permissions'})

role_create = 'CREATE (role:Role {name : $name, description : $description})' 

#functions

def confirm(question):
    valid = {"yes": True, "y": True, "no": False, "n": False}
    prompt = " [y/n] "
    while True:
        sys.stdout.write(question + prompt)
        choice = input().lower()
        if choice in valid:
            return valid[choice]
        else:
            sys.stdout.write("Please respond with 'yes' or 'no' (or 'y' or 'n').\n")

def delete_database(tx):
    '''erase database'''
    tx.run('MATCH (n) OPTIONAL MATCH (n)-[r]-() DELETE n,r')

def create_constraints(tx):
    tx.run('CREATE CONSTRAINT ON (role:Role) ASSERT role.name IS UNIQUE')

class Create:
    def __init__ (self, username):
        self.username=username        

    def roles(self, tx, ROLES):
        for role in ROLES:
            try:
                tx.run(role_create, 
                    name=role['name'], 
                    description=role['description'],
                    time=str(datetime.datetime.now()) )    
            except ConstraintError as cex:
                print(cex)
                continue
        
if not confirm('Are you sure you want to proceed? This is should probably only be run when setting up the database'):
    sys.exit()

if confirm('Do you want to a wipe existing data and rebuild the constraints?'):
    print('Performing a full reset of database')
    with driver.session() as session:
        session.write_transaction(delete_database)   
else:
    print('Attempting to create the following while retaining existing data:\n'
    '  * role:start' )

with driver.session() as session: 
    session.write_transaction(create_constraints)

with driver.session() as session:
    try:
        session.write_transaction(Create('start').roles, ROLES)
    except ConstraintError as cex:
        print('Session ', cex)
        
print ('Complete')

