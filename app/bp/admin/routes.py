'''
Created on 8.8.2018

@author: jm

 Administrator operations page urls
 
'''

import os

import logging 
from _pickle import Unpickler
logger = logging.getLogger('stkserver')

from flask import render_template, request, redirect, url_for, send_from_directory
from flask_security import login_required, roles_accepted, roles_required, current_user
from flask_babelex import _

import shareds
from models import dbutil, dataupdater, loadfile, datareader
from .models import DataAdmin, UserAdmin
from .cvs_refnames import load_refnames
from .forms import AllowedEmailForm
from . import bp
from . import uploads


# # Go to admin start page in app/routes.py 
# @bp.route('/admin',  methods=['GET', 'POST'])
# @login_required
# @roles_required('admin')
# def admin():
#     """ Home page for administraor """    
#     return render_template('/admin/admin.html') # entinen adminindex.html


@bp.route('/admin/clear_db/<string:opt>')
@roles_required('admin')
def clear_db(opt):
    """ Clear database - with no confirmation! """
    try:
        updater = DataAdmin(current_user)
        msg =  updater.db_reset(opt) # dbutil.alusta_kanta()
        return render_template("/admin/talletettu.html", text=msg)
    except Exception as e:
        return redirect(url_for('virhesivu', code=1, text=str(e)))

#TODO Ei varmaan pitäisi enää olla käytössä käytössä?
@bp.route('/admin/set/estimated_dates')
@roles_required('admin')
def aseta_estimated_dates():
    """ syntymä- ja kuolinaikojen arvioiden asettaminen henkilöille """
    dburi = dbutil.get_server_location()
    message = dataupdater.set_estimated_dates()
    return render_template("/admin/talletettu.html", text=message, uri=dburi)

# Refnames homa page
@bp.route('/admin/refnames')
#@roles_required('admin')
def refnames():
    """ Operations for reference names """
    return render_template("/admin/reference.html")

@bp.route('/admin/set/refnames')
@roles_accepted('member', 'admin')
def set_all_person_refnames():
    """ Setting reference names for all persons """
    dburi = dbutil.get_server_location()
    message = dataupdater.set_person_refnames() or "Tehty"
    return render_template("/admin/talletettu.html", text=message, uri=dburi)

@bp.route('/admin/upload_csv', methods=['POST'])
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
                "Data type '" + subj + "' is not supported"))
    except KeyError as e:
        return render_template("virhe_lataus.html", code=1, \
               text="Missing proper column title: " + str(e))
    return render_template("/admin/talletettu.html", text=status, uri=dburi)

# # Ei ilmeisesti käytössä
# @bp.route('/admin/aseta/confidence')
# @roles_required('admin')
# def aseta_confidence():
#     """ tietojen laatuarvion asettaminen henkilöille """
#     dburi = dbutil.get_server_location()
#     message = dataupdater.set_confidence_value()
#     return render_template("/admin/talletettu.html", text=message, uri=dburi)


# Siirretty security--> admin
@bp.route('/admin/allowed_emails',  methods=['GET', 'POST'])
@login_required
@roles_required('admin')
def list_allowed_emails():
    form = AllowedEmailForm()
    if request.method == 'POST': 
        # Register a new email
        UserAdmin.allowed_email_register(form.allowed_email.data,
                                         form.default_role.data)
 
    lista = UserAdmin.get_allowed_emails()
    return render_template("/admin/allowed_emails.html", emails=lista, 
                            form=form)


# Siirretty security--> admin
@bp.route('/admin/list_users', methods=['GET'])
@login_required
@roles_accepted('admin', 'audit')
def list_users():
    # Käytetään neo4juserdatastorea
    lista = shareds.user_datastore.get_users()
    return render_template("/admin/list_users.html", users=lista)  

@bp.route('/admin/list_uploads/<username>', methods=['GET'])
@login_required
@roles_accepted('admin', 'audit')
def list_uploads(username):
    upload_list = uploads.list_uploads(username) 
    return render_template("/admin/uploads.html", uploads=upload_list, user=username)

@bp.route('/admin/start_upload/<username>/<xmlname>', methods=['GET'])
@login_required
@roles_accepted('admin', 'audit')
def start_load_to_neo4j(username,xmlname):
    upload_list = uploads.initiate_background_load_to_neo4j(username,xmlname) 
    return redirect(url_for('admin.list_uploads', username=username))

@bp.route('/admin/list_threads', methods=['GET'])
@roles_accepted('admin', 'audit')
def list_threads():
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
@roles_accepted('member', 'admin')
def show_upload_log(username,xmlfile):
    upload_folder = uploads.get_upload_folder(current_user.username)
    fname = os.path.join(upload_folder,xmlfile + ".log")
    result_list = Unpickler(open(fname,"rb")).load()
    return render_template("/admin/load_result.html", batch_events=result_list)




@bp.route('/admin/xml_delete/<username>/<xmlfile>')
@login_required
@roles_accepted('admin', 'audit')
def xml_delete(username,xmlfile):
    uploads.delete_files(username,xmlfile)
    return redirect(url_for('admin.list_uploads', username=username))

