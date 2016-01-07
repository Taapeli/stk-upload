# coding=UTF-8
# Taapeli harjoitustyö @ Sss 2016
# Source http://syntx.io/how-to-upload-files-in-python-and-flask/
# Source http://flask.pocoo.org/docs/0.10/patterns/fileuploads/
# JMä 30.12.2015

import os
from flask import Flask, redirect, url_for
from werkzeug import secure_filename

UPLOAD_FOLDER = '/tmp'
ALLOWED_EXTENSIONS = set(['txt', 'csv'])

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

def upload_file(infile, fmt='list'):
    """ Save file 'infile' in the upload folder 
    and show as 'list' or 'table' """
    filename = normalized_name(infile)
    infile.save(filename)
    return redirect(url_for('nayta1', filename=filename, fmt=fmt))

def normalized_name(infile):
    """ Tarkastetaan tiedostonimi ja palautetaan täysi polkunimi """
    # Tiedostonimi saatu?
    if not infile:
        # 404 Not Found
        return redirect(url_for('virhesivu', code=404, text="tiedostonimi puuttuu"))
    # Tiedostopääte ok?
    ok_name = '.' in infile.filename and \
           infile.filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS
    if not ok_name:
        # 415 Unsupported Media Type
        return redirect(url_for('virhesivu', code=415, text=infile.filename))
    # Palautetaan nimi ilman ylimääräisiä hakemistotasoja
    return secure_filename(infile.filename)

def fullname(name):
    """ Palauttaa täyden polkunimen """
    return os.path.join(app.config['UPLOAD_FOLDER'], name)
 