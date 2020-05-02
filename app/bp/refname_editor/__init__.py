from flask import Blueprint

bp = Blueprint('refname_editor', __name__, template_folder='templates')
from . import routes
