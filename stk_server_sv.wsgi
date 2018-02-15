#!/usr/bin/python
# Version for public server (?) / 8.2.2018 JMä
import sys
import logging
import os

logging.basicConfig(stream=sys.stderr)
sys.path.insert(0,"/opt/repo/ROOT/stk_server")
#print('Polku: ' + str(sys.path))
os.chdir("/opt/repo/ROOT/stk_server") 

#from stk_server.hello import app as application
import stk_server
from stk_server import app as application
application.secret_key = 'Add your secret key'




