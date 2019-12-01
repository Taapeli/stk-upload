'''
Created on 28.11.2019

 Auditor operations page urls
 
'''
from . import bp
from bp.admin.users import Batches

import logging
logger = logging.getLogger('stkserver')

from flask import render_template, request #, redirect, url_for , send_from_directory, flash, session, jsonify
from flask_security import login_required, roles_accepted #, roles_required, current_user
# from flask_babelex import _
# 
# import shareds

@bp.route('/audit')
#TODO: Audit homa pege is missing
def audit_home():
    return render_template('/audit/index.html')

@bp.route('/audit/movein/<batch_name>',  methods=['GET', 'POST'])
@login_required
@roles_accepted('admin', 'audit')
def move_in_1(batch_name):
    """ Moving selected Batch to Isotammi database """    
    user, batch_id, tstring, labels = Batches.get_batch_stats(batch_name)
    logger.info(f' bp.audit.routes.move_in_1 batch {user} / {batch_name}')

    return render_template('/audit/move_in_1.html', user=user, batch=batch_id, 
                           time=tstring, label_nodes=labels)

@bp.route('/audit/movenow',  methods=['POST'])
@login_required
@roles_accepted('admin', 'audit')
def move_in_2():
    """ Move the accepted Batch to Isotammi database """
    user = request.form['user']
    batch_id = request.form['batch']
    
    logger.info(f' bp.audit.routes.move_in_2 batch {user} / {batch_id}')
    return render_template('/audit/move_in_2.html', user=user, batch=batch_id)

