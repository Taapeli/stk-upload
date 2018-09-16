'''
    Gramps xml file upload

Created on 15.8.2018

@author: jm
'''

import os
import time
import threading
from pathlib import Path
from pickle import Pickler
import traceback

import logging 
logger = logging.getLogger('stkserver')

from flask import render_template, request, redirect, url_for 
from flask_security import roles_accepted, current_user
from flask_babelex import _

import shareds
from models import dbutil, loadfile
from . import bp
from .gramps_loader import xml_to_neo4j
from .batchlogger import Log
from pickle import Unpickler

#===============================================================================
# Background loading of a Gramps XML file
# 
# 1. The user uploads an XML file using the user interface. This is handled by the function "upload_gramps". 
#    The file is stored in a global temporary folder (e.g. /tmp).
# 
# 2. The function redirects to "save_loaded_gramps" which calls "initiate_background_load_to_neo4j"
# 
# 3. The function "initiate_background_load_to_neo4j" starts a background thread to do the actual database load. 
#    The thread executes the function "background_load_to_neo4j" which calls the actual logic in
#    "gramps_loader.xml_to_neo4j"
#    
#    For each user there is the folder "uploads/<userid>" that contains "log files" for the loads
#    performed by the user. These log files are also used to keep track of the loading progress
#    as described below.
#    
#    The function "initiate_background_load_to_neo4j" generates a unique file name for the log file.
#    This file in the upload folder serves as a marker while the load is running and finally contains the log
#    data for the load. The file name consists of three parts:
# 
#    <timestamp>.<xml-file>.<state>
#    
#    <timestamp> is the time when the load started (as seconds returned by the time.time() function - only
#    the integer part is retained).
#    
#    <xml-file> is the name of the file being loaded to the database (.xml or .gramps).
#    
#    The suffix <state> is one of
#    
#    - loading
#    - loading.done
#    - loading.failed
#    
#    The suffix is initially "loading" and remains so while the Neo4j load is being processed. If the load 
#    completes successfully then ".done" is appended to the file name (i.e. the file is renamed). 
#    If there is an error (an exception is thrown) then ".failed" is appended.
#    
# 4. It is conceivable that the thread doing the load is somehow stopped without being able to rename the file
#    to indicate a completion or failure. Then the file name suffix remains ".loading" indefinitely. 
#    This situation is noticed by the "i_am_alive" thread whose only purpose is to update the timestamp of
#    ("touch") the log file as long as the loading thread is running. This update will happen every 10 seconds.
#    
#    This enables the user interface to notice that the load has failed. The load will be marked as "in error"
#    if the log file is not updated (touched) for a minute.
#    
# 5. If the load completes successfully then the file is renamed with a ".done" suffix as explained above.
#    The result of the load is also stored in the file. The result is returned by the "xml_to_neo4j" function
#    as a list of Log recerds. This list is serialized using the "pickle" module and stored in the file.
#    THe user interface is then able to retrieve the Log records and display them to the user (in function
#    upload_info).
#    
# 6. The "uploads" function displays a list of the load operations performed by the user. This function 
#    will display the state of the file according to the file name suffix and also indicates an error if the
#    file is "loading" but has not been updated for minute. The list is automatically updated every 30 seconds.
# 
#    The user is redirected to this screen immediately after initiating a load operation. The user can also 
#    go to the screen from the main display.
#===============================================================================
   

def get_upload_folder(): 
    return os.path.join("uploads", current_user.username)

def i_am_alive(logname,parent_thread):
    while os.path.exists(logname) and parent_thread.is_alive():
        Path(logname).touch()
        time.sleep(10)

def background_load_to_neo4j(pathname,userid,logname):
    try:
        open(logname,"w").write("started")
        threading.Thread(target=lambda: i_am_alive(logname,threading.current_thread())).start()
        steps = xml_to_neo4j(pathname,userid)
        for step in steps:
            print(step)
        Pickler(open(logname,"wb")).dump(steps)
        os.rename(logname,logname+".done")
    except:
        traceback.print_exc()
        res = traceback.format_exc()
        open(logname,"w").write(res)
        os.rename(logname,logname+".failed")


