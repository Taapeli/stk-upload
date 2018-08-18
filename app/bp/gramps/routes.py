'''
    Gramps xml file upload

Created on 15.8.2018

@author: jm
'''

import logging 
logger = logging.getLogger('stkserver')

from flask import render_template, request, redirect, url_for 
from flask_security import roles_accepted, current_user
import time
#import .gramps_loader # Loading a gramps xml file

import shareds
from models import dbutil, loadfile
from . import bp
from .gramps_loader import xml_to_neo4j


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
        loadfile.upload_file(infile)
        shareds.tdiff = time.time()-t0

    except Exception as e:
        return redirect(url_for('error_page', code=1, text=str(e)))

    return redirect(url_for('gramps.save_loaded_gramps', filename=infile.filename))


@bp.route('/gramps/save/xml_file/<string:filename>')
@roles_accepted('member', 'admin')
def save_loaded_gramps(filename):
    """ Save loaded gramps data to the database """
    #TODO: Latauksen onnistuttua perusta uusi Batch-erä (suoritusaika shareds.tdiff)
    pathname = loadfile.fullname(filename)
    dburi = dbutil.get_server_location()
    try:
        # gramps backup xml file to Neo4j db
        result_list = xml_to_neo4j(pathname, current_user.username)
    except KeyError as e:
        return redirect(url_for('gramps.error_page', code=1, \
                                text="Missing proper column title: " + str(e)))
    return render_template("/gramps/result.html", batch_events=result_list, uri=dburi)


@bp.route('/gramps/virhe_lataus/<int:code>/<text>')
def error_page(code, text=''):
    """ Virhesivu näytetään """
    logging.debug('Virhesivu ' + str(code) )
    return render_template("virhe_lataus.html", code=code, text=text)

