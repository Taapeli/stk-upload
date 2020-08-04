# coding=UTF-8
# Flask routes program for Stk application
# @ Sss 2016
# JMä 29.12.2015

import logging 
import traceback
from werkzeug.utils import redirect
from flask.helpers import url_for
from ..gedcom.models import gedcom_utils
logger = logging.getLogger('stkserver')

from flask import render_template, request, session , flash
from flask_security import login_required, roles_accepted, current_user, utils as secutils
from flask_babelex import _, get_locale

import shareds
from models import email
from bp.api import api

from bp.start.forms import JoinForm
from models.gen.batch_audit import Batch

""" Application route definitions
"""

@shareds.app.before_request
def force_https():
    if not shareds.app.config.get('FORCE_HTTPS'): return
    if request.endpoint in shareds.app.view_functions and not request.is_secure:
        host = request.host.split(":")[0]
        if host in {"localhost","127.0.0.1"}: return
        return redirect(request.url.replace('http://', 'https://'))

# @shareds.app.route('/')
#     Home page for a guest user (from login page or home button)
#     or anonymous user (home)
#
#     @See: routes.entry

@shareds.app.route('/start/guest', methods=['GET', 'POST'])
def start_guest():
    """ Scene start page for a guest user.
    """
    user = shareds.user_datastore.get_user('guest')
    secutils.login_user(user)
    logger.info('-> bp.start.routes.start_guest')
    return render_template('/start/index_guest.html')


@shareds.app.route('/start/logged', methods=['GET', 'POST'])
@login_required
#@roles_accepted('member', 'gedcom', 'research', 'audit', 'admin')
def start_logged():
    """ Opening the home page for logged in user (from login page or home button)
        or anonymous user (home).

        Note. The home page for anonymous user is routes.entry in app/routes.py
    """
    if "gedcom_user" in session: del session["gedcom_user"]

    role_names = [role.name for role in current_user.roles]
    logger.info(f"-> bp.start.routes.start_logged")
    logger.debug(f"bp.start.routes.start_logged"
                 f" lang={get_locale().language}"
                 f" user={current_user.username}/{current_user.email}"
                 f" roles= {role_names}")
    return render_template('/start/index_logged.html')


@shareds.app.route('/thankyou')
def thankyou():
    return render_template("/start/thankyou.html")

@shareds.app.route('/join', methods=['GET', 'POST'])
def join():
    from bp.admin.models.user_admin import UserProfile, UserAdmin

    form = JoinForm()
    logger.info('-> bp.start.routes.join')
    msg = ""
    for name,value in request.form.items():
        msg += f"\n{name}: {value}"
    if form.validate_on_submit(): 
        msg = ""
        for name,value in request.form.items():
            if name == "csrf_token": continue
            if name == "submit": continue
            msg += f"\n{name}: {value}"
        if email.email_admin("New user request for Isotammi", msg,
                             sender=request.form.get('email') ):
            flash(_("Join message sent"))
        else:
            flash(_("Sending join message failed"))
        profile = UserProfile(
            name=request.form.get("name"),
            email = request.form.get('email'),
            language = request.form.get('language'),
            GSF_membership = request.form.get('GSF_membership'),
            research_years = request.form.get('research_years'),
            software = request.form.get('software'),
            researched_names = request.form.get('researched_names'),
            researched_places = request.form.get('researched_places'),
            text_message = request.form.get('text_message'),
        )
        UserAdmin.register_applicant(profile,role=None)
        return redirect(url_for("thankyou"))

    return render_template("/start/join.html", form=form)  


@shareds.app.route('/message')
@login_required
def my_message():
    return render_template("/start/my_message.html")

@shareds.app.route('/send_email',methods=["post"])
@login_required
def send_email():
    subject = request.form["subject"]
    body = request.form["message"]
    ok = email.email_admin(_(subject),
                      body,
                      sender=(current_user.name,current_user.email))
    if ok:
        return "ok"
    else:
        return "failed"

@shareds.app.route('/settings',methods=["GET","POST"])
@login_required
def my_settings():
    lang = request.form.get("lang")
    is_guest = current_user.username == "guest"
    referrer = request.form.get("referrer",default=request.referrer)
    if lang:
        try:
            from bp.admin.models.user_admin import UserAdmin # can't import earlier
            current_user.language = lang
            result = UserAdmin.update_user_language(current_user.username,lang)
            if not result:
                flash(_("Update did not work1"),category='flash_error')
            session['lang'] = lang
        except:
            flash(_("Update did not work"),category='flash_error')
            traceback.print_exc()

    labels, user_batches = Batch.get_user_stats(current_user.username)
    print(f'# User batches {user_batches}')

    gedcoms = gedcom_utils.list_gedcoms(current_user.username)
    print(f'# Gedcoms {gedcoms}')
    
    logger.info("-> bp.start.routes.my_settings")
    return render_template("/start/my_settings.html",
                           is_guest=is_guest,
                           referrer=referrer,
                           roles=current_user.roles,
                           apikey=api.get_apikey(current_user),
                           labels=labels,
                           batches=user_batches,
                           gedcoms=gedcoms)

# Admin start page
@shareds.app.route('/admin',  methods=['GET', 'POST'])
@login_required
@roles_accepted('admin', 'master')
def admin():
    """ Home page for administrator """    
    logger.info("-> bp.start.routes.admin")
    return render_template('/admin/admin.html')


