from flask import Flask, current_app, session, render_template, request, g 
from flask_security import Security, UserMixin, RoleMixin, login_required, roles_accepted, roles_required, current_user
from flask_security.forms import RegisterForm, ConfirmRegisterForm, Required, StringField
from flask_security.utils import _
from flask_mail import Mail
from stk_security.models.neo4jengine import Neo4jEngine  
from stk_security.models.neo4juserdatastore import Neo4jUserDatastore
from models.gen.dates import DateRange  # Aikavälit ym. määreet
from datetime import datetime
from neo4j.exceptions import CypherSyntaxError, ConstraintError, CypherError
import logging
logger = logging.getLogger('stkserver') 
import shareds

class Role(RoleMixin):
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

class ExtendedConfirmRegisterForm(ConfirmRegisterForm):
    username = StringField('Username', validators=[Required('Username required')])
    name = StringField('Name', validators=[Required('Name required')])
    language = StringField('Language', validators=[Required('Language required')])

# Create app
app = Flask(__name__, instance_relative_config=True)
mail = Mail(app)
with app.app_context():
    # within this block, current_app points to app.
    print('Stk-server init')    
    print('Current application: ' + current_app.name)
    print('Application instance path: ' + app.instance_path)
    app.config.from_object('config')
    app.config.from_pyfile('config.py')
#    builtins.app = app
    shareds.app = app
    mail = Mail(app)
    shareds.mail = mail
    db = Neo4jEngine(app)
    shareds.driver = db.driver
   
#  Alusta sovellusosat
    import stk_run 

    # Setup Flask-Security
    user_datastore = Neo4jUserDatastore(db.driver, User, UserProfile, Role)
    shareds.user_datastore = user_datastore
    security = Security(app, user_datastore,
        confirm_register_form=ExtendedConfirmRegisterForm)
    shareds.security = security
    
    print('Security set up')
    @security.register_context_processor
    def security_register_processor():
        return {"username": _("Käyttäjänimi"), "name": _("Nimi"), "language": _("Kieli")}
      
#  Tarkista roolien olemassaolo
    print('Check the user roles')
    results = shareds.driver.session().run('MATCH (a:Role) RETURN COUNT(a)')
    for result in results:
        num_of_roles = result[0]
        break
    if num_of_roles == 0:
        #inputs
        ROLES = ({'level':'0', 'name':'guest', 'description':'Kirjautumaton käyttäjä rajoitetuin lukuoikeuksin'},
                 {'level':'1', 'name':'member', 'description':'Seuran jäsen täysin lukuoikeuksin'},
                 {'level':'2', 'name':'research', 'description':'Tutkija, joka voi päivittää omaa tarjokaskantaansa'},
                 {'level':'4', 'name':'audit', 'description':'Valvoja, joka auditoi ja hyväksyy ehdokasaineistoja'},
                 {'level':'8', 'name':'admin', 'description':'Ylläpitäjä kaikin oikeuksin'})
        
        role_create = (
            '''
            CREATE (role:Role 
                {level : $level, 
                name : $name, 
                description : $description,
                timestamp : $timestamp})
            '''
            ) 
#        print(role_create)
        #functions
        def create_constraints(tx):
            try:
                tx.run('CREATE CONSTRAINT ON (role:Role) ASSERT role.name IS UNIQUE')
                tx.commit() 
            except CypherSyntaxError as cex:
                print(cex)
        
        def create_role(tx, role):
            try:
                tx.run(role_create,
                    level=role['level'],    
                    name=role['name'], 
                    description=role['description'],
                    timestamp=str(datetime.now()) ) 
#                print(role['name'])
            except CypherSyntaxError as cex:
                print(cex)
            except CypherError as cex:
                print(cex)
            except ConstraintError as cex:
                print(cex)
#            print(role['name'])

        with shareds.driver.session() as session: 
            session.write_transaction(create_constraints)
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
    
 
    """ 
        Application filter definitions 
    """
    
    @app.template_filter('pvt')
    def _jinja2_filter_dates(daterange):
        """ Aikamääreet suodatetaan suomalaiseksi """
        return str(DateRange(daterange))
  
    @app.template_filter('pvm')
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
        
    @app.template_filter('timestamp')
    def _jinja2_filter_datestamp(time_str, fmt=None):
        """ Unix time 1506950049 suodatetaan selväkieliseksi 20.9.2017 """
        try:
            s = datetime.fromtimestamp(int(time_str)).strftime('%d.%m.%Y %H:%M:%S')
            return s
        except:
            return time_str
    
    
    @app.template_filter('transl')
    def _jinja2_filter_translate(term, var_name, lang="fi"):
        """ Given term is translated depending of var_name name.
            No language selection yet.
            
            'nt'  = Name types
            'evt' = Event types
            'role' = Event role
            'lt'  = Location types
            'lt_in' = Location types, inessive form
        'urlt' = web page type
        """    
    # Create a user to test with
    #===============================================================================
    # @app.before_first_request
    # def create_user():
    #     user_datastore.create_user(email='xxx@yyyyyyy.fi', password='password')
    #===============================================================================
    

