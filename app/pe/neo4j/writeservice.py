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
