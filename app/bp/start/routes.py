# coding=UTF-8
# Flask routes program for Stk application
# @ Sss 2016
# JMä 29.12.2015

import logging 
import traceback
from bp.start.forms import JoinForm
from werkzeug.utils import redirect
from flask.helpers import url_for
logger = logging.getLogger('stkserver')

from flask import render_template, request, session , flash
from flask_security import login_required, roles_accepted, current_user
from flask_babelex import _

import shareds
from models import email

""" Application route definitions
""" 

@shareds.app.before_request
def force_https():
    if request.endpoint in shareds.app.view_functions and not request.is_secure:
        #print(f"redirect to {request.url.replace('http://', 'https://')}")
        host = request.host.split(":")[0]
        if host in {"localhost","127.0.0.1"}: return
        return redirect(request.url.replace('http://', 'https://'))
    
@shareds.app.route('/', methods=['GET', 'POST'])
def start():
    """ Home page for logged in user (from login page or home button) 
        or anonymous user (home)
    """
    print(f"request.endpoint = {request.endpoint}")
    print(f"request.is_secure = {request.is_secure}")
    print(f"request.host = {request.host}")
    if current_user.is_authenticated:
        role_names = [role.name for role in current_user.roles]
        logger.info("Start user {}/{}, roles {}".\
                    format(current_user.username, current_user.email, role_names))
        return render_template('/start/index_logged.html')
    else:
#        session['lang'] = new_lang
        logger.info('Anonymous user')
        return render_template('/start/index.html')

@shareds.app.route('/join2',methods=['get','post'])
def join2():
    if request.method == 'POST':
        msg = ""
        for name,value in request.form.items():
            msg += f"\n{name}: {value}"
        email.email_admin("New user for Isotammi", msg )
        return render_template("/start/thankyou.html")
    else:
        return render_template("/start/join.html")

@shareds.app.route('/thankyou')
def thankyou():
    return render_template("/start/thankyou.html")

@shareds.app.route('/join', methods=['GET', 'POST'])
def join():
    
    form = JoinForm()
    msg = ""
    for name,value in request.form.items():
        msg += f"\n{name}: {value}"
    logging.info(msg)
    if form.validate_on_submit(): 
        msg = ""
        for name,value in request.form.items():
            if name == "csrf_token": continue
            if name == "submit": continue
            msg += f"\n{name}: {value}"
        logging.info(msg)
        email.email_admin("New user request for Isotammi", msg )
        """
        user = User(id = form.id.data,
                email = form.email.data,
                username = form.username.data,
                name = form.name.data,
                language = form.language.data,
                is_active = form.is_active.data,
                roles = form.roles.data,
                confirmed_at = form.confirmed_at.data,
                last_login_at = form.last_login_at.data, 
                last_login_ip = form.last_login_ip.data,                    
                current_login_at = form.current_login_at.data,  
                current_login_ip = form.current_login_ip.data,
                login_count = form.login_count.data)        
        updated_user = UserAdmin.update_user(user)
        if updated_user.username == current_user.username:
            session['lang'] = form.language.data
        """
        flash(_("Join message sent"))
        return redirect(url_for("thankyou"))

    """
    user = shareds.user_datastore.get_user(username) 
    form.id.data = user.id  
    form.username.data = user.username
    form.name.data = user.name 
    form.language.data = user.language
    form.is_active.data = user.is_active
    form.roles.data = [role.name for role in user.roles]
    form.confirmed_at.data = user.confirmed_at 
    form.last_login_at.data = user.last_login_at  
    form.last_login_ip.data = user.last_login_ip
    form.current_login_at.data = user.current_login_at
    form.current_login_ip.data = user.current_login_ip
    form.login_count.data = user.login_count
    """    
    #form.email.data = user.email
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
    email.email_admin(_(subject),
                      body,
                      sender=(current_user.name,current_user.email))
    return "ok"

@shareds.app.route('/settings',methods=["GET","POST"])
@login_required
def my_settings():
    lang = request.form.get("lang")
    referrer = request.form.get("referrer",default=request.referrer)
    if lang:
        try:
            from bp.admin.models.user_admin import UserAdmin # can't import earlier
            current_user.language = lang
            saved_roles = current_user.roles 
            current_user.roles = [role.name for role in current_user.roles]
            updated_user = UserAdmin.update_user(current_user)
            current_user.roles = saved_roles
            if not updated_user:
                flash(_("Update did not work1"),category='flash_error')
            session['lang'] = lang
        except:
            flash(_("Update did not work"),category='flash_error')
            traceback.print_exc()
    print("-> bp.start.routes.my_settings")
    return render_template("/start/my_settings.html",
                           referrer=referrer,
                           roles=current_user.roles)

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

