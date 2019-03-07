# coding: utf-8  

from datetime import datetime
import logging
logger = logging.getLogger('stkserver') 
from neo4j.exceptions import CypherSyntaxError, ConstraintError, CypherError

import shareds

#inputs
ROLES = ({'level':'0',  'name':'gedcom',   'description':'Kirjautunut käyttäjä, pääsee vain gedcom-muunnoksiin'},
         {'level':'1',  'name':'member',   'description':'Seuran jäsen täysin lukuoikeuksin'},
         {'level':'2',  'name':'research', 'description':'Tutkija, joka voi käsitellä omaa tarjokasaineistoaan'},
         {'level':'4',  'name':'audit',    'description':'#Valvoja, joka auditoi ja hyväksyy gramps- ja tarjokasaineistoja'},
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

    set_user_constraint1 = """
    CREATE CONSTRAINT ON (user:User) 
        ASSERT (user.email) IS UNIQUE;
    """
 
    set_user_constraint2 = """
    CREATE CONSTRAINT ON (user:User) 
        ASSERT (user.username) IS UNIQUE;
    """  
     
    set_allowed_email_constraint = """ 
    CREATE CONSTRAINT ON (email:Allowed_email) 
    ASSERT email.allowed_email IS UNIQUE
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

#erase total database 
def delete_database(tx):
    tx.run(SetupCypher.delete_database)

def roles_exist():
#  Tarkista roolien olemassaolo
    print('Check the user roles')
    num_of_roles = 0
    results = shareds.driver.session().run(SetupCypher.check_role_count)
    for result in results:
        num_of_roles = result[0]

    return(num_of_roles > 0)
        #inputs
    
def create_role(tx, role):
    try:
        tx.run(SetupCypher.role_create,
            level=role['level'],    
            name=role['name'], 
            description=role['description'])
#        tx.commit()            
#                print(role['name'])
    except CypherSyntaxError as cex:
        logger.error('CypherSyntaxError in create_role ' + cex)
    except CypherError as cex:
        logger.error('CypherError in create_role ' + cex)
    except ConstraintError as cex:
        logger.error('ConstraintError in create_role ' + cex)
#            print(role['name'])

def create_roles():
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


def master_exists():
    print('Check the master user')
    num_of_masters = 0  
    for result in shareds.driver.session().run(SetupCypher.master_check_existence):
        num_of_masters = result[0]
    return(num_of_masters > 0)    

def build_master_user():
    from flask_security import utils as sec_utils
    with shareds.app.app_context():
        return( 
            {'username': 'master', 
             'password': sec_utils.hash_password(shareds.app.config['MASTER_USER_PASSWORD']),  
             'email': shareds.app.config['MASTER_USER_EMAIL'], 
             'name': 'Stk-kannan pääkäyttäjä',
             'language': 'fi',  
             'is_active': True,
             'confirmed_at': datetime.now().timestamp()/1000, 
             'roles': ['master'],
             'last_login_at': datetime.now().timestamp()/1000,
             'current_login_at': datetime.now().timestamp()/1000,
             'last_login_ip': '127.0.0.1',  
             'current_login_ip': '127.0.0.1',
             'login_count': 0            
             } )
            
def create_master(master_user):
    with shareds.driver.session() as session: 
        try:
            session.run(SetupCypher.master_create, master_user) 
        except CypherSyntaxError as cex:
            logger.error('CypherSyntaxError in create_master ' + cex)
            return
        except CypherError as cex:
            logger.error('CypherError in create_master ' + cex)
            return
        except ConstraintError as cex:
            logger.error('ConstraintError in create_master ' + cex)
            return
    logger.info('Master user account created')    


def create_role_constraints():
    with shareds.driver.session() as session: 
        try:
            session.run(SetupCypher.set_role_constraint)
        except CypherError as cex:
            logger.error('CypherError in create_role_constraints ' + cex)
            return
        except ConstraintError as cex:
            logger.error('ConstraintError in create_role_constraints ' + cex)
            return
    logger.info('Role constraints created')


def create_user_constraints():
    with shareds.driver.session() as session: 
        try:  
            session.run(SetupCypher.set_user_constraint1)
            session.run(SetupCypher.set_user_constraint2)  
        except CypherSyntaxError as cex:
            logger.error('ConstraintError in create_user_constraints ' + cex)
            return
        except CypherError as cex:
            logger.error('ConstraintError in create_user_constraints ' + cex)
            return
        except ConstraintError as cex:
            logger.error('ConstraintError in create_user_constraints ' + cex)
            return
    logger.info('User constraints created')
    

def create_allowed_email_constraints():
    with shareds.driver.session() as session: 
        try:  
            session.run(SetupCypher.set_allowed_email_constraint)  
        except CypherSyntaxError as cex:
            logger.error('ConstraintError in create_user_constraints ' + cex)
            return
        except CypherError as cex:
            logger.error('ConstraintError in create_user_constraints ' + cex)
            return
        except ConstraintError as cex:
            logger.error('ConstraintError in create_user_constraints ' + cex)
            return
    logger.info('Allowed email constraints created')


def initialize_db(): 
    if not roles_exist():
        create_role_constraints()
        create_roles()
        
    if not master_exists():
        create_user_constraints()
        create_master(build_master_user())
        create_allowed_email_constraints()
