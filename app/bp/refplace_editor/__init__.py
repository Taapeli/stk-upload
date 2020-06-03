from flask import Blueprint

bp = Blueprint('refplace_editor', __name__, template_folder='templates')
from . import routes
