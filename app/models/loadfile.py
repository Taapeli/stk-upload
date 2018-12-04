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

ALLOWED_EXTENSIONS = set(['gramps', 'txt', 'csv', 'xml'])

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER


def upload_file(infile,folder=None, secure=False):
    """ Save file 'infile' in the upload folder 
        and return the final full name of the file 
    """
    if not folder:
        folder = app.config['UPLOAD_FOLDER']
    try:
        filename = normalized_name(infile.filename)
    except Exception:
        logging.debug('Normalizing file name "' + infile.filename + '" fails')
        raise
    if secure:    
        fullname =  os.path.join(folder, secure_filename(filename))
    else:    
        fullname =  os.path.join(folder, filename)
    infile.save(fullname)
    logging.debug('Tiedosto "' + fullname + '" talletettu')
    return fullname

def normalized_name(in_name, secure=False):
    """ Tarkastetaan tiedostonimi ja palautetaan täysi polkunimi """
    # Tiedostonimi saatu?
    if not in_name:
        raise IOError('Tiedostonimi puuttuu')
    # Tiedostopääte ok?
    ok_name = '.' in in_name and \
           in_name.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS
    if not ok_name:
        raise ValueError('Tiedostopääte nimessä "' + in_name + \
              '" pitää olla .gramps .csv .txt tai .xml ')
    # Palautetaan nimi ilman ylimääräisiä hakemistotasoja
    if secure:
        return secure_filename(in_name)
    return in_name

def fullname(name, secure=False):
    """ Palauttaa täyden polkunimen """
    if not name:
        return ''
    elif secure:
        return os.path.join(app.config['UPLOAD_FOLDER'], secure_filename(name))
    return os.path.join(app.config['UPLOAD_FOLDER'], name)

def status_update(status):
    ''' STUB: Store process progress status 0..100 in metadata for display
        For ex. status = {status:"started", percent:1}
    '''
    print(" - models.loadfile.status_update: Progress {}".format(status))
    #Todo Store status info to *.meta file
