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

# Admin start page
@bp.route('/audit/movein/<batch_name>',  methods=['GET', 'POST'])
@login_required
@roles_accepted('admin', 'audit')
def move_in(batch_name):
    """ Moving selected Batch to Isotammi database """    
    print(f"-> bp.audit.routes.move_in {batch_name}")
    batch_reader = Batches()
    user, batch_id, tstring, labels = batch_reader.get_batch_stats(batch_name)
    logger.info(f'# User batches {user} / {batch_id}')

    return render_template('/audit/approve.html', user=user, batch=batch_id, 
                           time=tstring, label_nodes=labels)

@bp.route('/audit/movenow',  methods=['POST'])
@login_required
@roles_accepted('admin', 'audit')
def move_now():
    """ Move the accepted Batch to Isotammi database """
    user = request.form['user']
    batch_id = request.form['batch']
    
    logger.info(f"-> bp.audit.routes.move_now {user} / {batch_id}")
    return render_template('/audit/got_in.html', user=user, batch=batch_id)

