import json
import time

from flask_security import current_user

import shareds
from models import util

def log(type,**kwargs):
    logname = shareds.app.config.get('SYSLOGNAME')
    if not logname: return
    values = dict(
        _type=type,
        _user=current_user.username,
        _time=time.time(),
        _timestr=util.format_timestamp())
    values.update(kwargs)
    msg = json.dumps(values)
    open(logname,"a").write(msg+"\n")
    
def readlog():
    logname = shareds.app.config.get('SYSLOGNAME')
    if not logname: return None
    return open(logname).readlines()
