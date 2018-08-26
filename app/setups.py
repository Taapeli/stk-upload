from flask import session
from flask_security import Security, UserMixin, RoleMixin
from flask_security.forms import ConfirmRegisterForm, Required, StringField, ValidationError
from wtforms import SelectField
from flask_security.utils import _
from flask_mail import Mail
from database.models.neo4jengine import Neo4jEngine 
from database.models.neo4juserdatastore import Neo4jUserDatastore
from models.gen.dates import DateRange  # Aikavälit ym. määreet
import shareds
from templates import jinja_filters

import os
from datetime import datetime
from neo4j.exceptions import CypherSyntaxError, ConstraintError, CypherError
import logging
logger = logging.getLogger('stkserver') 

#===================== Classes to create user session ==========================

class SetupCypher():
    """ Cypher classes for setup """

    set_user_constraint = '''
        CREATE CONSTRAINT ON (user:User) 
        ASSERT user.username IS UNIQUE
        ASSERT user.email IS UNIQUE'''
    
    role_create = '''
        CREATE (role:Role {level: $level, name: $name, 
                           description: $description, timestamp: $timestamp})'''

    master_check_existence = """
        MATCH  (user:User) 
        WHERE user.username = 'master' 
        RETURN COUNT(user)"""
        
    email_val = """
        MATCH (a:Allowed_email) WHERE a.allowed_email = $email RETURN COUNT(a)"""
        
    master_create = ('''
        MATCH  (role:Role) WHERE role.name = 'admin'
        CREATE (user:User 
            {username : $username, 
            password : $password,  
            email : $email, 
            name : $name,
            language : $language, 
            is_active : $is_active,
            confirmed_at : $confirmed_at, 
            roles : $roles,
            last_login_at : $last_login_at,
            current_login_at : $current_login_at,
            last_login_ip : $last_login_ip,
            current_login_ip : $current_login_ip,
            login_count : $login_count} )           
            -[:HAS_ROLE]->(role)
        ''' ) 

#     master_create = '''
#         MERGE (u:User) -[:HAS_ROLE]-> (r:Role {name:'master'})
#         ON CREATE 
#             SET u = { username: $username, password: $password, 
#                       email: $email, name: $name, language: $language,
#                       is_active: $is_active, confirmed_at: $confirmed_at,
#                       roles: $roles, last_login_at: $last_login_at,
#                       current_login_at: $current_login_at,
#                       last_login_ip: $last_login_ip, 
#                       current_login_ip: $current_login_ip,
#                       login_count: $login_count }'''

       
class Role(RoleMixin):
    """ Object describing any application user roles,
        where each user is linked
    """
    id = ''
    level = 0
    name = ''
    description = ''
    timestamp = None
    
    def __init__(self, **kwargs):
        self.name = kwargs['name']
        self.description = kwargs['description']
#        self.timestamp = kwargs['timestamp']


class User(UserMixin):
    """ Object describing distinct user security properties """
    id = ''
    email = ''
    username = ''   
    name = ''
    language = ''
    password = ''
    is_active = True
    confirmed_at = None
    roles = []
    last_login_at = None
    last_login_ip = ''    
    current_login_at = None
    current_login_ip = ''
    login_count = 0

    def __init__(self, **kwargs):
        self.email = kwargs['email']
        self.username = kwargs.get('username')
        self.name = kwargs.get('name')
        self.language = kwargs.get('language')   
        self.password = kwargs['password']
        self.is_active = True
        self.confirmed_at = kwargs.get('confirmed_at')
        self.roles = kwargs['roles']
        self.last_login_at = kwargs.get('last_login_at')
        self.last_login_ip = kwargs.get('last_login_ip')        
        self.current_login_at = kwargs.get('current_login_at')
        self.current_login_ip = kwargs.get('current_login_ip')
        self.login_count = kwargs.get('login_count')        


class UserProfile():
    """ Object describing dynamic user properties """
    uid = ''
    userName = ''
    numSessions = 0
    lastSessionTime = None  

    def __init__(self, **kwargs):
        self.numSessions = kwargs['numSessions']
        self.lastSessionTime = kwargs.get('lastSessionTime')

    def newSession(self):   
        self.numSessions += 1
        self.lastSessionTime = datetime.timestamp() 

     
class AllowedEmail():
    """ Object for storing an allowed user to register in """
    allowed_email = ''
    default_role = ''
    creator = ''
    created_at = ''
    registered_at = ''
       
    def __init__(self, **kwargs):
        self.allowed_email = kwargs['allowed_email']
        self.default_role = kwargs.get('default_role')        


class ExtendedConfirmRegisterForm(ConfirmRegisterForm):

    email = StringField('Email Address', validators=[Required('Email required') ])
#    email = StringField('Email', validators=[validators.InputRequired()])
    def validate_email(self, field):
        for result in shareds.driver.session().run(SetupCypher.email_val, email=field.data):
            num_of_emails = result[0]
        if num_of_emails == 0:
#        if not shareds.user_datastore.email_accepted(field.data):
            raise ValidationError('Email address must be an authorized one') 
        else:
            return True    
        
    username = StringField('Username', validators=[Required('Username required')])
    name = StringField('Name', validators=[Required('Name required')])
    #language = StringField('Language', validators=[Required('Language required')])
    language = SelectField('Language', 
                           choices=[
                               ("fi","suomi"),
                               ("sv","ruotsi"),
                               ("en","englanti"),
                            ],
                           validators=[Required('Language required')])

