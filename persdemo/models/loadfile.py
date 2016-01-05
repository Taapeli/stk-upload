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

def upload_file(infile):
    """ Save file 'infile' in upload folder """
    if not infile:
        # 404 Not Found
        return redirect(url_for('virhesivu', code=404, text="tiedostonimi puuttuu"))
    if not allowed_file(infile.filename):
        # 415 Unsupported Media Type
        return redirect(url_for('virhesivu', code=415, text=infile.filename))
        
    filename = secure_filename(infile.filename)
    infile.save(fullname(filename))
    return redirect(url_for('nayta1', filename=filename))
    
def fullname(name):
    return os.path.join(app.config['UPLOAD_FOLDER'], name)

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS
