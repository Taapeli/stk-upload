from flask import Blueprint

bp = Blueprint('narrative', __name__, template_folder='templates')

from . import routes
