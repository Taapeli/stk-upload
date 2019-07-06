from flask import Blueprint

bp = Blueprint('dupsearch', __name__, template_folder='templates')
from . import routes