def initiate_background_load_to_neo4j(filename, userid):
    import subprocess
    pathname = loadfile.fullname(filename)
    upload_folder = get_upload_folder()
    os.makedirs(upload_folder, exist_ok=True)
    logname = "{}.{}.loading".format(int(time.time()),filename)
    logname = os.path.join(upload_folder,logname)
    #===========================================================================
    # subprocess.Popen("PYTHONPATH=app python runload.py " 
    #                  + pathname + " " 
    #                  + username + " "
    #                  + logname,
    #                   shell=True)
    #===========================================================================
    def background_load_to_neo4j_thread():
        background_load_to_neo4j(pathname,userid,logname)
    threading.Thread(target=background_load_to_neo4j_thread).start()
    
    for i in range(10):
        if os.path.exists(logname): return True
        time.sleep(0.5)
    return False


@bp.route('/gramps/upload_info/<upload>')
@roles_accepted('member', 'admin')
def upload_info(upload): 
    upload_folder = get_upload_folder()
    fname = os.path.join(upload_folder,upload + ".loading.done")
    result_list = Unpickler(open(fname,"rb")).load()
    return render_template("/gramps/result.html", batch_events=result_list)

@bp.route('/gramps/uploads')
@roles_accepted('member', 'admin')
def uploads():
    upload_folder = get_upload_folder()
    try:
        names = sorted([name for name in os.listdir(upload_folder)]) 
    except:
        names = []
    uploads = []
    class Upload: pass
    for name in names:
        fname = os.path.join(upload_folder,name)
        stat = os.stat(fname)
        parts = name.split(".",maxsplit=1)
        starttime = parts[0]
        name1 = parts[1] # xmlfile.loading...
        xmlname = None
        if fname.endswith(".loading"):
            xmlname = name1.rsplit(".",maxsplit=1)[0]
            if stat.st_mtime < time.time() - 60: # not updated in a minute -> assume failed
                status = _("ERROR")
            else:
                status = _("LOADING") 
        elif fname.endswith(".done"):
            xmlname = name1.rsplit(".",maxsplit=2)[0]
            status = _("DONE")
        elif fname.endswith(".failed"):
            xmlname = name1.rsplit(".",maxsplit=2)[0]
            status = _("FAILED")
        if xmlname:
            upload = Upload()
            upload.xmlname = xmlname
            upload.status = status
            upload.done = (status == _("DONE"))
            upload.starttime = int(starttime)
            upload.starttime_s = time.strftime("%Y-%m-%d %H.%M.%S",time.localtime(upload.starttime))
            uploads.append(upload)
    return render_template("/gramps/uploads.html", uploads=uploads)

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
        return redirect(url_for('gramps.error_page', code=1, text=str(e)))

    return redirect(url_for('gramps.save_loaded_gramps', filename=infile.filename))



@bp.route('/gramps/save/xml_file/<string:filename>')
@roles_accepted('member', 'admin')
def save_loaded_gramps(filename):
    """ Save loaded gramps data to the database """
    #TODO: Latauksen onnistuttua perusta uusi Batch-erä (suoritusaika shareds.tdiff)
    pathname = loadfile.fullname(filename)
    result_list = []
#     dburi = dbutil.get_server_location()
    try:
        # gramps backup xml file to Neo4j db
        #result_list = xml_to_neo4j(pathname, current_user.username)
        initiate_background_load_to_neo4j(filename, current_user.username)
        return redirect(url_for('gramps.uploads'))
    except KeyError as e:
        return redirect(url_for('gramps.error_page', code=1, \
                                text="Missing proper column title: " + str(e)))
    return render_template("/gramps/result.html", batch_events=result_list)


@bp.route('/gramps/virhe_lataus/<int:code>/<text>')
def error_page(code, text=''):
    """ Virhesivu näytetään """
    logging.debug('Virhesivu ' + str(code) )
    return render_template("virhe_lataus.html", code=code, text=text)

