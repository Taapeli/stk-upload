from flask import Blueprint

admin_pages = Blueprint('admin', __name__, template_folder='templates')

from . import models
