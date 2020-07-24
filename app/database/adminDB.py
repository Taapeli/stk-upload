# coding: utf-8  

from datetime import datetime
import logging
logger = logging.getLogger('stkserver') 
from neo4j.exceptions import CypherSyntaxError, ConstraintError
from flask_security import utils as sec_utils

import shareds
from .cypher_setup import SetupCypher
from .schema_fixes import do_schema_fixes

#inputs
ROLES = ({'level':'0',  'name':'guest',    'description':'Rekisteröitymätön käyttäjä, näkee esittelysukupuun'},
         {'level':'1',  'name':'gedcom',   'description':'Kirjautunut käyttäjä, pääsee vain gedcom-muunnoksiin'},
         {'level':'2',  'name':'member',   'description':'Seuran jäsen täysin lukuoikeuksin'},
         {'level':'4',  'name':'research', 'description':'Tutkija, joka voi käsitellä omaa tarjokasaineistoaan'},
         {'level':'8',  'name':'audit',    'description':'#Valvoja, joka auditoi ja hyväksyy gramps- ja tarjokasaineistoja'},
         {'level':'16', 'name':'admin',    'description':'Ylläpitäjä kaikin oikeuksin'},
         {'level':'32', 'name':'master',   'description':'Tietokannan pääkäyttäjä, ei sovellusoikeuksia'})


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
    return(num_of_roles == len(ROLES))
        #inputs
def role_exists(name):
#    print(f'Check the existense of the {name} role')
    num_of_roles = 0  
    for result in shareds.driver.session().run(SetupCypher.role_check_existence, rolename=name):
        num_of_roles = result[0] 
    return(num_of_roles > 0) 
       
def create_role(tx, role):
    try:
        tx.run(SetupCypher.role_create,
            level=role['level'],    
            name=role['name'], 
            description=role['description'])
#        tx.commit()            
#                print(role['name'])
    except CypherSyntaxError as cex:
        logger.error('CypherSyntaxError in create_role ' + cex.message)
    except Exception as e:
        logging.error(f'database.adminDB.create_role: {e.__class__.__name__}, {e}')            
        raise      

def create_roles():
    with shareds.driver.session() as session:
        for role in ROLES:
            try:    
                session.write_transaction(create_role, role)
                print(role['name'])
            except Exception as e:
                logging.error(f'database.adminDB.create_roles: {e.__class__.__name__}, {e}')            
                continue

        print('Roles initialized')


def user_exists(name):
    print(f'Check the existense of the {name} user')
    num_of_users = 0  
    for result in shareds.driver.session().run(SetupCypher.user_check_existence, username=name):
        num_of_users = result[0]
    return(num_of_users > 0)    

def profile_exists(name):
    print(f'Check the existense of {name} profile')
    num_of_users = 0  
    for result in shareds.driver.session().run(SetupCypher.profile_check_existence, username=name):
        num_of_users = result[0]
    return(num_of_users > 0)    


def build_master_user():
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
            
def create_master_user():
    master_user = build_master_user()
    with shareds.driver.session() as session: 
        try:
            session.run(SetupCypher.master_create, master_user) 
        except Exception as e:
            logging.error(f'database.adminDB.create_master_user: {e.__class__.__name__}, {e}')            
            return
    logger.info('Master user account created')    

def build_guest_user():
    with shareds.app.app_context():
        return(shareds.user_model( 
            username = 'guest', 
            password = sec_utils.hash_password(shareds.app.config['GUEST_USER_PASSWORD']),  
            email = shareds.app.config['GUEST_USER_EMAIL'], 
            name = 'Vieraileva käyttäjä',
            language = 'fi',  
            is_active = True,
            confirmed_at = datetime.now().timestamp()*1000, 
            roles= ['guest'],
            last_login_at = datetime.now().timestamp()*1000,
            current_login_at = datetime.now().timestamp()*1000,
            last_login_ip = '127.0.0.1',  
            current_login_ip = '127.0.0.1',
            login_count = 0 )           
               )
                        
def create_guest_user():
    guest = build_guest_user()
    user = shareds.user_datastore.put(guest)                
    if user:
        logger.info('Guest user account created') 
    else:       
        logger.error('Guest user account not created')

def create_single_profile(name):
    """ Create the profile, where approved Audit nodes shall be connected.

        There is no User node for this UserProfile.
    """
    attr = {"numSessions":0,
            "lastSessionTime":0,
            "username":name}
    with shareds.driver.session() as session: 
        try:
            session.run(SetupCypher.single_profile_create, attr=attr)
        except Exception as e:
            logger.error("database.adminDB.create_single_profile"
                         f" Failed {e.__class__.__name__} {e.message}")
            return
    logger.info(f'Profile {name} created')    


