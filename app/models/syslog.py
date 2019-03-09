import json
import time
import traceback

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
    try:
        open(logname,"a").write(msg+"\n")
    except:
        traceback.print_exc()
    
def readlog():
    logname = shareds.app.config.get('SYSLOGNAME')
    if not logname: return []
    try:
        return open(logname).readlines()
    except:
        traceback.print_exc()
        return []
