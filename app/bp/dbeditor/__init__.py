from flask import Blueprint

bp = Blueprint('dbeditor', __name__, template_folder='templates')
from . import routes
