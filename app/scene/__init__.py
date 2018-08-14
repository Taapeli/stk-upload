from flask import Blueprint

bp = Blueprint('scene', __name__, template_folder='templates')

from . import routes
