'''
Created on 26.11.2017

@author: Timo

Arvot asetetaan järjestelmän  setups.py:ssä
'''

#from flask import session
import logging 
logger = logging.getLogger('stkserver')


app = None
babel = None
security = None
mail = None
db = None
driver = None
user_datastore = None
allowed_email_model = None
tdiff = 0.0     # Elapsed time of previous step, if any
current_neo4j = None

user_model = None
role_model = None

DEFAULT_ROLE = 'member'    # Value overridden with configuration in application setup

PRIVACY_LIMIT = 0