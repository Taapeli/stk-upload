'''
Created on 28.11.2019

 Auditor operations page urls
 
'''
from . import bp
import time

import logging
from bp.admin.cvs_refnames import load_refnames
from models import dataupdater
from io import StringIO, BytesIO
import csv
from models.gen.person import Person
logger = logging.getLogger('stkserver')

from flask import render_template, request, redirect, url_for #, flash, send_from_directory, session, jsonify
from flask import send_file
from flask_security import login_required, roles_accepted, current_user
#from flask_babelex import _

import shareds
from models.gen.batch_audit import Batch, Audit
from .models.batch_merge import Batch_merge
#from .models.audition import Audition

from bp.admin import uploads
from models import syslog , loadfile, datareader, dbutil

@bp.route('/audit')
@login_required
@roles_accepted('audit')
def audit_home():
    return render_template('/audit/index.html')

# ------------------------- User Gramps uploads --------------------------------

@bp.route('/audit/list_uploads', methods=['GET'])
@login_required
@roles_accepted('audit')
def list_uploads():
    ''' Show Batches

        The list of Gramps uploads is filtered by an existing Batch node
    '''
    users = shareds.user_datastore.get_users()
    upload_list = list(uploads.list_uploads_all(users))
    logger.info(f"-> bp.audit.routes.list_uploads")
    return render_template("/audit/batches.html", uploads=upload_list )


# --------------------- Move Batch to Approved data ----------------------------

@bp.route('/audit/movein/<batch_name>',  methods=['GET', 'POST'])
@login_required
@roles_accepted('audit')
def move_in_1(batch_name):
    """ Confirm Batch move to Isotammi database """    
    user, batch_id, tstring, labels = Batch.get_batch_stats(batch_name)
    total = 0
    for _label, cnt in labels:
        total += cnt
    # Not needed: logger.info(f' bp.audit.routes.move_in_1 {user} / {batch_name}, total {total} nodes')

    return render_template('/audit/move_in_1.html', user=user, batch=batch_id, 
                           label_nodes=labels, total=total, time=tstring)

@bp.route('/audit/movenow',  methods=['POST'])
@login_required
@roles_accepted('audit')
def move_in_2():
    """ Move the accepted Batch to Isotammi database """
    owner = request.form['user']
    batch_id = request.form['batch']
    auditor = current_user.username
    logger.info(f' bp.audit.routes.move_in_2 u={owner} b={batch_id}')
    merger = Batch_merge()
    msg = merger.move_whole_batch(batch_id, owner, auditor)
    syslog.log(type="batch to Common data", batch=batch_id, by=owner, msg=msg)
    return redirect(url_for('audit.move_in_1', batch_name=batch_id))


# --------------------- List Approved data batches ----------------------------

@bp.route('/audit/approvals/<who>',  methods=['GET', 'POST'])
@login_required
@roles_accepted('audit')
def audit_approvals(who=None):
    """ List Audit batches """
    t0 = time.time()
    if who == "all":
        auditor=None
    else:
        auditor = current_user.username
    titles, batches = Audit.get_auditor_stats(auditor)
    # {'matti/2020-01-03.001/13.01.2020 20:30': {'Note': 17, 'Place': 30, 'Repository': 3}, 
    #  'teppo/2020-01-03.002/23.01.2020 15:52': {...} ...}
    total = 0
    for key in batches.keys():
        #print(key + ":")
        for _lbl, cnt in batches[key].items():
            #print (f'    {_lbl} = {cnt}')
            total += cnt
    logger.info(f' bp.audit.routes.audit_approvals {auditor} {len(batches)} batches, total {total} nodes')

    return render_template('/audit/approvals.html', user=auditor, total=total,
                           titles=titles, batches=batches, elapsed=time.time()-t0)

# Refnames home page
@bp.route('/audit/refnames')
@login_required
@roles_accepted('audit')
def refnames():
    """ Operations for reference names """
    return render_template("/audit/reference.html")

@bp.route('/audit/set/refnames')
@login_required
@roles_accepted('member', 'admin', 'audit')
def set_all_person_refnames():
    """ Setting reference names for all persons """
    dburi = dbutil.get_server_location()
    (refname_count, _sortname_count) = dataupdater.set_person_name_properties(ops=['refname']) or _('Done')
    logger.info(f"-> bp.audit.routes.set_all_person_refnames n={refname_count}")
    return render_template("/audit/talletettu.html", uri=dburi, 
                           text=f'Updated {_sortname_count} person sortnames, {refname_count} refnames')


@bp.route('/audit/download/refnames')
@login_required
@roles_accepted('audit')
def download_refnames():
    """Download reference names as a CSV file"""
    logger.info(f"-> bp.audit.routes.download_refnames") # n={refname_count}")
    with StringIO() as f:
        writer = csv.writer(f)
        hdrs = "Name,Refname,Reftype,Gender,Source,Note".split(",")
        writer.writerow(hdrs)
        refnames = datareader.read_refnames()
        for refname in refnames:
            row = [refname.name,
                   refname.refname,
                   refname.reftype,
                   Person.convert_sex_to_str(refname.sex),
                   refname.source]
            writer.writerow(row)
        csvdata = f.getvalue()
        f2 = BytesIO(csvdata.encode("utf-8"))
        f2.seek(0)
        return send_file(f2, mimetype='text/csv', as_attachment=True, attachment_filename="refnames.csv") 


@bp.route('/audit/upload_csv', methods=['POST'])
@login_required
@roles_accepted('audit')
def upload_csv():
    """ Load a cvs file to temp directory for processing in the server
    """
    try:
        infile = request.files['filenm']
        material = request.form['material']
        logging.info(f"-> bp.audit.routes.upload_csv/{material} f='{infile.filename}'")

        loadfile.upload_file(infile)
        if 'destroy' in request.form and request.form['destroy'] == 'all':
            logger.info("-> bp.audit.routes.upload_csv/delete_all_Refnames")
            datareader.recreate_refnames()

    except Exception as e:
        return redirect(url_for('virhesivu', code=1, text=str(e)))

    return redirect(url_for('audit.save_loaded_csv', filename=infile.filename, subj=material))

@bp.route('/audit/save/<string:subj>/<string:filename>')
@login_required
@roles_accepted('audit')
def save_loaded_csv(filename, subj):
    """ Save loaded cvs data to the database """
    pathname = loadfile.fullname(filename)
    dburi = dbutil.get_server_location()
    logging.info(f"-> bp.audit.routes.save_loaded_csv/{subj} f='{filename}'")
    try:
        if subj == 'refnames':    # Stores Refname objects
            status = load_refnames(pathname)
        else:
            return redirect(url_for('virhesivu', code=1, text= \
                _("Data type '{}' is not supported").format(subj)))
    except KeyError as e:
        return render_template("virhe_lataus.html", code=1, \
               text=_("Missing proper column title: ") + str(e))
    return render_template("/audit/talletettu.html", text=status, uri=dburi)
