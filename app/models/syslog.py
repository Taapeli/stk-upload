import json
import time

import shareds
from models import util

def log(**kwargs):
    logname = shareds.app.config.get('SYSLOGNAME')
    if not logname: return
    values = dict(
        time=time.time(),
        timestr=util.format_timestamp())
    values.update(kwargs)
    msg = json.dumps(values)
    open(logname,"a").write(msg+"\n")
    
