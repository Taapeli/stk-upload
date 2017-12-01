#!/usr/bin/env pytho
# -*- coding: utf-8 -*-

import sys
import os
import datetime

from neo4j.v1 import GraphDatabase

#neo4j config
uri = "bolt://localhost:7687"
auth = (os.getenv('NEO4J_USERNAME'), os.getenv('NEO4J_PASSWORD'))
driver = GraphDatabase.driver(uri, auth=auth)

#inputs

ROLES = ({'level':'0', 'name':'user', 'description':'Basic user with limited read permissions'},
         {'level':'8', 'name':'audit', 'description':'Auditor with read permission to everything'},
         {'level':'9', 'name':'admin', 'description':'Administrator with all permissions'})

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
#erase database 
def delete_database(tx):
	tx.run('MATCH (n) OPTIONAL MATCH (n)-[r]-() DELETE n,r')

class Create:
	def __init__ (self, username):
		self.username=username		

	def roles(self, tx, ROLES):
		for role in ROLES: 
			tx.run(role_create, 
                   name=role['name'], 
                   description=role['description'],
                   time=str(datetime.datetime.now()) )	

if not confirm('Are you sure you want to proceed? This is should probably only be run when setting up the database'):
	sys.exit()
else:
	if confirm('Do you want to a wipe existing data and rebuild the constraints?'):
		print('Performing a full reset of database')
		with driver.session() as session:
			session.write_transaction(delete_database)
	else: print('Attempting to create the following while retaining existing data:\n'
		'  * role:start' )
	with driver.session() as session:
		session.write_transaction(Create('start').roles, ROLES)

	print ('Complete')


