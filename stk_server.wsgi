#!/usr/bin/python
import sys
import logging

logging.basicConfig(stream=sys.stderr)
sys.path.insert(0,"/opt/shared/webroot/ROOT/stk_server")

from stk_server import stk_server as application
application.secret_key = 'Add your secret key'
