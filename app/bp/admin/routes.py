'''
Created on 8.8.2018

@author: jm

 Administrator operations page urls
 
'''

import os

import logging 
import inspect
import traceback
#import datetime
#from _pickle import Unpickler
logger = logging.getLogger('stkserver')

from flask import render_template, request, redirect, url_for, send_from_directory, flash, session
from flask_security import login_required, roles_accepted, roles_required, current_user
from flask_babelex import _

import shareds
from setups import User, Allowed_email #, Role
from models import dbutil, dataupdater, loadfile, datareader, util
from bp.admin.models.data_admin import DataAdmin
from bp.admin.models.user_admin import UserAdmin
from .cvs_refnames import load_refnames
from .forms import AllowedEmailForm, UpdateAllowedEmailForm, UpdateUserForm
from . import bp
from . import uploads
from .. gedcom.models import gedcom_utils
from .. import gedcom
from models import email
from models import syslog 

# Admin start page
@bp.route('/admin',  methods=['GET', 'POST'])
@login_required
@roles_accepted('admin', 'master')
def admin():
    """ Home page for administrator """    
    print("-> bp.start.routes.admin")
    return render_template('/admin/admin.html')


@bp.route('/admin/clear_db/<string:opt>')
@login_required
@roles_required('admin')
def clear_db(opt):
    """ Clear database - with no confirmation! """
    try:
        updater = DataAdmin(current_user)
        msg =  updater.db_reset(opt) # dbutil.alusta_kanta()
        return render_template("/admin/talletettu.html", text=msg)
    except Exception as e:
        return redirect(url_for('virhesivu', code=1, text=str(e)))

@bp.route('/admin/clear_my_own')
@login_required
@roles_accepted('research')
def clear_my_db():
    """ Clear database - with no confirmation! """
    try:
        updater = DataAdmin(current_user)
        msg =  updater.db_reset('my_own') # dbutil.alusta_kanta()
        return render_template("/admin/talletettu.html", text=msg)
    except Exception as e:
        return redirect(url_for('virhesivu', code=1, text=str(e)))


#TODO Ei varmaan pitäisi enää olla käytössä käytössä?
@bp.route('/admin/set/estimated_dates')
@bp.route('/admin/set/estimated_dates/<int:uid>')
@login_required
@roles_required('admin')
def estimate_dates(uid=None):
    """ syntymä- ja kuolinaikojen arvioiden asettaminen henkilöille """
    message = dataupdater.set_estimated_person_dates(list(uid))
    ext = _("estimated lifetime")
    return render_template("/admin/talletettu.html", text=message, info=ext)

# Refnames homa page
@bp.route('/admin/refnames')
@login_required
@roles_required('admin')
def refnames():
    """ Operations for reference names """
    return render_template("/admin/reference.html")

@bp.route('/admin/set/refnames')
@login_required
@roles_accepted('member', 'admin')
def set_all_person_refnames():
    """ Setting reference names for all persons """
    dburi = dbutil.get_server_location()
    message = dataupdater.set_person_name_properties(ops=['refname']) or _('Done')
    return render_template("/admin/talletettu.html", text=message, uri=dburi)

@bp.route('/admin/upload_csv', methods=['POST'])
@login_required
@roles_required('admin')
def upload_csv():
    """ Load a cvs file to temp directory for processing in the server
    """
    try:
        infile = request.files['filenm']
        material = request.form['material']
        logging.debug("Got a {} file '{}'".format(material, infile.filename))

        loadfile.upload_file(infile)
        if 'destroy' in request.form and request.form['destroy'] == 'all':
            logger.info("*** About deleting all previous Refnames ***")
            datareader.recreate_refnames()

    except Exception as e:
        return redirect(url_for('virhesivu', code=1, text=str(e)))

    return redirect(url_for('admin.save_loaded_csv', filename=infile.filename, subj=material))

