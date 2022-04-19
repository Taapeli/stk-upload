import json
import time
import traceback

from flask_security import current_user

import shareds 
from models import util

syslog_cypher_init = """
    merge (start:Syslog{sentinel:'start'}) -[:NEXT]-> (end:Syslog{sentinel:'end'})
    return start,end
"""

syslog_cypher_exists = """
    match (row:Syslog) return count(row)
"""

syslog_cypher_write = """
    match (last:Syslog) -[r:NEXT]-> (end:Syslog{sentinel:'end'})   
    delete r
    merge (last)-[:NEXT]->
        (new:Syslog{
            type:$type,
            user:$user,
            msg:$msg,
            time:$time,
            timestr:$timestr})-[:NEXT]->(end)
    return new
"""

syslog_cypher_read_from_end = """
    match (row:Syslog) -[r:NEXT*1..20]-> (end:Syslog{sentinel:'end'})   
    where row.sentinel is null // Depricated: not exists(row.sentinel)
    return row
    order by row.time
"""

syslog_cypher_read_from_beginning = """
    match (beginning:Syslog{sentinel:'start'}) -[r:NEXT*1..20]-> (row:Syslog)   
    where row.sentinel is null
    return row
    order by row.time
"""

syslog_cypher_read_backward = """
    match(end:Syslog) where id(end) = $startid
    match (row:Syslog) -[r:NEXT*0..20]-> (end)   
    where row.sentinel is null
    return row
    order by row.time
"""

syslog_cypher_read_forward = """
    match(start:Syslog) where id(start) = $startid
    match (start:Syslog) -[r:NEXT*0..20]-> (row:Syslog)   
    where row.sentinel is null
    return row
    order by row.time
"""

def log(type,**kwargs):
    """ Create a Syslog event node with given arguments and timestamp.
    """
    try:
        user=current_user.username
    except:
        user = kwargs.get("user","")
    timestamp = time.time()
    timestr=util.format_timestamp(timestamp)
    msg = json.dumps(kwargs)
    try:
        shareds.driver.session().run(syslog_cypher_write, type=type, user=user,
                                     msg=msg, time=timestamp, timestr=timestr)
        return msg # Helps debugging
    except Exception:
        traceback.print_exc()
    
def readlog(direction="backward",startid=None):
    if not direction: direction = "backward"
    if direction == "backward":
        if startid:
            cypher_stmt = syslog_cypher_read_backward
        else:
            cypher_stmt = syslog_cypher_read_from_end
    if direction == "forward":
        if startid:
            cypher_stmt = syslog_cypher_read_forward
        else:
            cypher_stmt = syslog_cypher_read_from_beginning
    try:
        recs = []
        result = shareds.driver.session().run(cypher_stmt,
                                              direction=direction, startid=startid)
        for record in result:
            recs.append(record)
        return recs
    except:
        traceback.print_exc()
        return []


def syslog_exists():
    try:
        result = shareds.driver.session().run(syslog_cypher_exists).single()
        return result[0] > 0
    except:
        traceback.print_exc()
        raise

def syslog_init():
    if not syslog_exists():
        try:
            shareds.driver.session().run(syslog_cypher_init).single()
        except:
            traceback.print_exc()
            raise
