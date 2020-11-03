# coding: utf-8  

#from datetime import datetime
import logging
logger = logging.getLogger('stkserver')

#from neobolt.exceptions import ConstraintError # Obsolete
from neo4j.exceptions import ClientError, ConstraintError #,CypherSyntaxError
from flask_security import utils as sec_utils

import shareds
from .cypher_setup import SetupCypher
from .schema_fixes import do_schema_fixes

# All User roles here:
ROLES = ({'level':'0',  'name':'guest',    'description':'Rekisteröitymätön käyttäjä, näkee esittelysukupuun'},
         {'level':'1',  'name':'gedcom',   'description':'Kirjautunut käyttäjä, pääsee vain gedcom-muunnoksiin'},
         {'level':'2',  'name':'member',   'description':'Seuran jäsen täysin lukuoikeuksin'},
         {'level':'4',  'name':'research', 'description':'Tutkija, joka voi käsitellä omaa tarjokasaineistoaan'},
         {'level':'8',  'name':'audit',    'description':'Valvoja, joka auditoi ja hyväksyy gramps- ja tarjokasaineistoja'},
         {'level':'16', 'name':'admin',    'description':'Ylläpitäjä kaikin oikeuksin'},
         {'level':'32', 'name':'master',   'description':'Tietokannan pääkäyttäjä, ei sovellusoikeuksia'},
         {'level':'',   'name':'to_be_approved','description':'Käyttäjä joka odottaa hyväksymistä'}
)

# ====== Database schema ======
# increment this, if shcema must be updated
DB_SCHEMA_VERSION = 1
# =============================

#erase total database 
def delete_database(tx):
    tx.run(SetupCypher.delete_database)

def schema_updated():
    # Check, that Lock 'initiated' exists and schema is updated.
    result = shareds.driver.session().run(SetupCypher.check_lock_initiated)
    active_version = 0
    for record in result:
        active_version = record[0]
    return active_version == DB_SCHEMA_VERSION

def roles_exist():
    #  Tarkista roolien olemassaolo
    print(f'Check there are {len(ROLES)} user roles')
    num_of_roles = 0
    results = shareds.driver.session().run(SetupCypher.check_role_count)
    for result in results:
        num_of_roles = result[0]
    return(num_of_roles == len(ROLES))

def role_exists(name):
    # print(f'Check the existense of the {name} role')
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
        print(f'Role {role["name"]} created')
    except ClientError as e:
        #print(f'Role {role["name"]} exists')
        return
    except Exception as e:
        logging.error(f'database.adminDB.create_role: {e.__class__.__name__}, {e}')            
        raise      

def create_roles():
    with shareds.driver.session() as session:
        for role in ROLES:
            create_role(session, role)

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
             #'confirmed_at': datetime.now().timestamp()/1000, 
             'roles': ['master'],
             #'last_login_at': datetime.now().timestamp()/1000,
             #'current_login_at': datetime.now().timestamp()/1000,
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
            #confirmed_at = datetime.now().timestamp()*1000, 
            roles= ['guest'],
            #last_login_at = datetime.now().timestamp()*1000,
            #current_login_at = datetime.now().timestamp()*1000,
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
        except ClientError as e:
            msgs = e.message.split(',')
            print(f'Role constraint ok: {msgs[0]}')
            return
        except Exception as e:
            logging.error(f'database.adminDB.create_role_constraints: {e.__class__.__name__}, {e}')            
            return
    logger.info('Role constraints created')


def create_user_constraints():
    with shareds.driver.session() as session: 
        try:  
            session.run(SetupCypher.set_user_constraint1)
            session.run(SetupCypher.set_user_constraint2)  
        except ConstraintError:
            print(f'User constraints ok')
            return
        except ClientError:
            print(f'User constraints seems to be ok')
            return
        except Exception as e:
            logging.error(f'database.adminDB.create_user_constraints: {e.__class__.__name__}, {e}')            
            return
    logger.info('User constraints created')
    