@bp.route('/admin/save/<string:subj>/<string:filename>')
@login_required
@roles_required('admin')
def save_loaded_csv(filename, subj):
    """ Save loaded cvs data to the database """
    pathname = loadfile.fullname(filename)
    dburi = dbutil.get_server_location()
    try:
        if subj == 'refnames':    # Stores Refname objects
            status = load_refnames(pathname)
        else:
            return redirect(url_for('virhesivu', code=1, text= \
                _("Data type '{}' is not supported").format(subj)))
    except KeyError as e:
        return render_template("virhe_lataus.html", code=1, \
               text=_("Missing proper column title: ") + str(e))
    return render_template("/admin/talletettu.html", text=status, uri=dburi)

# # Ei ilmeisesti käytössä
# @bp.route('/admin/aseta/confidence')
# @roles_required('admin')
# def aseta_confidence():
#     """ tietojen laatuarvion asettaminen henkilöille """
#     dburi = dbutil.get_server_location()
#     message = dataupdater.set_confidence_value()
#     return render_template("/admin/talletettu.html", text=message, uri=dburi)


@bp.route('/admin/allowed_emails',  methods=['GET', 'POST'])
@login_required
@roles_accepted('admin', 'master') 
def list_allowed_emails():
    form = AllowedEmailForm()
#    if request.method == 'POST':
    lista = UserAdmin.get_allowed_emails()
    if form.validate_on_submit(): 
# Register a new email
        UserAdmin.register_allowed_email(form.allowed_email.data,
                                         form.default_role.data)
        return redirect(url_for('admin.list_allowed_emails'))

    return render_template("/admin/allowed_emails.html", emails=lista, 
                            form=form)
    
@bp.route('/admin/update_allowed_email/<email>', methods=['GET', 'POST'])
@login_required
@roles_accepted('admin', 'master')
def update_allowed_email(email):
    
    form = UpdateAllowedEmailForm()
    if form.validate_on_submit():
        allowed_email = Allowed_email(
                allowed_email = form.email.data,
                default_role = form.role.data,
                approved = form.approved.data,
                creator = form.creator.data)
#                 created_at = form.created.data,
#                 confirmed_at = form.confirmed_at.data) 
        _updated_allowed_email = UserAdmin.update_allowed_email(allowed_email)
        flash(_("Allowed email updated"))
        return redirect(url_for("admin.update_allowed_email", email=form.email.data))

    allowed_email = UserAdmin.find_allowed_email(email) 
    form.email.data = allowed_email.allowed_email
    form.approved.data = allowed_email.approved
    form.role.data = allowed_email.default_role
    form.creator.data = allowed_email.creator
    form.created.data = allowed_email.created_at
    form.confirmed_at.data = allowed_email.confirmed_at
    return render_template("/admin/update_allowed_email.html", allowed_email=allowed_email.allowed_email, form=form)  

@bp.route('/admin/list_users', methods=['GET'])
@login_required
@roles_accepted('admin', 'audit', 'master')
def list_users():
    lista = shareds.user_datastore.get_users()
    return render_template("/admin/list_users.html", users=lista)  


@bp.route('/admin/list_all_users', methods=['GET', 'POST'])
@login_required
@roles_accepted('admin', 'audit', 'master')
def list_all_users():
    """ List users and candidate users.
    
        list_allowed_emails + list_users
    """
    # Allowe emails
    form = AllowedEmailForm()
    list_emails = UserAdmin.get_allowed_emails()
    if form.validate_on_submit(): 
        # Register a new email
#        lista = UserAdmin.get_allowed_emails()
        UserAdmin.register_allowed_email(form.allowed_email.data,
                                         form.default_role.data)
        return redirect(url_for('admin.list_allowed_emails'))


    list_users = shareds.user_datastore.get_users()
    return render_template("/admin/list_users_mails.html", 
                           users=list_users, emails=list_emails)  


