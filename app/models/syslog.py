import json
import time

from flask_security import current_user

import shareds
from models import util

def log(type,**kwargs):
    logname = shareds.app.config.get('SYSLOGNAME')
    if not logname: return
    try:
        user=current_user.username
    except:
        user = ""
    values = dict(
        _type=type,
        _user=user,
        _time=time.time(),
        _timestr=util.format_timestamp())
    values.update(kwargs)
    msg = json.dumps(values)
    print("MSG",msg)
    open(logname,"a").write(msg+"\n")
    
def readlog():
    logname = shareds.app.config.get('SYSLOGNAME')
    if not logname: return []
    return open(logname).readlines()
