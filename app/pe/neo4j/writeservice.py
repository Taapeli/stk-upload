'''
Created on Jan 12, 2021

@author: kari
'''

from time import strptime
import traceback

from pe.neo4j.cypher.cy_event import CypherEvent
from bl.dates import DateRange
from bl.event import EventBl

def parsedate(datestr, attrs):
    try:
        t = strptime(datestr, "%d.%m.%Y")
        s = f"{t.tm_year:}-{t.tm_mon:02d}-{t.tm_mday:02d}"
        daterange = DateRange(s)
        attrs.update(daterange.for_db())
    except:
        traceback.print_exc()

class Neo4jWriteService:
    ''' Methods for accessing Neo4j database.
    '''
    def __init__(self, driver):
        self.driver = driver

    def dr_update_event(self, uuid, data):
        with self.driver.session(default_access_mode='WRITE') as session:
            attrs = {}
            attrs["description"] = data["description"]
            parsedate(data["date"], attrs)
            record = session.run(CypherEvent.update_event, uuid=uuid, attrs=attrs).single()
            eventnode = record['e']
            return EventBl.from_node(eventnode)
