'''
Created on 3.1.2018

@author: TimNal
'''

from wtforms import StringField, SubmitField, SelectField
from wtforms.validators import InputRequired, Email, Length
from flask_wtf import FlaskForm
from flask_babelex import _
    
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