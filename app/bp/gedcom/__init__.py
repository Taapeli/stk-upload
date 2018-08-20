'''
    Initialize gedcom transform Blueprint packakge
'''
import os
from flask import Blueprint

bp = Blueprint('gedcom',__name__,template_folder='templates')

# Directories
from config import APP_ROOT
GEDCOMS_DIR=os.path.join(APP_ROOT, "gedcoms")   # Absolute path 
# GEDDER_PATH=os.path.join(APP_ROOT, "app/bp/gedcom")
GEDDER_PATH="app/bp/gedcom"                     # Relative to APP_ROOT
  
print("Gedcom directories Gedder={}, gedcom={}".format(GEDDER_PATH, GEDCOMS_DIR))

ALLOWED_EXTENSIONS = {"ged"}  

from . import handlers
