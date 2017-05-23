# coding=UTF-8
# Taapeli harjoitustyö @ Sss 2016
# Source http://syntx.io/how-to-upload-files-in-python-and-flask/
# Source http://flask.pocoo.org/docs/0.10/patterns/fileuploads/
# JMä 30.12.2015

import os
import logging
from flask import Flask
from werkzeug.utils import secure_filename

if 'TMPDIR' in os.environ:
    UPLOAD_FOLDER = os.environ['TMPDIR']
elif 'TMP' in os.environ:
    UPLOAD_FOLDER = os.environ['TMP']
else:
    UPLOAD_FOLDER = os.sep + 'tmp'

ALLOWED_EXTENSIONS = set(['txt', 'csv', 'xml'])

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER


def upload_file(infile):
    """ Save file 'infile' in the upload folder 
        and return a list of row dictionaries 
    """
    try:
        filename = normalized_name(infile.filename)
    except Exception:
        logging.debug('Tiedostonimen "' + infile.filename + '" normalisointi ei onnaa')
        raise
        
    kokonimi=fullname(filename)
    infile.save(kokonimi)
    logging.debug('Tiedosto "' + kokonimi + '" talletettu')
    return (kokonimi)

def normalized_name(in_name):
    """ Tarkastetaan tiedostonimi ja palautetaan täysi polkunimi """
    # Tiedostonimi saatu?
    if not in_name:
        raise IOError('Tiedostonimi puuttuu')
    # Tiedostopääte ok?
    ok_name = '.' in in_name and \
           in_name.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS
    if not ok_name:
        raise ValueError('Tiedostopääte nimessä "' + in_name + \
              '" pitää olla .csv .txt tai .xml ')
    # Palautetaan nimi ilman ylimääräisiä hakemistotasoja
    return secure_filename(in_name)

def fullname(name):
    """ Palauttaa täyden polkunimen """
    if not name:
        return ''
    else:
        return os.path.join(app.config['UPLOAD_FOLDER'], name)
