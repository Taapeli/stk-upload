# coding: utf-8  

import sys
import datetime
import logging
logger = logging.getLogger('stkserver') 
from neo4j.exceptions import CypherSyntaxError, ConstraintError, CypherError

#neo4j config
import shareds

#inputs
ROLES = ({'level':'0',  'name':'guest',    'description':'Kirjautumaton käyttäjä rajoitetuin lukuoikeuksin'},
         {'level':'1',  'name':'member',   'description':'Seuran jäsen täysin lukuoikeuksin'},
         {'level':'2',  'name':'research', 'description':'Tutkija, joka voi päivittää omaa tarjokaskantaansa'},
         {'level':'4',  'name':'audit',    'description':'Valvoja, joka auditoi ja hyväksyy ehdokasaineistoja'},
         {'level':'8',  'name':'admin',    'description':'Ylläpitäjä kaikin oikeuksin'},
         {'level':'16', 'name':'master',   'description':'Tietokannan pääkäyttäjä, ei sovellusoikeuksia'})


class SetupCypher():
    """ Cypher classes for setup """
#erase database 
    delete_database = """
    MATCH (n) OPTIONAL MATCH (n)-[r]-() DELETE n,r
    """
    check_role_count = """
    MATCH (a:Role) RETURN COUNT(a)
    """

    set_role_constraint = """
    CREATE CONSTRAINT ON (role:Role) ASSERT role.name IS UNIQUE
    """

    role_create = """
    CREATE (role:Role 
    {level: $level, name: $name, 
    description: $description, timestamp: timestamp()})
    """

    master_check_existence = """
    MATCH  (user:User) WHERE user.username = 'master' RETURN COUNT(user)
    """
        
    email_val = """
    MATCH (a:Allowed_email) WHERE a.allowed_email = $email RETURN COUNT(a)
    """

    set_user_constraint = """
    CREATE CONSTRAINT ON (user:User) 
    ASSERT user.username IS UNIQUE
    ASSERT user.email IS UNIQUE
    """
            
    master_create = """
    MATCH  (role:Role) WHERE role.name = 'master'
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
    """ 


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

def create_role_constraints(tx):
    tx.run(SetupCypher.set_role_constraints)

class Create:
    def __init__ (self, username):
        self.username=username        

    def roles(self, tx, ROLES):
        for role in ROLES:
            try:
                tx.run(SetupCypher.role_create,
                    level=role['level'],    
                    name=role['name'], 
                    description=role['description'],
                    timestamp=str(datetime.datetime.now()) )    
            except ConstraintError as cex:
                print(cex)
                continue


#  Tarkista roolien olemassaolo
print('Check the user roles')
num_of_roles = 0
results = shareds.driver.session().run(SetupCypher.check_role_count)
for result in results:
    num_of_roles = result[0]

if num_of_roles == 0:
    #inputs
    ROLES = ({'level':'0', 'name':'guest', 
              'description':'Kirjautumaton käyttäjä rajoitetuin lukuoikeuksin'},
             {'level':'1', 'name':'member', 
              'description':'Seuran jäsen täysin lukuoikeuksin'},
             {'level':'2', 'name':'research', 
              'description':'Tutkija, joka voi päivittää omaa tarjokaskantaansa'},
             {'level':'4', 'name':'audit', 
              'description':'Valvoja, joka auditoi ja hyväksyy ehdokasaineistoja'},
             {'level':'8', 'name':'admin', 
              'description':'Ylläpitäjä kaikin oikeuksin'},
             {'level':'16', 'name':'master', 
              'description':'Tietokannan pääkäyttäjä ilman sovellusoikeuksia'})
    
    
    #functions
    def create_role_constraints(tx):
        try:
            tx.run(SetupCypher.set_role_constraint)
            tx.commit() 
        except CypherSyntaxError as cex:
            print(cex)
    
    def create_role(tx, role):
        try:
            tx.run(SetupCypher.role_create,
                level=role['level'],    
                name=role['name'], 
                description=role['description'])
            tx.commit()            
#                print(role['name'])
        except CypherSyntaxError as cex:
            print(cex)
        except CypherError as cex:
            print(cex)
        except ConstraintError as cex:
            print(cex)
#            print(role['name'])



    def delete_database():
        print('Performing a full reset of database')
        with shareds.driver.session() as session:
            session.write_transaction(SetupCypher.delete_database)

    def create_role_constraints():
        with shareds.driver.session() as session: 
            session.write_transaction(SetupCypher.set_role_constraint)

    def create_user_constraints():
        with shareds.driver.session() as session:
            for role in ROLES:
                try:    
                    session.write_transaction(create_role, role)
                    print(role['name'])
                except CypherSyntaxError as cex:
                    print('Session ', cex)
                    continue
                except CypherError as cex:
                    print('Session ', cex)
                    continue
                except ConstraintError as cex:
                    print('Session ', cex)
                    continue
        print('Roles initialized')



