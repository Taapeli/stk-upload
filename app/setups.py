'''
Setups imported from bp.admin.routes.

    Classes
    - User management classes: Role, User
    - Extended forms for login and register

    Jinja2 filters
    - Various filters methods

    Import routes

Created on 2016 or earlier

@author: timnal
'''

from flask_security import Security, UserMixin, RoleMixin
from flask_security.forms import LoginForm, ConfirmRegisterForm, Required, StringField, PasswordField, ValidationError
from flask_security.utils import _
from flask_mail import Mail
from templates import jinja_filters
from wtforms import SelectField, SubmitField, BooleanField

from database.models.neo4jengine import Neo4jEngine 
from database import adminDB
import shareds
from chkdate import Chkdate

from bp.stk_security.models.neo4juserdatastore import Neo4jUserDatastore
from bp.admin.models.user_admin import UserAdmin, UserProfile, Allowed_email
from models.gen.dates import DateRange  # Aikavälit ym. määreet
from datetime import datetime
from ui.user_context import UserContext

#import logging
#from flask_login.utils import current_user
#from flask.globals import session
import json
from flask_babelex import lazy_gettext as _l


"""
    Classes to create user session.
    See: database.cypher_setup.SetupCypher
"""
       
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

    def __str__(self):
        """ Role name in ui language """
        return _(self.name)

    @staticmethod
    def has_role(name, role_list):
        '''
            Check, if given role name exists in a list of Role objects
        '''
        for role in role_list:
            if role.name == name:
                return True
        return False


class User(UserMixin):
    """ Object describing distinct user security properties.
    """
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
    # View filtering option. Stored here for logging in scene pages
    current_context = UserContext.ChoicesOfView.COMMON

    def __init__(self, **kwargs):
        if 'id' in kwargs:
            self.id = kwargs['id']
        self.email = kwargs['email']
        self.username = kwargs.get('username')
        self.name = kwargs.get('name')
        self.language = kwargs.get('language')   
        self.password = kwargs.get('password')
        self.is_active = kwargs.get('is_active')
        self.confirmed_at = kwargs.get('confirmed_at')
        self.roles = kwargs['roles']
        self.last_login_at = kwargs.get('last_login_at')
        self.last_login_ip = kwargs.get('last_login_ip')        
        self.current_login_at = kwargs.get('current_login_at')
        self.current_login_ip = kwargs.get('current_login_ip')
        self.login_count = kwargs.get('login_count')        

    def is_showing_common(self):
        """ Is showing common, approved data only?
        """
        return not (self.current_context & UserContext.ChoicesOfView.OWN)


# class UserProfile():
# See: bp.admin.models.user_admin.UserProfile

     
class ExtendedLoginForm(LoginForm):

    email = StringField(_l('Email or Username'), validators=[Required('Email required') ])
    password = PasswordField(_l('Password'),
                             validators=[Required('Password required')])
    remember = BooleanField(_l('Remember Me'))
    submit = SubmitField(_l('Login'))

class ExtendedConfirmRegisterForm(ConfirmRegisterForm):

    email = StringField(_l('Email address'), validators=[Required('Email required') ])
    agree = BooleanField( _l("I have read and agree the <a href='static/termsofuse.html'>Terms of use</a>"))
    password = PasswordField(_l('Password'),
                             validators=[Required('Password required')])
    submit = SubmitField(_l('Register'))
 
    def validate_agree(self, field):
        if not field.data:
            raise ValidationError(_('Please indicate that you have read and agree to the Terms and Conditions'), 'error') 
        else:
            return True 

    def validate_email(self, field):
        allowed_email = UserAdmin.find_allowed_email(field.data)
        if allowed_email:
            if allowed_email.confirmed_at != None:
                raise ValidationError(_('Email address has been confirmed earlier'))
            elif (allowed_email.creator == 'system') and not allowed_email.approved:
                raise ValidationError(_('Email address has not been approved yet'))             
#            if (allowed_email.creator != 'system') or allowed_email.approved:
            else: 
                return True
        raise ValidationError(_('Email address must be an authorized one')) 

    def validate_username(self, field):
        user = shareds.user_datastore.get_user(field.data)
        if user:
            raise ValidationError(_('Username has been reserved already'))

    username = StringField(_l('Username'), validators=[Required('Username required')])
    name = StringField(_l('Name'), validators=[Required('Name required')])
    language = SelectField(_l('Language'), 
                choices=shareds.app.config.get('LANGUAGES'),
                validators=[Required(_('Language required'))])

#============================== Start here ====================================

shareds.mail = Mail(shareds.app)
shareds.db = Neo4jEngine(shareds.app)
shareds.driver  = shareds.db.driver

shareds.user_model = User
shareds.role_model = Role

print('Stk server setups') 
sysversion = Chkdate()  # Last application commit date or "Unknown"

# Setup Flask-Security
shareds.user_datastore = Neo4jUserDatastore(shareds.driver, User, UserProfile, Role)
shareds.allowed_email_model = Allowed_email
shareds.security = Security(shareds.app, shareds.user_datastore,
    confirm_register_form=ExtendedConfirmRegisterForm,
    login_form=ExtendedLoginForm)

print('Security set up')

@shareds.security.register_context_processor
def security_register_processor():
    return {"username": _('User name'), "name": _('Name'), "language": _('Language')}

adminDB.initialize_db() 


""" 
    Jinja application filter definitions 
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

@shareds.app.template_filter('isodatetime')
def _jinja2_filter_datetime(datetime, fmt=None):
    """ Datetime ISO-muotoon ilman sekunnin osia """
    if datetime == None:
        return ""
    try:
        s = datetime.strftime('%Y-%m-%d %H:%M:%S')
        return s
    except:
        return "Error"

@shareds.app.template_filter('int_thousands')
def _jinja2_filter_int_thousands(i):
    """ Integer presented with space as thousands separator '1 000 000'. """
    if isinstance(i, int):
        return format(i, ",").replace(',',' ')
    else:
        return str(i)


@shareds.app.template_filter('transl')
def _jinja2_filter_translate(term, var_name):
    """ Given term is translated depending of var_name name.

        Example: event type code e.type in jinja template: {{e.type|transl('evt')}}
    """
    return jinja_filters.translate(term, var_name)

@shareds.app.template_filter('is_list')
def _is_list(value):
    return isinstance(value, list)

@shareds.app.template_filter('app_date')
def app_date(value):
    ''' Application date from git status.
    '''
    if value == 'git':
        return sysversion.revision_time()
    elif value == 'app':
        # Set the value in the beginning of this file
        return sysversion.revision_date()
    return 'Not defined'

@shareds.app.template_filter('logcontent')
def logcontent(row):
    ''' Create an Application log content from a json row.
    '''
    s = ""
    sep = ""
    row = json.loads(row)
    for name,value in sorted(row.items()):
        if name.startswith("_"): continue
        s += f"{sep}{name}={repr(value)}"
        sep = " "
    return s

#------------------------  Load Flask routes file ------------------------------

# DO NOT REMOVE (ON käytössä vaikka varoitus "unused import")
import routes
