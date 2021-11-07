from flask import Blueprint

bp = Blueprint('merge', __name__, template_folder='templates')
from .sources import routes
