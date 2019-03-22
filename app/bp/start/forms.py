from wtforms import StringField, SubmitField, SelectField, SelectMultipleField
from wtforms import BooleanField, DateTimeField, IntegerField, HiddenField, RadioField, TextAreaField
from wtforms.validators import InputRequired, Optional, Email, Length
from flask_wtf import FlaskForm
from flask_babelex import _
import shareds

class JoinForm(FlaskForm):
    strip_filter = lambda x: x.strip() if x else None
    name = StringField(_('Your name:'), 
                       [InputRequired()], 
                       description = _('Name of the user'))      
    email = StringField(_('Your email address:'), 
                        [InputRequired(), Email(), 
                         Length(min=1, max=100, message=_('Maximum 100 characters'))],
                        filters = [strip_filter],
                        description = _('Enter the email address'))
    language = SelectField( _('Language'), 
                        [Optional()],
                        choices=shareds.app.config.get('LANGUAGES'),
                        default=2,
                        description = _('Language')) 
    is_member = RadioField(_('Are you a member of the Genealogical Society of Finland?'), 
                        [Optional()],
                        choices=[
                            ("yes",_("Yes")),
                            ("no",_("No")),
                            ("dontknow",_("Don't know")),
                        ])
    years = StringField(_("How many years have you been doing genealogical research?"))
    software = StringField(_("What genealogy software are you mainly using?"))
    surnames = StringField(_("Which families/surnames are you mainly researching?"))
    places = StringField(_("Which places are you mainly researching?"))
    message = TextAreaField(_("Message:"))
                       

    submit = SubmitField(_('Send request'))
    
