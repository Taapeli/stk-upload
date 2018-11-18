'''
Created on 3.1.2018

@author: TimNal
'''

from wtforms import StringField, SubmitField, SelectField, SelectMultipleField, BooleanField, DateTimeField, IntegerField, HiddenField
from wtforms.validators import InputRequired, Optional, Email, Length
from flask_wtf import FlaskForm
from flask_babelex import _

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
    id = HiddenField(_('id:'), 
        description = _('Id of the user'))  
    email = StringField(_('Email Address:'), 
        filters = [strip_filter],
        description = _('Email address'))
    username = StringField(_('Username:'), 
        description = _('User name'))  
    name = StringField(_('Name:'), 
        description = _('Name of the user'))      
    language = SelectField( _('Language'), [Optional()],
            choices=[
               ("fi",_("Finnish")),
               ("sv",_("Swedish")),
               ("en",_("English"))],
            default=2,
            description = _('Language')) 
    is_active = BooleanField(_('Is active'), [Optional()],
        description = _('Active / passive user')) 
    roles = SelectMultipleField(_('Roles'), 
                choices=[
#                   ("guest",_("Guest")),
                   ("member",_("Member")),
                   ("research",_("Research")),
                   ("audit",_("Audit")),                      
                   ("admin",_("Admin")) ],
                description = _('Assigned roles')) 
    confirmed_at = DateTimeField(_('Email confirmed time'), [Optional()],
        description = _('Time of email confirmation'))        
    last_login_at = DateTimeField(_('Last login time'), [Optional()],
        description = _('Time of last login'))   
    last_login_ip = StringField(_('Last login IP address'), [Optional()],
        description = _('IP address of last login'))    
    current_login_at = DateTimeField(_('Current login time'), [Optional()],
        description = _('Time of current login'))   
    current_login_ip = StringField(_('Current login IP address'), [Optional()],
        description = _('IP address of current login'))
    login_count = IntegerField(_('Login count'), [Optional()],
        description = _('Count of logins'))

    submit = SubmitField(_('Update user'))
    
class AllowedEmailForm(FlaskForm):
#    id = "register_email_form"
    strip_filter = lambda x: x.strip() if x else None
    allowed_email = StringField(_('Email Address:'), [InputRequired(), Email(), Length(min=1, 
        max=100, message=_('Maximum 100 characters'))],
        filters = [strip_filter],
        description = _('Enter the email address'))
    default_role = SelectField(_('Default role:'), 
                    choices=[
                       ("guest",_("Guest")),
                       ("member",_("Member")),
                       ("research",_("Research")),
                       ("audit",_("Audit")),                      
                       ("admin",_("Admin")),
                    ],
                description = _('Enter the default role'))  
    submit = SubmitField(_('Add user candidate'))
