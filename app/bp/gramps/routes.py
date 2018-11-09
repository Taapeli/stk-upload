'''
    Gramps xml file upload

Created on 15.8.2018

@author: jm
'''

import os
import time

import logging 
logger = logging.getLogger('stkserver')

from flask import render_template, request, redirect, url_for, send_from_directory
from flask_security import roles_accepted, current_user
#from flask_babelex import _

import shareds
from models import loadfile, email, util    # dbutil, 
#from models import email
from . import bp
#from .gramps_loader import xml_to_neo4j
#from bp.admin.uploads import initiate_background_load_to_neo4j
#from .batchlogger import Log
from pickle import Unpickler

from bp.admin.uploads import initiate_background_load_to_neo4j
from ..admin import uploads

@bp.route('/gramps/upload_info/<upload>')
@roles_accepted('member', 'admin')
def upload_info(upload): 
    upload_folder = uploads.get_upload_folder(current_user.username)
    fname = os.path.join(upload_folder,upload + ".loading.done")
    result_list = Unpickler(open(fname,"rb")).load()
    return render_template("/gramps/result.html", batch_events=result_list)

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
                        status="uploaded",
                        upload_time=time.time())
        msg = "{}: User {} uploaded the file {}".format(
            util.format_timestamp(),current_user.username,pathname)
        open(logname,"w").write(msg)
        email.email_admin(
                    "Stk: Gramps XML file uploaded",
                    msg )
    except Exception as e:
        return redirect(url_for('gramps.error_page', code=1, text=str(e)))

    return redirect(url_for('gramps.list_uploads'))
    #return redirect(url_for('gramps.save_loaded_gramps', filename=infile.filename))


# @bp.route('/gramps/save/xml_file/<string:filename>')
# @roles_accepted('member', 'admin')
# def save_loaded_gramps(filename):
#     """ Save loaded gramps data to the database """
#     #TODO: Latauksen onnistuttua perusta uusi Batch-erä (suoritusaika shareds.tdiff)
# #    pathname = loadfile.fullname(filename)
#     result_list = []
# #     dburi = dbutil.get_server_location()
#     try:
#         # gramps backup xml file to Neo4j db
#         #result_list = xml_to_neo4j(pathname, current_user.username)
#         initiate_background_load_to_neo4j(filename, current_user.username)
#         return redirect(url_for('gramps.uploads'))
#     except KeyError as e:
#         return redirect(url_for('gramps.error_page', code=1, \
#                                 text="Missing proper column title: " + str(e)))
#     return render_template("/gramps/result.html", batch_events=result_list)


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
    return redirect(url_for('gramps.list_uploads'))

@bp.route('/gramps/xml_download/<xmlfile>')
@roles_accepted('admin', 'audit')
def xml_download(xmlfile):
    xml_folder = uploads.get_upload_folder(current_user.username)
    xml_folder = os.path.abspath(xml_folder)
    return send_from_directory(directory=xml_folder, filename=xmlfile, 
                               mimetype="application/gzip",
                               as_attachment=True)
                               #attachment_filename=xmlfile+".gz") 