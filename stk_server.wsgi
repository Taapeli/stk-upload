#!/usr/bin/python
import sys
import os
import logging
logging.basicConfig(level=logging.INFO, format=('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))

logging.basicConfig(stream=sys.stderr)
print("Start directory {}".format(os.getcwd()))
sys.path.insert(0, os.path.join(os.getcwd(),"app")) #"/opt/repo/ROOT/app"
print('Polku: ' + str(sys.path))
#os.chdir("/opt/repo/ROOT/app")
print("Active directory {}".format(os.getcwd()))

from app import app as application
application.secret_key = 'You don\'n know OUR secret key'
