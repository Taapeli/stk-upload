#!/usr/bin/python
import sys
import logging
import os

logging.basicConfig(stream=sys.stderr)
sys.path.insert(0,"/opt/repo/ROOT/stk_server")
#print('Polku: ' + str(sys.path))
os.chdir("/opt/repo/ROOT/stk_server")

#from stk_server.hello import app as application
from stk_server.stk_run import app as application
application.secret_key = 'Add your secret key'
