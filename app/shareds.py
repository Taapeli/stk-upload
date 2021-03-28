#   Isotammi Genealogical Service for combining multiple researchers' results.
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
# Database services (default Neo4j)
db = None           # pe.neo4j.Neo4jEngine instance
driver = None       # = shareds.db.driver, GraphDatabase.driver instance
dataservices = {}   # Database service modules for read, read_tx, update
# readservice = None      # pe.neo4j.update_serv.Neo4jReadService instance
# readservice_tx = None   # pe.neo4j.update_serv.Neo4jReadServiceTx instance
# dataservice = None      # pe.neo4j.update_serv.Neo4jDataService instance
datastore = None    # pe.db_writer.DbWriter instance – stk data services
user_datastore = None

user_model = None
role_model = None
allowed_email_model = None

tdiff = 0.0         # Elapsed time of previous step, if any

DEFAULT_ROLE = 'member'    # Value overridden with configuration in application setup
PROGRESS_UPDATE_RATE = 15  # seconds to update progress data in UI

PRIVACY_LIMIT = 0       #Todo: Use bl.person.PRIVACY_LIMIT (?)
