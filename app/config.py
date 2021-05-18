#   Isotammi Genealogical Service for combining multiple researchers' results.
#   Created in co-operation with the Genealogical Society of Finland.
#
#   Copyright (C) 2016-2021  Juha Mäkeläinen, Jorma Haapasalo, Kari Kujansuu, 
#                            Timo Nallikari, Pekka Valta
#   See the LICENSE file.

'''
Created on 17.11.2017

@author: TimNal

Sovelluksen toiminnallisuutta ohjaavat tiedot  
'''

from flask_babelex import lazy_gettext as _l
 
print('Reading application config.py')
DEBUG = False

SECURITY_REGISTERABLE = True
SECURITY_CONFIRMABLE = True
SECURITY_RECOVERABLE = True
SECURITY_TRACKABLE = True
#SECURITY_REGISTER_URL = '/register'
#SECURITY_SEND_CONFIRMATION_TEMPLATE = 'stk_security/send_confirmation.html' 

#SECURITY_USER_IDENTITY_ATTRIBUTES = ['email', 'username']
SECURITY_POST_LOGIN_VIEW = '/'
SECURITY_POST_LOGOUT_VIEW = '/'
#SECURITY_LOGIN_USER_TEMPLATE = 'security/login_user.html'
#SECURITY_REGISTER_USER_TEMPLATE = 'security/register_user.html'
#SECURITY_RESET_PASSWORD_TEMPLATE = 'security/reset_password.html'
#SECURITY_CHANGE_PASSWORD_TEMPLATE = 'security/change_password.html'
SECURITY_SEND_REGISTER_EMAIL = True

LANGUAGES = [("fi",_l("Finnish")),
             ("sv",_l("Swedish")),
             ("en",_l("English"))]

LANGS = [LANGUAGE[0] for LANGUAGE in LANGUAGES]

#DEFAULT_ROLE='admin'
EXPLAIN_TEMPLATE_LOADING=False   # True: explain Flask, if you like
from os import getcwd
APP_ROOT = getcwd() or 'None'
print('app.config: APP_ROOT "{}"'.format(APP_ROOT))
