from flask import Blueprint

bp = Blueprint('graph', __name__, template_folder='templates')

from . import routes
