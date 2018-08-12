'''
Created on 8.8.2018

@author: jm

 Administrator operations page urls
 
'''
import logging 
logger = logging.getLogger('stkserver')

from flask import render_template, request, redirect, url_for 
from flask_security import roles_accepted, roles_required, current_user

import shareds
from models import dbutil, dataupdater
from .models import DataAdmin
from .forms import ListEmailsForm
from . import bp

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
@bp.route('/admin/aseta/estimated_dates')
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
    message = dataupdater.set_person_refnames()
    return render_template("/admin/talletettu.html", text=message, uri=dburi)

#TODO Kuuluisiko kokonaisuuteen security??
@bp.route('/admin/list_emails',  methods=['GET', 'POST'])
#    @login_required
#    @roles_required('admin')
def list_emails():
    form = ListEmailsForm()
    if request.method == 'POST':
        # Register a new email
        shareds.user_datastore.allowed_email_register(form.allowed_email.data,
                                                      form.default_role.data)
        
    lista = shareds.user_datastore.get_allowed_emails()
    return render_template("/security/list_allowed_emails.html", emails=lista, 
                           form=form)


#TODO Kuuluisiko kokonaisuuteen security??
@bp.route('/admin/list_users', methods=['GET'])
# @login_required
def list_users():
    # Käytetään neo4juserdatastorea
    lista = shareds.user_datastore.get_users()
    return render_template("/security/list_users.html", users=lista)  

