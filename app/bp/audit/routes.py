'''
Created on 28.11.2019

 Auditor operations page urls
 
'''
from . import bp
from models.gen.batch import Batch

import logging
logger = logging.getLogger('stkserver')

from flask import render_template, request, redirect, url_for #, flash, send_from_directory, session, jsonify
from flask_security import login_required, roles_accepted, current_user
#from flask_babelex import _

import shareds
from .models.batch_merge import Batch_merge
from bp.admin import uploads
from models import syslog 

@bp.route('/audit')
@login_required
@roles_accepted('audit')
def audit_home():
    return render_template('/audit/index.html')

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


@bp.route('/audit/movein/<batch_name>',  methods=['GET', 'POST'])
@login_required
@roles_accepted('audit')
def move_in_1(batch_name):
    """ Confirm Batch move to Isotammi database """    
    user, batch_id, tstring, labels = Batch.get_batch_stats(batch_name)
    total = 0
    for _label, cnt in labels:
        total += cnt
    logger.info(f' bp.audit.routes.move_in_1 {user} / {batch_name}, total {total} nodes')

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
    logger.info(f' bp.audit.routes.move_in_2 {owner} / {batch_id}')
    merger = Batch_merge()
    msg = merger.move_whole_batch(batch_id, owner, auditor)
    syslog.log(type="batch to Common data", batch=batch_id, by=owner, msg=msg)
    return redirect(url_for('audit.move_in_1', batch_name=batch_id))
