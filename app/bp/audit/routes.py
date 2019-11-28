'''
Created on 28.11.2019

 Auditor operations page urls
 
'''
from . import bp

from flask import render_template, request, redirect, url_for, send_from_directory, flash, session, jsonify
from flask_security import login_required, roles_accepted, roles_required, current_user
from flask_babelex import _

import shareds

# Admin start page
@bp.route('/audit/movein/<batch>',  methods=['GET', 'POST'])
@login_required
@roles_accepted('admin', 'audit')
def move_in(batch):
    """ Move accepted Batch to Suomi-kanta """    
    print(f"-> bp.audit.routes.move_in {batch}")
    return render_template('/audit/approve.html', batch=batch)

