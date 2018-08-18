'''
Created on 26.11.2017

@author: Timo

Arvot asetetaan järjestelmän  setups.py:ssä
'''
app = None
security = None
mail = None
db = None
driver = None
user_datastore = None
tdiff = 0.0     # Elapsed time of previous step, if any

DEFAULT_ROLE = 'member'    # Value overridden with configuration in application setup