from flask import Blueprint

bp = Blueprint('tools', __name__, template_folder='templates')
from . import routes