@bp.route('/admin/update_user/<username>', methods=['GET', 'POST'])
@login_required
@roles_accepted('admin', 'master')
def update_user(username):
    
    form = UpdateUserForm()
    if form.validate_on_submit(): 
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
        flash(_("User updated"))
        return redirect(url_for("admin.update_user", username=updated_user.username))

    user = shareds.user_datastore.get_user(username) 
    form.id.data = user.id  
    form.email.data = user.email
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
        
    return render_template("/admin/update_user.html", username=user.username, form=form)  

@bp.route('/admin/list_uploads/<username>', methods=['GET'])
@login_required
@roles_accepted('admin', 'audit')
def list_uploads(username):
    upload_list = uploads.list_uploads(username) 
    return render_template("/admin/uploads.html", uploads=upload_list, user=username)

@bp.route('/admin/list_uploads_all', methods=['POST'])
@login_required
@roles_accepted('admin', 'audit')
def list_uploads_for_users():
    requested_users = request.form.getlist('select_user')
    if len(requested_users) == 0:
        users = shareds.user_datastore.get_users()  # default: all users
    else:
        users = [user for user in shareds.user_datastore.get_users() if user.username in requested_users]
    upload_list = list(uploads.list_uploads_all(users))
    return render_template("/admin/uploads.html", uploads=upload_list,  
                           users=users, num_requested_users=len(requested_users), 
                           num_users=len(users))

@bp.route('/admin/list_uploads_all', methods=['GET'])
@login_required
@roles_accepted('admin', 'audit')
def list_uploads_all():
    users = shareds.user_datastore.get_users()
    upload_list = list(uploads.list_uploads_all(users))
    return render_template("/admin/uploads.html", uploads=upload_list )

@bp.route('/admin/start_upload/<username>/<xmlname>', methods=['GET'])
@login_required
@roles_accepted('admin', 'audit')
def start_load_to_neo4j(username,xmlname):
    uploads.initiate_background_load_to_neo4j(username,xmlname)
    flash(_('Data import from %(i)s to database has been started.', i=xmlname), 'info')
    return redirect(url_for('admin.list_uploads', username=username))

@bp.route('/admin/list_threads', methods=['GET'])
@login_required
@roles_accepted('admin', 'audit')
def list_threads(): # for debugging
    import threading
    s = "<pre>\n"
    s += "Threads:\n"
    for t in threading.enumerate():
        s += "  " + t.name + "\n"
    s += "-----------\n"
    s += "Current thread: " + threading.current_thread().name
    s += "</pre>"
    return s

@bp.route('/admin/xml_download/<username>/<xmlfile>')
@login_required
@roles_accepted('admin', 'audit')
def xml_download(username,xmlfile):
    xml_folder = uploads.get_upload_folder(username)
    xml_folder = os.path.abspath(xml_folder)
    logging.info(xml_folder)
    logging.info(xmlfile)
    return send_from_directory(directory=xml_folder, filename=xmlfile, 
                               mimetype="application/gzip",
                               as_attachment=True)
    #attachment_filename=xmlfile+".gz") 

@bp.route('/admin/show_upload_log/<username>/<xmlfile>')
@login_required
@roles_accepted('member', 'admin')
def show_upload_log(username,xmlfile):
    upload_folder = uploads.get_upload_folder(username)
    fname = os.path.join(upload_folder,xmlfile + ".log")
    #result_list = Unpickler(open(fname,"rb")).load()
    msg = open(fname, encoding="utf-8").read()
    #return render_template("/admin/load_result.html", batch_events=result_list)
    return render_template("/admin/load_result.html", msg=msg)


@bp.route('/admin/xml_delete/<username>/<xmlfile>')
@login_required
@roles_accepted('admin', 'audit')
def xml_delete(username,xmlfile):
    uploads.delete_files(username,xmlfile)
    syslog.log(type="gramps file uploaded",file=xmlfile,user=username)
    return redirect(url_for('admin.list_uploads', username=username))

#------------------- GEDCOMs -------------------------

def list_gedcoms(users):
    for user in users:
        for f in gedcom_utils.list_gedcoms(user.username):
            yield (user.username,f)