def create_role_constraints():
    with shareds.driver.session() as session: 
        try:
            session.run(SetupCypher.set_role_constraint)
        except Exception as e:
            logging.error(f'database.adminDB.create_role_constraints: {e.__class__.__name__}, {e}')            
            return
    logger.info('Role constraints created')


def create_user_constraints():
    with shareds.driver.session() as session: 
        try:  
            session.run(SetupCypher.set_user_constraint1)
            session.run(SetupCypher.set_user_constraint2)  
        except Exception as e:
            logging.error(f'database.adminDB.create_user_constraints: {e.__class__.__name__}, {e}')            
            return
    logger.info('User constraints created')
    

def create_allowed_email_constraints():
    with shareds.driver.session() as session: 
        try:  
            session.run(SetupCypher.set_allowed_email_constraint)  
        except Exception as e:
            logging.error(f'database.adminDB.create_allowed_email_constraints: {e.__class__.__name__}, {e}')            
            return
    logger.info('Allowed email constraints created')


def check_contraints(needed:dict):
    # Check which UNIQUE contraints are missing from given nodes and parameters.
    # Returns a set of missing constraints
    import re
    p = re.compile(":(\S*)(\s.*\.)(\w+)")
    #print(needed)
    with shareds.driver.session() as session:
        result = session.run("CALL db.constraints")
        for record in result:
            # "CONSTRAINT ON ( user:User ) ASSERT (user.email) IS UNIQUE"
            desc = record[1]
            x = p.search(desc)
            label = x.group(1)
            prop = x.group(3)
            if label in needed.keys():
                if prop in needed[label]:
                    needed[label].remove(prop)
                    print(f'constraint {label}.{prop} ok')
    #print(f'Missing contraints: {needed}')
    for label,props in needed.items():
        for prop in props:
            create_unique_constraint(label, prop)
    return

def create_lock_and_constraint():
    # can be created multiple times!
    with shareds.driver.session() as session:
        record = session.run("match (n:Lock) return count(*) as exists limit 1").single()
        if record[0] == 0:
            # Create first Lock node and contraint
            session.run("merge (lock:Lock {id:$lock_id}) set lock.locked = true", 
                        lock_id="batch_id")
            session.run("create constraint on (l:Lock) assert l.id is unique")
            print(' - One Lock created')


def create_unique_constraint(label, prop):
    ' Create given contraint for given label and property.'
    with shareds.driver.session() as session:
        query = f"create constraint on (n:{label}) assert n.{prop} is unique"
        try:  
            session.run(query)  
        except Exception as e:
            logger.error(f'database.adminDB.create_unique_constraint: {e.__class__.__name__} {e}' )
            raise
        print(f'Unique contraint for {label}.{prop} created')
    return

def set_confirmed_at():
    """
    For some reason many User nodes were missing the 'confirmed_at'
    property. This code creates the missing properties by copying
    it from the corresponding 'Allowed_email' node. The actual value
    is in fact not very important.
    """
    stmt = """
        match (allowed:Allowed_email),(user:User) 
        where not exists(user.confirmed_at) and 
              allowed.allowed_email=user.email
        return count(user) as count
    """
    result = shareds.driver.session().run(stmt).single()
    count = result['count']
    print(f"Setting confirmed_at for {count} users") 

    stmt = """
        match (allowed:Allowed_email),(user:User) 
        where not exists(user.confirmed_at) and 
              allowed.allowed_email=user.email
        set user.confirmed_at = allowed.confirmed_at
    """
    shareds.driver.session().run(stmt)


def initialize_db():
    # Fix changed schema
    do_schema_fixes()
    
    if not roles_exist():
        create_role_constraints()
        create_roles()
        
    if not user_exists('master'):
        create_user_constraints()
        create_master_user()
        create_allowed_email_constraints()
        
    if not user_exists('guest'):
        create_guest_user()

    if not profile_exists('_Stk_'):
        create_single_profile('_Stk_')
        # Create Lock, too
        create_lock_and_constraint()

    needed_constraints = {
        "Allowed_email":{"allowed_email"},
        "Citation":{"uuid"},
        "Event":{"uuid"},
        "Family":{"uuid"},
        "Media":{"uuid"},
        "Note":{"uuid"},
        "Person":{"uuid"},
        "Place":{"uuid"},
        "Repository":{"uuid"},
        "Role":{"name"},
        "Source":{"uuid"},
        "User":{"email","username"}
    }
    check_contraints(needed_constraints)
    return  # ============================= test only

    #create_uuid_constraints()
    #set_confirmed_at()