def create_year_indexes():
    ''' Person node is indexed by two year properties.
    '''
    with shareds.driver.session() as session: 
        try:
            session.run(SetupCypher.index_year_birth_low)
            session.run(SetupCypher.index_year_death_high)  
        except ConstraintError:
            print(f'Person years indexes ok')
        except Exception as e:
            msgs = e.message.split(',')
            print(f'database.adminDB.create_year_indexes: {e.__class__.__name__}, {msgs[0]}')            
            return
    logger.info('Person years indexes created')
    

def check_constraints(needed:dict):
    # Create missing UNIQUE constraints from given nodes and parameters.

    for label,props in needed.items():
        for prop in props:
            create_unique_constraint(label, prop)
#     print(f'checked {n_ok} constraints ok')
    return

def create_lock_w_constraint():
    # Initial lock with schema version.
    with shareds.driver.session() as session:
        # Create first Lock node and contraint
        session.run(SetupCypher.update_lock, 
                    id="initiated", 
                    db_schema=DB_SCHEMA_VERSION, 
                    locked=False)
        print(f'Initial Lock (version {DB_SCHEMA_VERSION}) created')
        create_unique_constraint('Lock', 'id')
        return

def re_initiate_nodes_constraints_fixes():
    # Remove initial lock for re-creating nodes, constraints and schema fixes
    with shareds.driver.session() as session:
        session.run(SetupCypher.remove_lock_initiated)
        logger.info(f'database.adminDB.re_initiate_nodes_constraints_fixes: requested')
        print('Initial Lock removed')
        return

def create_unique_constraint(label, prop):
    ' Create given contraint for given label and property.'
    with shareds.driver.session() as session:
        query = f"create constraint on (n:{label}) assert n.{prop} is unique"
        try:  
            session.run(query)
            print(f'Unique constraint for {label}.{prop} created')
        except ClientError as e:
            msgs = e.message.split(',')
            print(f'Unique constraint for {label}.{prop} ok: {msgs[0]}')
            return
        except Exception as e:
            logger.error(f'database.adminDB.create_unique_constraint: {e.__class__.__name__} {e}' )
            raise
    return

def create_constraint(label, prop):
    ' Create given contraint for given label and property.'
    with shareds.driver.session() as session:
        query = f"create constraint on (n:{label})"
        try:  
            session.run(query)
            print(f'Constraint for {label}.{prop} created')
        except ClientError as e:
            msgs = e.message.split(',')
            print(f'Constraint for {label}.{prop} ok: {msgs[0]}')
            return
        except Exception as e:
            logger.error(f'database.adminDB.create_constraint: {e.__class__.__name__} {e}' )
            raise
    return

# def create_to_be_approved_role():
#     stmt = "create (r:Role{name:'to_be_approved',description:'Käyttäjä joka odottaa hyväksymistä'});"
#     try:
#         shareds.driver.session().run(stmt)
#         logger.info("Created Role 'to_be_approved'")
#     except ClientError: # already exists, ok
#         print(f"Role 'to_be_approved' already exists")

#------------------------------- Start here -----------------------------------

def initialize_db():
    '''
    Check and initiate important nodes and constraints and schema fixes,
    if (:Lock{id:'initiated'}) schema is not == database.adminDB.DB_SCHEMA_VERSION.
    ''' 
    if not schema_updated():
        logger.info('database.adminDB.initialize_db: checking roles, constraints '
                    f'and schema fixes (version {DB_SCHEMA_VERSION})' )

        if not roles_exist():
            create_role_constraints()
            create_roles()
            
        if not user_exists('master'):
            create_user_constraints()
            create_master_user()
            
        if not user_exists('guest'):
            create_guest_user()

        if not profile_exists('_Stk_'):
            create_single_profile('_Stk_')

        create_lock_w_constraint()

        create_year_indexes()

        constr_list = {
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
            "User":{"email", "username"}
        }
        check_constraints(constr_list)

        # Fix changed schema
        do_schema_fixes()

        # Done in database.adminDB.create_role_constraints()
        #create_to_be_approved_role()

