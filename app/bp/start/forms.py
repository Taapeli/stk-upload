from wtforms import StringField, SubmitField, SelectField, SelectMultipleField
from wtforms import BooleanField, DateTimeField, IntegerField, HiddenField, RadioField, TextAreaField
from wtforms.validators import InputRequired, Optional, Email, Length
from flask_wtf import FlaskForm
from flask_babelex import _
from flask_babelex import lazy_gettext as _l

import shareds

class JoinForm(FlaskForm):
    strip_filter = lambda x: x.strip() if x else None
    name = StringField(_l('Your name:'), 
                       [InputRequired()], 
                       description = _l('Name of the user'))      
    email = StringField(_l('Your email address:'), 
                        [InputRequired(), Email(), 
                         Length(min=1, max=100, message=_('Maximum 100 characters'))],
                        filters = [strip_filter],
                        description = _('Enter the email address'))
    language = SelectField( _l('Language'), 
                        [Optional()],
                        choices=shareds.app.config.get('LANGUAGES'),
                        default=2,
                        description = _('Language')) 
    GSF_membership = RadioField(_l('Are you a member of the Genealogical Society of Finland?'), 
                        [Optional()],
                        choices=[
                            ("yes",_l("Yes")),
                            ("no",_l("No")),
                            ("dontknow",_l("Don't know")),
                        ])
    research_years = StringField(_l("How many years have you been doing genealogical research?"))
    software = StringField(_l("What genealogy software are you mainly using?"))
    researched_names = StringField(_l("Which families/surnames are you mainly researching?"))
    researched_places = StringField(_l("Which places are you mainly researching?"))
    text_message = TextAreaField(_l("Message:"))
                       
    submit = SubmitField(_l('Send request'))
    
