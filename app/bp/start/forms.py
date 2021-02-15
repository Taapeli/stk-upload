#   Isotammi Geneological Service for combining multiple researchers' results.
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
    
