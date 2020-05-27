'''
    Gramps xml file upload

Created on 15.8.2018

@author: jm
'''

import os
import time
import logging 
logger = logging.getLogger('stkserver')

from flask import render_template, request, redirect, url_for, send_from_directory, flash, jsonify
from flask_security import login_required, roles_accepted, current_user # ,roles_required
from flask_babelex import _

import shareds
from models import loadfile, email, util, syslog 
from . import bp
from . import gramps_loader
from ..admin import uploads
#from .models import batch

@bp.route('/gramps')
@login_required
@roles_accepted('research', 'admin')
def gramps_index():
    """ Home page gramps input file processing """
    logger.info("-> bp.start.routes.gramps_index")
    return render_template("/gramps/index_gramps.html")

@bp.route('/gramps/show_log/<xmlfile>')
@login_required
@roles_accepted('research')
def show_upload_log(xmlfile):
    upload_folder = uploads.get_upload_folder(current_user.username)
    fname = os.path.join(upload_folder,xmlfile + ".log")
    msg = open(fname, encoding="utf-8").read()
    logger.info(f"-> bp.gramps.routes.show_upload_log f='{xmlfile}'")
    return render_template("/admin/load_result.html", msg=msg)

@bp.route('/gramps/uploads')
@login_required
@roles_accepted('research', 'admin')
def list_uploads():
    upload_list = uploads.list_uploads(current_user.username) 
    #Not essential: logger.info(f"-> bp.gramps.routes.list_uploads n={len(upload_list)}")
    return render_template("/gramps/uploads.html", uploads=upload_list)

@bp.route('/gramps/upload', methods=['POST'])
@login_required
@roles_accepted('research', 'admin')
def upload_gramps(): 
    """ Load a gramps xml file to temp directory for processing in the server
    """
    try:
        infile = request.files['filenm']
        material = request.form['material']
        #logger.debug("Got a {} file '{}'".format(material, infile.filename))

        t0 = time.time()
        upload_folder = uploads.get_upload_folder(current_user.username)
        os.makedirs(upload_folder, exist_ok=True)

        pathname = loadfile.upload_file(infile,upload_folder)
        shareds.tdiff = time.time()-t0

        logname = pathname + ".log"
        uploads.set_meta(current_user.username,infile.filename,
                        status=uploads.STATUS_UPLOADED,
                        upload_time=time.time())
        msg = f"{util.format_timestamp()}: User {current_user.name} ({current_user.username}) uploaded the file {pathname}"
        open(logname,"w", encoding='utf-8').write(msg)
        email.email_admin(
                    "Stk: Gramps XML file uploaded",
                    msg )
        syslog.log(type="gramps file uploaded",file=infile.filename)
        logger.info(f'-> bp.gramps.routes.upload_gramps/{material} f="{infile.filename}"'
                    f' e={shareds.tdiff:.3f}sek')
    except Exception as e:
        return redirect(url_for('gramps.error_page', code=1, text=str(e)))

    return redirect(url_for('gramps.list_uploads'))
    #return redirect(url_for('gramps.save_loaded_gramps', filename=infile.filename))

@bp.route('/gramps/start_upload/<xmlname>')
@login_required
@roles_accepted('research')
def start_load_to_neo4j(xmlname):
    uploads.initiate_background_load_to_neo4j(current_user.username,xmlname)
    logger.info(f'-> bp.gramps.routes.start_load_to_neo4j f="{os.path.basename(xmlname)}"')
    flash(_("Data import from %(i)s to database has been started.", i=xmlname), 'info')
    return redirect(url_for('gramps.list_uploads'))

@bp.route('/gramps/virhe_lataus/<int:code>/<text>')
@login_required
@roles_accepted('research', 'admin')
def error_page(code, text=''):
    """ Virhesivu näytetään """
    logger.info(f'bp.gramps.routes.error_page/{code}' )
    return render_template("virhe_lataus.html", code=code, text=text)

