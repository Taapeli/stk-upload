#   Isotammi Genealogical Service for combining multiple researchers' results.
#   Created in co-operation with the Genealogical Society of Finland.
#
#   Copyright (C) 2016-2021  Juha Mäkeläinen, Jorma Haapasalo, Kari Kujansuu, 
#                            Timo Nallikari, Pekka Valta
#
#   This program is free software: you can redistribute it and/or modify
#   it under the terms of the GNU General Public License as published by
#   the Free Software Foundation, either version 2 of the License, or
#   (at your option) any later version.
#
#   This program is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU General Public License for more details.
#
#   You should have received a copy of the GNU General Public License
#   along with this program.  If not, see <http://www.gnu.org/licenses/>.

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
from ui import jinja_filters
from wtforms import SelectField, SubmitField, BooleanField

from pe.neo4j.neo4jengine import Neo4jEngine
#from pe.neo4j.readservice import Neo4jReadService
#from database.models.neo4jengine import Neo4jEngine 
from database import accessDB

import shareds
from chkdate import Chkdate

from bp.stk_security.models.neo4juserdatastore import Neo4jUserDatastore
from bl.admin.models.user_admin import UserProfile
from bl.dates import DateRange  # Aikavälit ym. määreet
from datetime import datetime
#from ui.context import UserContext

import json
from flask_babelex import lazy_gettext as _l
from speaklater import _LazyString


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
        self.name = kwargs.get("name")
        self.description = kwargs.get("description")
#        self.timestamp = kwargs['timestamp']

    def __str__(self):
        """ Role name in ui language """
        return _(self.name)

    @classmethod
    def from_node(cls, node):
        # type: (Any) -> Root
        """Convert a Neo4j node to Role object."""
        obj = cls()
        obj.name = node.get("name", "")
        obj.description = node.get("description", "")
        return obj

    @staticmethod
    def has_role(name, role_list):
        ''' Check, if given role name exists in a list of Role objects.
        '''
        for role in role_list:
            if role == name or role.name == name:
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
    agree = False
    # View filtering option. Stored here for logging in scene pages
    current_context = "common"  # = ui.context.MATERIAL_COMMON

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
        self.agree = kwargs.get('agree')        

    def __str__(self):
        if self.roles:
            rolelist = []
            for i in self.roles:
                if isinstance(i, str):
                    # Got a Role name
                    rolelist.append(i)
                elif isinstance(i, Role):
                    # Got a Role object
                    rolelist.append(i.name)
            return f'setups.User {self.username} {rolelist}'
        else:
            return f'setups.User {self.username}, no roles'

    def has_role(self, role_name):
        """ Check if user has given role
        """
        for r in self.roles:
            if r.name == role_name:
                return True
        return False


# class UserProfile():
# See: bp.admin.models.user_admin.UserProfile

class LazyFormat(_LazyString):
    """Hack to enable lazy strings in string formatting"""
    def __init__(self, s, **params):   
        self.s = s
        self.params = params
    @property
    def value(self):
        return _l(self.s).format(**dict((name,_l(value)) for (name,value) in self.params.items()))  

class ExtendedLoginForm(LoginForm):

    email = StringField(_l('Email or Username'), validators=[Required('Email required') ])
    password = PasswordField(_l('Password'),
                             validators=[Required('Password required')])
    remember = BooleanField(_l('Remember Me'))
    submit = SubmitField(_l('Login'))



class ExtendedConfirmRegisterForm(ConfirmRegisterForm):

    email = StringField(_l('Email address'), validators=[Required('Email required') ])
    agree = BooleanField( LazyFormat(_("I have read and agree to the <a href='{terms_of_use_url}' target='esite'>{terms_of_use}</a>"),
                                  terms_of_use_url=_("http://wiki.isotammi.net/wiki/Isotammi_käyttöehdot"),
                                  terms_of_use=_("Terms of use"),
    ))
    password = PasswordField(_l('Password'),
                             validators=[Required('Password required')])
    submit = SubmitField(_l('Register'))
 
    def validate_agree(self, field):
        if not field.data:
            raise ValidationError(_l('Please indicate that you have read and agree to the Terms and Conditions'), 'error') 
        else:
            return True 

    def validate_email(self, field):
        user = shareds.user_datastore.get_user(field.data)
        if user:
            raise ValidationError(_l('Email has been reserved already'))

    def validate_username(self, field):
        user = shareds.user_datastore.get_user(field.data)
        if user:
            raise ValidationError(_l('Username has been reserved already'))

    username = StringField(_l('Username'), validators=[Required('Username required')])
    name = StringField(_l('Name'), validators=[Required('Name required')])
    language = SelectField(_l('Language'), 
                choices=shareds.app.config.get('LANGUAGES'),
                validators=[Required(_('Language required'))])

#============================== Start here ====================================

sysversion = Chkdate()  # Last application commit date or "Unknown"

print('Stk server setups') 
shareds.mail = Mail(shareds.app)
shareds.user_model = User
shareds.role_model = Role

if True:
    #
    #    A Neo4j database is selected as our datastore
    #
    # dataservice, readservice, readservice_tx -> Tietokantapalvelu
    #      driver -> Tietokanta-ajuri
    #
    # About database driver object:
    # https://neo4j.com/docs/api/python-driver/current/api.html#driver-object-lifetime
    #
    from pe.neo4j.updateservice import Neo4jUpdateService
    from pe.neo4j.writeservice import Neo4jWriteService
    from pe.neo4j.readservice import Neo4jReadService
    from pe.neo4j.readservice_tx import Neo4jReadServiceTx

    shareds.db = Neo4jEngine(shareds.app)
    shareds.driver  = shareds.db.driver
    shareds.dataservices = {
        "read":    Neo4jReadService,
        "read_tx": Neo4jReadServiceTx,
        "update":  Neo4jUpdateService,
        "simple":  Neo4jWriteService    # Without transaction
        }

    # Setup Flask-Security
    shareds.user_datastore = Neo4jUserDatastore(shareds.driver, User, UserProfile, Role)
    shareds.security = Security(shareds.app, shareds.user_datastore,
                                confirm_register_form=ExtendedConfirmRegisterForm,
                                login_form=ExtendedLoginForm)

print('Neo4j and security set up')

# Check and initiate important nodes and constraints and schema fixes.
accessDB.initialize_db() 


@shareds.security.register_context_processor
def security_register_processor():
    return {"username": _('User name'), "name": _('Name'), "language": _('Language')}


""" 
    Jinja application filter definitions.
    Example: {{ size|int_thousands }}
"""

@shareds.app.template_filter('pvt')
def _jinja2_filter_dates(dates):    # Not in use!
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

@shareds.app.template_filter('isodatetime') # Not in use
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

@shareds.app.template_filter('format_ts')
def _jinja2_filter_timestamp_ms(ms):
    """ Given term is translated depending of var_name name.

        Example: event type code e.type in jinja template: {{e.type|transl('evt')}}
    """
    return jinja_filters.timestamp_ms(ms)

@shareds.app.template_filter('is_list') # Not in use?
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