shareds.mail = Mail(shareds.app)
shareds.db = Neo4jEngine(shareds.app)
shareds.driver  = shareds.db.driver
print('Stk server setups') 

# Setup Flask-Security
shareds.user_datastore = Neo4jUserDatastore(shareds.driver, User, UserProfile, Role)
shareds.allowed_email_model = AllowedEmail
shareds.security = Security(shareds.app, shareds.user_datastore,
    confirm_register_form=ExtendedConfirmRegisterForm)

print('Security set up')
@shareds.security.register_context_processor
def security_register_processor():
    return {"username": _("Käyttäjänimi"), "name": _("Nimi"), "language": _("Kieli")}

#  Tarkista roolien olemassaolo
print('Check the user roles')
num_of_roles = 0
results = shareds.driver.session().run('MATCH (a:Role) RETURN COUNT(a)')
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
            tx.run('CREATE CONSTRAINT ON (role:Role) ASSERT role.name IS UNIQUE')
            tx.commit() 
        except CypherSyntaxError as cex:
            print(cex)
    
    def create_role(tx, role):
        try:
            tx.run(SetupCypher.role_create,
                level=role['level'],    
                name=role['name'], 
                description=role['description'],
                timestamp=str(datetime.now()) ) 
            tx.commit()            
#                print(role['name'])
        except CypherSyntaxError as cex:
            print(cex)
        except CypherError as cex:
            print(cex)
        except ConstraintError as cex:
            print(cex)
#            print(role['name'])

    with shareds.driver.session() as session: 
        session.write_transaction(create_role_constraints)
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

print('Check the master user')
num_of_masters = 0  
results =  shareds.driver.session().run(SetupCypher.master_check_existence)
for result in results:
    num_of_masters = result[0]

if num_of_masters == 0:
    default_master_params = {'username': 'master', 
             'password': 'taapeli',  
             'email': 'stk.sukututkimusseura@gmail.com', 
             'name': 'Stk-kannan pääkäyttäjä',
             'language': 'fi',  
             'is_active': True,
             'confirmed_at': datetime.now().timestamp(), 
             'roles': ['admin'],
             'last_login_at': datetime.now().timestamp(),
             'current_login_at': datetime.now().timestamp(),
             'last_login_ip': '127.0.0.1',
             'current_login_ip': '127.0.0.1',
             'login_count': 0            
             }
     

    def create_user_constraints(tx):
        try:
            tx.run(SetupCypher.set_user_constraint)
            tx.commit() 
        except CypherSyntaxError as cex:
            print(cex) 
            
    def create_master(tx, user):
        try:
            master_params = {
                'username': user['username'], 
                'password': user['password'],  
                'email': user['email'],
                'name': user['name'],
                'language': user['language'],  
                'is_active': True,
                'confirmed_at': user['confirmed_at'], 
                'roles': user['roles'],
                'last_login_at': user['last_login_at'],
                'current_login_at': user['current_login_at'],
                'last_login_ip': user['last_login_ip'],
                'current_login_ip': user['current_login_ip'],
                'login_count': user['login_count']
            }
            tx.run(SetupCypher.master_create, master_params) 
#                timestamp=str(datetime.now()) ) 
            tx.commit()            
#                print(role['name'])
        except CypherSyntaxError as cex:
            print(cex)
        except CypherError as cex:
            print(cex)
        except ConstraintError as cex:
            print(cex)

     
    print('Set the constraints and master user')
    with shareds.driver.session() as session: 
        session.write_transaction(create_user_constraints)

    with shareds.driver.session() as session:
        try: 
            session.write_transaction(create_master, default_master_params)
            print('Master user created')
           
        except CypherSyntaxError as cex:
            print('Session ', cex)
        except CypherError as cex:
            print('Session ', cex)
        except ConstraintError as cex:
            print('Session ', cex)


""" 
    Application filter definitions 
"""

@shareds.app.template_filter('pvt')
def _jinja2_filter_dates(dates):
    """ Aikamääreet suodatetaan suomalaiseksi """
    return str(DateRange(dates))

@shareds.app.template_filter('pvm')
def _jinja2_filter_date(date_str, fmt=None):
    """ ISO-päivämäärä 2017-09-20 suodatetaan suomalaiseksi 20.9.2017 """
    try:
        a = date_str.split('-')
        if len(a) == 3:
            p = int(a[2])
            k = int(a[1])
            return "{}.{}.{}".format(p,k,a[0]) 
        elif len(a) == 2:
            k = int(a[1])
            return "{}.{}".format(k,a[0]) 
        else:
            return "{}".format(a[0])
    except:
        return date_str
    
@shareds.app.template_filter('timestamp')
def _jinja2_filter_datestamp(time_str, fmt=None):
    """ Unix time 1506950049 suodatetaan selväkieliseksi 20.9.2017 """
    try:
        s = datetime.fromtimestamp(int(time_str)).strftime('%d.%m.%Y %H:%M:%S')
        return s
    except:
        return time_str


@shareds.app.template_filter('transl')
def _jinja2_filter_translate(term, var_name, lang="fi"):
    """ Given term is translated depending of var_name name
        and language [TODO]
    """
    return jinja_filters.translate(term, var_name, lang)

@shareds.app.template_filter('is_list')
def _is_list(value):
    return isinstance(value, list)

@shareds.app.template_filter('git_date')
def _git_date(value):
    return datetime.fromtimestamp(os.stat(".git/FETCH_HEAD").st_mtime).\
        strftime('%H:%M %d.%m.%Y')

#------------------------  Load Flask routes file ------------------------------
# (ON käytössä vaikka varoitus "unused import")

import routes
