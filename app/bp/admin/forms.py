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
Created on 3.1.2018

@author: TimNal
'''

from wtforms import StringField, SubmitField, SelectField, SelectMultipleField, BooleanField, DateTimeField, IntegerField, HiddenField
from wtforms.validators import InputRequired, Optional, Email, Length
from flask_wtf import FlaskForm
from flask_babelex import _
from flask_babelex import lazy_gettext as _l
import shareds

class UpdateUserForm(FlaskForm):

    """
    id = 0
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
    """

    strip_filter = lambda x: x.strip() if x else None
    id = HiddenField(_l('id:'), 
        description = _('Id of the user'))  
    email = StringField(_l('Email Address:'), 
        filters = [strip_filter],
        description = _('Email address'))
    username = StringField(_l('Username:'), 
        description = _('User name'))  
    name = StringField(_l('Name:'), 
        description = _('Name of the user'))      
    language = SelectField( _l('Language'), [Optional()],
            choices=shareds.app.config.get('LANGUAGES'),
            default=2,
            description = _('Language')) 
    is_active = BooleanField(_l('Is active'), [Optional()],
        description = _('Active / passive user')) 
    roles = SelectMultipleField(_l('Roles'), 
                choices=[
                   ("gedcom",_("Gedcom-files")),
                   ("member",_("Member")),
                   ("research",_("Research")),
                   ("audit",_("Audit")),                      
                   ("admin",_("Admin")) ],
                description = _('Assigned roles')) 
    confirmed_at = DateTimeField(_l('Email confirmed time'), [Optional()],
        description = _('Time of email confirmation'))        
    last_login_at = DateTimeField(_l('Last login time'), [Optional()],
        description = _('Time of last login'))   
    last_login_ip = StringField(_l('Last login IP address'), [Optional()],
        description = _('IP address of last login'))    
    current_login_at = DateTimeField(_l('Current login time'), [Optional()],
        description = _('Time of current login'))   
    current_login_ip = StringField(_l('Current login IP address'), [Optional()],
        description = _('IP address of current login'))
    login_count = IntegerField(_l('Login count'), [Optional()],
        description = _('Count of logins'))
    
    submit = SubmitField(_l('Update user'))
    approve = SubmitField(_l('Approve user'))
    

        
class UpdateUserProfilelForm(FlaskForm):
    
    """
    email = ''
    name = ''
    language = ''
    default_role = ''
    approved = False
    confirmed_at = None
    """

    strip_filter = lambda x: x.strip() if x else None
    email = StringField(_('Email Address:'), 
        filters = [strip_filter],
        description = _('Email address'))
    name = StringField(_('Name:'), 
        description = _('Name of the user'))      
    language = SelectField( _('Language'), [Optional()],
            choices=shareds.app.config.get('LANGUAGES'),
            default=2,
            description = _('Language')) 
    approved = BooleanField(_('Approved'), [Optional()],
        description = _('Approved / pending user')) 
    role = SelectField(_('Role'), 
                choices=[
                   ("gedcom",_("Gedcom-files")),
                   ("member",_("Member")),
                   ("research",_("Research")),
                   ("audit",_("Audit")),                      
                   ("admin",_("Admin")) ],
                description = _('Assigned role choices')) 
    confirmed_at = DateTimeField(_('Email confirmed time'), [Optional()],
        description = _('Time of registered email confirmation'))        


    submit = SubmitField(_('Update allowed email'))
                