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
Created on Jan 12, 2021

@author: kari
'''

from time import strptime
import traceback

from bl.base import Status
from bl.dates import DateRange
from bl.event import EventBl

from pe.neo4j.cypher.cy_event import CypherEvent
from pe.neo4j.cypher.cy_person import CypherPerson

def parsedate(datestr, attrs):
    try:
        t = strptime(datestr, "%d.%m.%Y")
        s = f"{t.tm_year:}-{t.tm_mon:02d}-{t.tm_mday:02d}"
        daterange = DateRange(s)
        attrs.update(daterange.for_db())
        return True
    except:
        traceback.print_exc()
        return False

class Neo4jWriteService:
    ''' Methods for accessing Neo4j database.
    '''
    def __init__(self, driver):
        self.driver = driver

    def dr_update_event(self, uuid, data):
        with self.driver.session(default_access_mode='WRITE') as session:
            statusText = ""
            attrs = {}
            attrs["description"] = data["description"]
            ok = parsedate(data["date"], attrs)
            if not ok:
                statusText = "Invalid date"
            record = session.run(CypherEvent.update_event, uuid=uuid, attrs=attrs).single()
            if not record:
                statusText = "Database update failed"
                return {"item":None, "status":Status.ERROR, "statusText":statusText}
            eventnode = record['e']
            event = EventBl.from_node(eventnode)
            return {"item":event, "status":Status.OK, "statusText":statusText}

    def dr_set_primary_name(self, uuid, old_order):
        with self.driver.session(default_access_mode='WRITE') as session:
            record = session.run(CypherPerson.set_primary_name, uuid=uuid, old_order=old_order).single()

    def dr_set_name_orders(self, uid_order_list):
        with self.driver.session(default_access_mode='WRITE') as session:
            for order, uid in enumerate(uid_order_list): 
                print("==>",order,uid)
                record = session.run(CypherPerson.set_name_order, uid=uid, order=order).single()
