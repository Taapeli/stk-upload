# coding: utf-8  

from datetime import datetime
import logging
logger = logging.getLogger('stkserver') 
from neo4j.exceptions import CypherSyntaxError, ConstraintError, CypherError
from flask_security import utils as sec_utils
import shareds
from .cypher_setup import SetupCypher

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
    except CypherError as cex:
        logger.error('CypherError in create_role ' + cex.message)
    except ConstraintError as cex:
        logger.error('ConstraintError in create_role ' + cex.message)
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


def user_exists(name):
    print(f'Check the existense of the {name} user')
    num_of_users = 0  
    for result in shareds.driver.session().run(SetupCypher.user_check_existence, username=name):
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
            
def create_master_user(master_user):
    master_user = build_master_user()
    with shareds.driver.session() as session: 
        try:
            session.run(SetupCypher.master_create, master_user) 
        except CypherSyntaxError as cex:
            logger.error('CypherSyntaxError in create_master ' + cex.message)
            return
        except CypherError as cex:
            logger.error('CypherError in create_master ' + cex.message)
            return
        except ConstraintError as cex:
            logger.error('ConstraintError in create_master ' + cex.message)
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

def create_role_constraints():
    with shareds.driver.session() as session: 
        try:
            session.run(SetupCypher.set_role_constraint)
        except CypherError as cex:
            logger.error('CypherError in create_role_constraints: ' + cex.message)
            return
        except ConstraintError as cex:
            logger.error('ConstraintError in create_role_constraints: ' + cex.message)
            return
    logger.info('Role constraints created')


def create_user_constraints():
    with shareds.driver.session() as session: 
        try:  
            session.run(SetupCypher.set_user_constraint1)
            session.run(SetupCypher.set_user_constraint2)  
        except CypherSyntaxError as cex:
            logger.error('ConstraintError in create_user_constraints: ' + cex.message)
            return
        except CypherError as cex:
            logger.error('ConstraintError in create_user_constraints: ' + cex.message)
            return
        except ConstraintError as cex:
            logger.error('ConstraintError in create_user_constraints: ' + cex.message)
            return
    logger.info('User constraints created')
    

def create_allowed_email_constraints():
    with shareds.driver.session() as session: 
        try:  
            session.run(SetupCypher.set_allowed_email_constraint)  
        except CypherSyntaxError as cex:
            logger.error('ConstraintError in create_allowed_email_constraints: ' + cex.message)
            return
        except CypherError as cex:
            logger.error('ConstraintError in create_allowed_email_constraints: ' + cex.message)
            return
        except ConstraintError as cex:
            logger.error('ConstraintError in create_allowed_email_constraints: ' + cex.message)
            return
    logger.info('Allowed email constraints created')

def do_schema_fixes():
    """ Search current obsolete terms in schema and fix them.
    
        #TODO: Muokataan tätä aina kun skeema muuttuu (tai muutos on ohi)
    """
    if True:
        if not role_exists("guest"):
            with shareds.driver.session() as session:
                try:    
                    session.write_transaction(create_role, ROLES[0])
                    print("Guest role added") 
                except CypherSyntaxError as cex:
                    print('Session ', cex)
                except CypherError as cex:
                    print('Session ', cex)
                except ConstraintError as cex:
                    print('Session ', cex)
                                  
        if not user_exists("guest"):
            guest = build_guest_user()
            shareds.user_datastore.put(guest)
            print("Guest user added")            
    else:    
        print(f"adminDB.do_schema_fixes: none")
    return

    change_HIERARCY_to_IS_INSIDE = """
MATCH (a) -[r:HIERARCY]-> (b)
    MERGE (a) -[rr:IS_INSIDE]-> (b)
        set rr = {datetype:r.datetype, date1:r.date1, date2:r.date2}
    DELETE r
RETURN count(rr)"""
    change_userName_to_username = """
match (u:UserProfile) where exists(u.userName)
    set u.username = u.userName
    set u.userName = null
return count(u)"""
    change_Repocitory_to_Repository = """
match (a:Repocitory)
    set a:Repository
    remove a:Repocitory
return count(a)"""
    change_Family_dates = """
match (f:Family) where f.datetype=3 and not exists(f.date1)
    set f.datatype = 1
    set f.data1 = f.data2
return count(f)"""
    change_wrong_supplemented_direction = """
MATCH (u:User)<-[r:SUPPLEMENTED]-(p:UserProfile) 
    DELETE r 
    CREATE (u) -[:SUPPLEMENTED]-> (p)
return count(u)"""

    with shareds.driver.session() as session: 
        try:
            result = session.run(change_HIERARCY_to_IS_INSIDE)
            cnt1 = result.single()[0]
            result = session.run(change_userName_to_username)
            cnt2 = result.single()[0]
            result = session.run(change_Repocitory_to_Repository)
            cnt3 = result.single()[0]
            result = session.run(change_Family_dates)
            cnt4 = result.single()[0]
            result = session.run(change_wrong_supplemented_direction)
            cnt5 = result.single()[0]

            print(f"adminDB.do_schema_fixes: changed {cnt1} relatios, {cnt2} properties, "
                  f"{cnt3} labels, {cnt4} families, {cnt5} supplemented directions")

        except Exception as e:
            logger.error(f"{e} in database.adminDB.do_schema_fixes")
            return

def create_lock_constraint():
    # can be created multiple times!
    shareds.driver.session().run( 
        "create constraint on (l:Lock) assert l.id is unique"
    )

def create_uuid_constraint():
    # can be created multiple times!
    shareds.driver.session().run( 
        "create constraint on (m:Media) assert m.uuid is unique"
    )

def initialize_db():
    # Fix chaanged schema
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

    create_lock_constraint()
    create_uuid_constraint()