@bp.route('/admin/list_user_gedcoms/<user>', methods=['GET'])
@login_required
@roles_accepted('admin', 'audit')
def list_user_gedcoms(user):
    session["gedcom_user"] = user
    return gedcom.routes.gedcom_list()

@bp.route('/admin/list_user_gedcom/<user>/<gedcomname>', methods=['GET'])
@login_required
@roles_accepted('admin', 'audit')
def list_user_gedcom(user,gedcomname):
    session["gedcom_user"] = user
    return gedcom.routes.gedcom_info(gedcomname)

@bp.route('/admin/list_gedcoms_for_users', methods=['POST'])
@login_required
@roles_accepted('admin', 'audit')
def list_gedcoms_for_users():
    requested_users = request.form.getlist('select_user')
    if len(requested_users) == 0:
        users = shareds.user_datastore.get_users()  # default: all users
    else:
        users = [user for user in shareds.user_datastore.get_users() if user.username in requested_users]
    gedcom_list = list(list_gedcoms(users))
    return render_template("/admin/gedcoms.html", gedcom_list=gedcom_list, 
                           num_requested_users=len(requested_users),
                           users=users,
                           num_users=len(users))

#------------------- Email -------------------------
@bp.route('/admin/send_email', methods=['POST'])
@login_required
@roles_accepted('admin', 'audit')
def send_email():
    requested_users = request.form.getlist('select_user')
    emails = [user.email for user in shareds.user_datastore.get_users() if user.username in requested_users]
    return render_template("/admin/message.html", 
                           users=", ".join(requested_users),emails=emails)
    
@shareds.app.route('/admin/send_emails',methods=["post"])
@login_required
@roles_accepted('admin', 'audit')
def send_emails():
    subject = request.form["subject"]
    body = request.form["message"]
    receivers = request.form.getlist("email")
    for receiver in receivers:
        email.email_from_admin(subject,body,receiver)
    return "ok"
    
#------------------- Site map -------------------------

def find_roles(endpoint,endpoints):
    info = endpoints.get(endpoint)
    if not info: return False,[]
    roles = []
    if info.roles_accepted: roles += info.roles_accepted
    if info.roles_required: roles += info.roles_required
    return info.login_required,roles

@bp.route("/admin/site-map")
@login_required
@roles_accepted('admin')
def site_map():
    "Show list of application route paths"
    class Link():
        def __init__(self, url='', endpoint='', methods='', desc='', roles='', login_required=False):
            self.url = url
            self.endpoint = endpoint
            self.methods = methods
            self.desc = desc
            self.roles = roles
            self.login_required = login_required

    links = []
    
    endpoints = util.scan_endpoints()
    for rule in shareds.app.url_map.iter_rules():
        #if not rule.endpoint.startswith("admin.clear"): continue
        #print(dir(rule.methods))
        #print(rule.methods)
        methods=''
        roles=''
        if "GET" in rule.methods: 
            methods="GET"
        if "POST" in rule.methods: 
            methods += " POST"
        try:
            #print("{} def {}".format(rule.rule, rule.defaults))
            url = rule.rule
            #url = url_for(rule.endpoint, **(rule.defaults or {}))
            try:
                view_function = shareds.app.view_functions[rule.endpoint]
                login_required, roles = find_roles(rule.rule, endpoints)
            except:
                traceback.print_exc()
                pass
        except:
            traceback.print_exc()
            url="-"
        links.append(Link(url, rule.endpoint, methods, roles=",".join(roles),login_required=login_required))
    
    return render_template("/admin/site-map.html", links=links)


#------------------- Log -------------------------
@bp.route("/admin/readlog")
@login_required
@roles_accepted('admin')
def readlog():
    direction = request.args.get("direction")
    startid_arg = request.args.get("id")
    if startid_arg:
        startid = int(startid_arg)
    else:
        startid = None
    recs = syslog.readlog(direction,startid)
    return render_template("/admin/syslog.html", recs=recs)
    
