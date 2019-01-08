# coding=UTF-8
# Flask routes program for Stk application
# @ Sss 2016
# JMä 29.12.2015

#import urllib

import logging 
logger = logging.getLogger('stkserver')
#import time

from flask import render_template, redirect, url_for #, request, flash, g
from flask_security import login_required, roles_accepted, current_user # ,roles_required
#from flask_babelex import _

import shareds
#from models.gen.person_name import Name
# from models import dbutil
# from models import loadfile          # Datan lataus käyttäjältä
#from models import datareader          # Tietojen haku kannasta (tai työtiedostosta)
#from models import dataupdater         # Tietojen päivitysmetodit


""" Application route definitions
""" 

@shareds.app.route('/', methods=['GET', 'POST'])
def start():
    """ Home page for logged in user """
    print("-> bp.start.routes.start auth={}".format(current_user.is_authenticated))
    if current_user.is_authenticated:
        role_names = [role.name for role in current_user.roles]
        logger.info("Start user {}/{}, roles {}".\
                    format(current_user.username, current_user.email, role_names))
        return render_template('/start/index_logged.html')
    else:
        logger.info('Anonymous user')
    return render_template('/start/index.html')


@shareds.app.route('/start', methods=['GET', 'POST'])
@login_required
def start_login():
    """ Home page for logged in user """
    print("-> bp.start.routes.start_logged_in")
    role_names = [role.name for role in current_user.roles]
    logger.info("Start user {}/{}, roles {}".\
                format(current_user.username, current_user.email, role_names))
    return render_template('/start/index_logged.html')

@shareds.app.route('/tables')
@login_required
@roles_accepted('member', 'admin')
def datatables():
    """ Home page for table format tools """
    print("-> bp.start.routes.datatables")
    return render_template("/tools/tables.html")

@shareds.app.route('/gramps')
@login_required
@roles_accepted('member', 'admin')
def gramps_upload():
    """ Home page gramps input file processing """
    print("-> bp.start.routes.gramps_upload")
    return render_template("/gramps/index_gramps.html")

# Admin start page
@shareds.app.route('/admin',  methods=['GET', 'POST'])
@login_required
@roles_accepted('admin', 'master')
def admin():
    """ Home page for administrator """    
    print("-> bp.start.routes.scene")
    return render_template('/admin/admin.html')

# Narrative start page
@shareds.app.route('/scene',  methods=['GET', 'POST'])
def scene():
    """ Home page for scene narrative pages ('kertova') """    
    print("-> bp.start.routes.scene")
    return render_template('/scene/index_scene.html')
