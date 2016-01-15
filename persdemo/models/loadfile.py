# coding=UTF-8
# Taapeli harjoitustyö @ Sss 2016
# Source http://syntx.io/how-to-upload-files-in-python-and-flask/
# Source http://flask.pocoo.org/docs/0.10/patterns/fileuploads/
# JMä 30.12.2015

import os
import logging
from flask import Flask, redirect, url_for
from werkzeug import secure_filename

if 'TMPDIR' in os.environ:
    UPLOAD_FOLDER = os.environ['TMPDIR']
if 'TMP' in os.environ:
    UPLOAD_FOLDER = os.environ['TMP']
else:
    UPLOAD_FOLDER = '/tmp'

ALLOWED_EXTENSIONS = set(['txt', 'csv'])

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

def upload_file(infile, fmt='list'):
    """ Save file 'infile' in the upload folder 
    and show as 'list' or 'table' """
    try:
        filename = normalized_name(infile)
        kokonimi=fullname(filename)
    except IOError as e:
        # 415 Unsupported Media Type
        return redirect(url_for('virhesivu', code=415, text=str(e)))
        
    infile.save(kokonimi)
    logging.debug('Tiedosto "' + kokonimi + '" talletettu')
    return redirect(url_for('nayta1', filename=filename, fmt=fmt))

def normalized_name(infile):
    """ Tarkastetaan tiedostonimi ja palautetaan täysi polkunimi """
    # Tiedostonimi saatu?
    if not infile:
        raise IOError('Tiedostonimi puuttuu')
    # Tiedostopääte ok?
    ok_name = '.' in infile.filename and \
           infile.filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS
    if not ok_name:
        raise IOError('Tiedostopääte ei ole sallittu')
    # Palautetaan nimi ilman ylimääräisiä hakemistotasoja
    return secure_filename(infile.filename)

def fullname(name):
    """ Palauttaa täyden polkunimen """
    if not name:
        return ''
    else:
        return os.path.join(app.config['UPLOAD_FOLDER'], name)
