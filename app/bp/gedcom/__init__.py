from flask import Blueprint

bp = Blueprint('gedcom',__name__,template_folder='templates')

from . import handlers