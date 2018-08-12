from flask import Blueprint
from . import routes

bp = Blueprint('admin', __name__, template_folder='templates')
