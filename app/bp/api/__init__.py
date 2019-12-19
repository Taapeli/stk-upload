from flask import Blueprint

bp = Blueprint('api', __name__, template_folder='templates')
from . import routes 
 