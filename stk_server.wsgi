#!/usr/bin/python
import sys
import os
import logging
logging.basicConfig(level=logging.INFO, format=('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))

logging.basicConfig(stream=sys.stderr)
sys.path.insert(0,"/opt/repo/ROOT/stk_server")
#print('Polku: ' + str(sys.path))
os.chdir("/opt/repo/ROOT/stk_server")

from stk_server import app as application
application.secret_key = 'Add your secret key'
