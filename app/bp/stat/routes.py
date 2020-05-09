# Flask routes program for Stk application stat blueprint
# @ Sss 2020
# Juha Takala 08.05.2020 19:11:31

import logging
logger = logging.getLogger('stkserver')
import time

from flask import render_template, request, redirect, url_for, flash, jsonify
from flask_security import roles_accepted, login_required #, current_user ,roles_required
from flask_babelex import _

import shareds
from models.gen.person_name import Name

from . import bp


@bp.route('/stat')
@login_required
@roles_accepted('admin')
def stat_home():
    """Statistiikkaa palvelimelta.
    """
    return render_template("/stat/stat.html")