@bp.route('/gramps/xml_analyze/<xmlfile>')
@login_required
@roles_accepted('research', 'admin')
def xml_analyze(xmlfile):
    references = gramps_loader.analyze(current_user.username, xmlfile)
    logger.info(f'bp.gramps.routes.xml_analyze f="{os.path.basename(xmlfile)}"')
    return render_template("/gramps/analyze_xml.html", 
                           references=references, file=xmlfile)

@bp.route('/gramps/xml_delete/<xmlfile>')
@login_required
@roles_accepted('research', 'admin')
def xml_delete(xmlfile):
    uploads.delete_files(current_user.username,xmlfile)
    logger.info(f'-> bp.gramps.routes.xml_delete f="{os.path.basename(xmlfile)}"')
    syslog.log(type="gramps file deleted",file=xmlfile)
    return redirect(url_for('gramps.list_uploads'))

@bp.route('/gramps/xml_download/<xmlfile>')
@login_required
@roles_accepted('research', 'admin')
def xml_download(xmlfile):
    xml_folder = uploads.get_upload_folder(current_user.username)
    xml_folder = os.path.abspath(xml_folder)
    return send_from_directory(directory=xml_folder, filename=xmlfile, 
                               mimetype="application/gzip",
                               as_attachment=True)
#                                attachment_filename=xmlfile+".gz")

@bp.route('/gramps/batch_delete/<batch_id>')
@login_required
@roles_accepted('research', 'admin')
def batch_delete(batch_id):

    from models.gen.batch_audit import Batch

    filename = Batch.get_filename(current_user.username,batch_id)
    metafile = filename.replace("_clean.",".") + ".meta"
    if os.path.exists(metafile):
        data = eval(open(metafile).read())
        if data.get('batch_id') == batch_id:
            del data['batch_id']
            data['status'] = uploads.STATUS_REMOVED
            open(metafile,"w").write(repr(data))
    Batch.delete_batch(current_user.username,batch_id)
    logger.info(f'-> bp.gramps.routes.batch_delete f="{batch_id}"')
    syslog.log(type="batch_id deleted",batch_id=batch_id) 
    flash(_("Batch id %(batch_id)s has been deleted", batch_id=batch_id), 'info')
    referrer = request.headers.get("Referer")                               
    return redirect(referrer)

@bp.route('/gramps/get_progress/<xmlfile>')
@login_required
@roles_accepted('research', 'admin')
def get_progress(xmlfile):
    xml_folder = uploads.get_upload_folder(current_user.username)
    xml_folder = os.path.abspath(xml_folder)
    filename = os.path.join(xml_folder,xmlfile)
    metaname = filename.replace("_clean.",".") + ".meta"
    meta = uploads.get_meta(metaname)

    status = meta.get("status")
    if status is None:
        return jsonify({"status":"error"})

    counts = meta.get("counts")
    if counts is None:
        return jsonify({"status":status,"progress":0})

    progress = meta.get("progress")
    if progress is None:
        return jsonify({"status":status,"progress":0})

    total = 0
    total += counts["citation_cnt"]
    total += counts["event_cnt"]
    total += counts["family_cnt"]
    total += counts["note_cnt"]
    total += 2*counts["person_cnt"] # include refnames update
    total += counts["place_cnt"]
    total += counts["object_cnt"]
    total += counts["source_cnt"]
    total += counts["repository_cnt"]
    done = 0
    done += progress.get("Citation", 0)
    done += progress.get("Event_gramps", 0)
    done += progress.get("Family_gramps", 0)
    done += progress.get("Note", 0)
    done += progress.get("Person_gramps", 0)
    done += progress.get("Place_gramps", 0)
    done += progress.get("Media", 0)
    done += progress.get("Source_gramps", 0)
    done += progress.get("Repository", 0)
    done += progress.get("refnames", 0)
    rsp = {
        "status":status,
        "progress":99*done//total,
        "batch_id":meta.get("batch_id"),
    }
    return jsonify(rsp)
