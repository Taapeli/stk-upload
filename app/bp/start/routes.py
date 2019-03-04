# coding=UTF-8
# Flask routes program for Stk application
# @ Sss 2016
# JMä 29.12.2015

import logging 
logger = logging.getLogger('stkserver')

from flask import render_template, request #, session, redirect, url_for, flash, g
from flask_security import login_required, roles_accepted, current_user # ,roles_required
from flask_babelex import _

import shareds
from models import email

""" Application route definitions
""" 

@shareds.app.route('/', methods=['GET', 'POST'])
def start():
    """ Home page for logged in user (from login page or home button) 
        or anonymous user (home)
    """
    print("--- " + repr(request))
#    print("-> bp.start.routes.start auth={}, new_lang={}, user_session".\
#          format(current_user.is_authenticated, new_lang))
    if current_user.is_authenticated:
        role_names = [role.name for role in current_user.roles]
        logger.info("Start user {}/{}, roles {}".\
                    format(current_user.username, current_user.email, role_names))
        return render_template('/start/index_logged.html')
    else:
#        session['lang'] = new_lang
        logger.info('Anonymous user')
        return render_template('/start/index.html')

@shareds.app.route('/message')
@login_required
def my_message():
    print("-> bp.start.routes.settings")
    return render_template("/start/my_message.html")

@shareds.app.route('/send_email',methods=["post"])
@login_required
def send_email():
    body = request.form["message"]
    print(body)
    email.email_admin(_("Message from Isotammi user " + current_user.username),body,sender=current_user.email)
    return "ok"

@shareds.app.route('/settings')
@login_required
def my_settings():
    print("-> bp.start.routes.settings")
    return render_template("/start/my_settings.html")

# @shareds.app.route('/tables') --> see bp.tools.routes.datatables
# @login_required
# @roles_accepted('member', 'admin')
# def datatables():
#     """ Home page for table format tools """
#     print("-> bp.start.routes.datatables")
#     return render_template("/tools/tables.html")
# @shareds.app.route('/gramps') moved to bp.gramps.routes 2019-01-22
# @login_required
# @roles_accepted('member', 'admin')
# def gramps_upload():
#     """ Home page gramps input file processing """
#     print("-> bp.start.routes.gramps_upload")
#     return render_template("/gramps/index_gramps.html")

# Admin start page
@shareds.app.route('/admin',  methods=['GET', 'POST'])
@login_required
@roles_accepted('admin', 'master')
def admin():
    """ Home page for administrator """    
    print("-> bp.start.routes.admin")
    return render_template('/admin/admin.html')

# route('/scene',  methods=['GET', 'POST']) moved to bp.scene.routes 2019-01-20

