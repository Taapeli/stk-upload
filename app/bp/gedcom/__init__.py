'''
    Initialize gedcom transform Blueprint packakge
'''
import os
from flask import Blueprint

bp = Blueprint('gedcom',__name__,template_folder='templates')

# Directories
from config import APP_ROOT
GEDCOM_DATA=os.path.join(APP_ROOT, "gedcoms") 
GEDCOM_APP=os.path.join(APP_ROOT, "app/bp/gedcom")
  
print("gedcom.init APP={}, DATA={}".format(GEDCOM_APP, GEDCOM_DATA))

ALLOWED_EXTENSIONS = {"ged"}  

from . import handlers
