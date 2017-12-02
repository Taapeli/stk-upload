from flask import Flask, current_app, session, render_template, request, g 
from flask_security import Security, UserMixin, RoleMixin, login_required, roles_accepted, roles_required, current_user
from flask_security.forms import RegisterForm, ConfirmRegisterForm, Required, StringField
from flask_security.utils import _
from flask_mail import Mail
from stk_security.models.neo4jengine import Neo4jEngine  
from stk_security.models.neo4juserdatastore import Neo4jUserDatastore
from models.gen.dates import DateRange  # Aikaväit ym. määreet
from datetime import datetime 
import shareds

class Role(RoleMixin):
    id = ''
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
       
    def __init__(self, **kwargs):
        self.email = kwargs['email']
        self.username = kwargs.get('username')
        self.name = kwargs.get('name')
        self.language = kwargs.get('language')   
        self.password = kwargs['password']
        self.is_active = True
        self.confirmed_at = None
        self.roles = kwargs['roles']

class ExtendedConfirmRegisterForm(ConfirmRegisterForm):
    username = StringField('Username', validators=[Required('Username required')])
    name = StringField('Name', validators=[Required('Name required')])
    language = StringField('Language', validators=[Required('Language required')])


print('Stk-server init')
# Create app
app = Flask(__name__, instance_relative_config=True)
mail = Mail(app)
with app.app_context():
    # within this block, current_app points to app.
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
    user_datastore = Neo4jUserDatastore(db.driver, User, Role)
    shareds.user_datastore = user_datastore
    security = Security(app, user_datastore,
        confirm_register_form=ExtendedConfirmRegisterForm)
    shareds.security = security
    print('Security set up')
    @security.register_context_processor
    def security_register_processor():
        return {"username": _("Käyttäjänimi"), "name": _("Nimi"), "language": _("Kieli")}


    
    """ Application filter definitions 
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
    
    # Views
    
    #===========================================================================
    # @app.route('/', methods=['GET', 'POST'])
    # @login_required
    # def home():
    #     role_names = [role.name for role in current_user.roles]
    #     print('home ',current_user.name + ' logged in, roles ' + str(role_names))
    #     return render_template('/mainindex.html')
    #===========================================================================
     
    #===============================================================================
    # @app.route('/index', methods=['GET', 'POST'])
    # @login_required
    # def index():
    #     role_names = [role.name for role in current_user.roles]
    #     print('index ', current_user.name + ' logged in, roles ' + str(role_names))
    #     return render_template('/index.html')
    #===============================================================================
    
    #===============================================================================
    # @app.route('/register', methods=['GET', 'POST'])
    # def register():
    #     print('register')
    #     return render_template('/security/register_user.html')
    #===============================================================================
    
    #===============================================================================
    # @app.route('/logout', methods=['GET', 'POST'])
    # @login_required    
    # def logout():
    #     print(current_user.name + ' logging out')
    #     return render_template('/security/login_user.html')
    #===============================================================================
    
    #===============================================================================
    # @app.route('/forgot_password', methods=['GET', 'POST'])
    # def forgot_password():
    #     print(current_user.name + ' forgot password')
    #     return render_template('/security/forgot_password.html')
    #===============================================================================
    
