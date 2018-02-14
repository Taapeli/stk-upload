'''
Created on 3.1.2018

@author: TimNal
'''

from wtforms import StringField, SubmitField
from wtforms.validators import InputRequired, Email, Length
from flask_wtf import FlaskForm
    
class ListEmailsForm(FlaskForm):
#    id = "register_email_form"
    strip_filter = lambda x: x.strip() if x else None
    allowed_email = StringField('Email Address:', [InputRequired(), Email(), Length(min=1, 
        max=100, message='Maximum 100 characters')],
        filters = [strip_filter],
        description = 'Enter the email address')
    default_role = StringField('Default role:', [InputRequired(), Length(min=5, 
        max=10, message='Maximum 10 characters')],
        filters = [strip_filter],
        description = 'Enter the default role')    
    submit = SubmitField('Lisää käyttäjäehdokas')