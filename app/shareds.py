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
db = None           # pe.neo4j.Neo4jEngine instance
driver = None       # = shareds.db.driver, GraphDatabase.driver instance
datastore = None    # pe.db_writer.DbWriter instance – stk data services
user_datastore = None
allowed_email_model = None
tdiff = 0.0         # Elapsed time of previous step, if any
#current_neo4j = None # NOT USED?

user_model = None
role_model = None

DEFAULT_ROLE = 'member'    # Value overridden with configuration in application setup
PROGRESS_UPDATE_RATE = 15  # seconds to update progress data in UI

PRIVACY_LIMIT = 0       #Todo: Use bl.person.PRIVACY_LIMIT (?)
