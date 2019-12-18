from flask import Blueprint

bp = Blueprint('audit', __name__, template_folder='templates')
from . import routes
