from flask import Blueprint

bp = Blueprint('stat', __name__, template_folder='templates')

from . import routes
