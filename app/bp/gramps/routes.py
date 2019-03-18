'''
    Gramps xml file upload

Created on 15.8.2018

@author: jm
'''

import os
import time
import logging 
logger = logging.getLogger('stkserver')

from flask import render_template, request, redirect, url_for, send_from_directory, flash
from flask_security import login_required, roles_accepted, current_user # ,roles_required
from flask_babelex import _

import shareds
from models import loadfile, email, util, syslog 
from . import bp
from ..admin import uploads

@bp.route('/gramps')
@login_required
@roles_accepted('member', 'admin')
def gramps_upload():
    """ Home page gramps input file processing """
    print("-> bp.start.routes.gramps_upload")
    return render_template("/gramps/index_gramps.html")

@bp.route('/gramps/show_log/<xmlfile>')
@roles_accepted('member')
def show_upload_log(xmlfile):
    upload_folder = uploads.get_upload_folder(current_user.username)
    fname = os.path.join(upload_folder,xmlfile + ".log")
    msg = open(fname, encoding="utf-8").read()
    return render_template("/admin/load_result.html", msg=msg)

@bp.route('/gramps/uploads')
@roles_accepted('member', 'admin')
def list_uploads():
    upload_list = uploads.list_uploads(current_user.username) 
    return render_template("/gramps/uploads.html", uploads=upload_list)

@bp.route('/gramps/upload', methods=['POST'])
@roles_accepted('member', 'admin')
def upload_gramps(): 
    """ Load a gramps xml file to temp directory for processing in the server
    """
    try:
        infile = request.files['filenm']
        material = request.form['material']
        logging.debug("Got a {} file '{}'".format(material, infile.filename))

        t0 = time.time()
        upload_folder = uploads.get_upload_folder(current_user.username)
        os.makedirs(upload_folder, exist_ok=True)

        pathname = loadfile.upload_file(infile,upload_folder)
        shareds.tdiff = time.time()-t0

        logname = pathname + ".log"
        uploads.set_meta(current_user.username,infile.filename,
                        status=uploads.STATUS_UPLOADED,
                        upload_time=time.time())
        msg = "{}: User {} uploaded the file {}".format(
            util.format_timestamp(),current_user.username,pathname)
        open(logname,"w", encoding='utf-8').write(msg)
        email.email_admin(
                    "Stk: Gramps XML file uploaded",
                    msg )
        syslog.log(type="gramps file uploaded",file=infile.filename)
    except Exception as e:
        return redirect(url_for('gramps.error_page', code=1, text=str(e)))

    return redirect(url_for('gramps.list_uploads'))
    #return redirect(url_for('gramps.save_loaded_gramps', filename=infile.filename))

@bp.route('/gramps/start_upload/<xmlname>')
@login_required
@roles_accepted('member')
def start_load_to_neo4j(xmlname):
    uploads.initiate_background_load_to_neo4j(current_user.username,xmlname)
    flash(_('Data import from {!r} to database has been started.'.format(xmlname)), 'info')
    return redirect(url_for('gramps.list_uploads'))

@bp.route('/gramps/virhe_lataus/<int:code>/<text>')
@roles_accepted('member', 'admin')
def error_page(code, text=''):
    """ Virhesivu näytetään """
    logging.debug('Virhesivu ' + str(code) )
    return render_template("virhe_lataus.html", code=code, text=text)

@bp.route('/gramps/xml_delete/<xmlfile>')
@roles_accepted('member', 'admin')
def xml_delete(xmlfile):
    uploads.delete_files(current_user.username,xmlfile)
    syslog.log(type="gramps file deleted",file=xmlfile)
    return redirect(url_for('gramps.list_uploads'))

@bp.route('/gramps/xml_download/<xmlfile>')
@roles_accepted('member', 'admin')
def xml_download(xmlfile):
    xml_folder = uploads.get_upload_folder(current_user.username)
    xml_folder = os.path.abspath(xml_folder)
    return send_from_directory(directory=xml_folder, filename=xmlfile, 
                               mimetype="application/gzip",
                               as_attachment=True)
#                                attachment_filename=xmlfile+".gz")
                               