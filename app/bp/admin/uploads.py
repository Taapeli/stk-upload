'''
Created on 8.8.2018

@author: jm

 Administrator operations page urls
 
'''
import os
import pprint
import time
import threading
from pathlib import Path
from pickle import Pickler
import traceback

import logging 
logger = logging.getLogger('stkserver')

from flask_babelex import _

from models import loadfile
from ..gramps import gramps_loader
from models import email


#===============================================================================
# Background loading of a Gramps XML file
# 
# 1. The user uploads an XML file using the user interface. This is handled by the function "upload_gramps". 
#    The file is stored in a global temporary folder (e.g. /tmp).
# 
# 2. The function redirects to "list_uploads" which shows the XML files uploaded by this user. This list shows 
#    - the
#
# 3. The admin user can see all users' uploads by going to the user list screen and clicking the link 'uploads'. 
#
# 4. The admin user also sees a list of the uplaoded file for a user but he sees more information:
#    which calls "initiate_background_load_to_neo4j"
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
   

def get_upload_folder(username): 
    return os.path.join("uploads", username)

def set_meta(username,filename,**kwargs):
    upload_folder = get_upload_folder(username) 
    name = "{}.meta".format(filename)
    metaname = os.path.join(upload_folder,name)
    try:
        meta = eval(open(metaname).read())
    except FileNotFoundError:
        meta = {}
    meta.update(kwargs)
    open(metaname,"w").write(pprint.pformat(meta))

def get_meta(metaname):
    try:
        meta = eval(open(metaname).read())
    except FileNotFoundError:
        meta = {}
    return meta

def i_am_alive(metaname,parent_thread):
    while os.path.exists(metaname) and parent_thread.is_alive():
        Path(metaname).touch()
        time.sleep(10)

def background_load_to_neo4j(username,filename):
    upload_folder = get_upload_folder(username) 
    pathname = os.path.join(upload_folder,filename)
    metaname = pathname+".meta"
    logname =  pathname+".log"
    try:
        os.makedirs(upload_folder, exist_ok=True)
        set_meta(username,filename,status="loading")
        this_thread = threading.current_thread()
        threading.Thread(target=lambda: i_am_alive(metaname,this_thread),name="i_am_alive for " + filename).start()
        steps = gramps_loader.xml_to_neo4j(pathname,username)
        for step in steps:
            print(step)
        set_meta(username,filename,status="done")
        msg = "Loaded the file {} from user {} to neo4j".format(pathname,username)
        msg += "\nLog file: {}".format(logname)
        msg += "\n"
        for step in steps:
            msg += "\n{}".format(step)
        open(logname,"w").write(msg)
        email.email_admin(
                    "Stk: Gramps XML file loaded",
                    msg )
    except:
        traceback.print_exc()
        res = traceback.format_exc()
        set_meta(username,filename,status="failed")
        msg = "Loading of file {} from user {} to neo4j FAILED".format(pathname,username)
        msg += "\nLog file: {}".format(logname)
        msg += "\n" + res
        open(logname,"w").write(msg)
        email.email_admin(
                    "Stk: Gramps XML file load FAILED",
                    msg )


def initiate_background_load_to_neo4j(userid,filename):
    #===========================================================================
    # subprocess.Popen("PYTHONPATH=app python runload.py " 
    #                  + pathname + " " 
    #                  + username + " "
    #                  + logname,
    #                   shell=True)
    #===========================================================================
    def background_load_to_neo4j_thread():
        background_load_to_neo4j(userid,filename)
        
    threading.Thread(target=background_load_to_neo4j_thread,name="neo4j load for " + filename).start()
    
    #for i in range(10):
    #    if os.path.exists(logname): return True
    #    time.sleep(0.5)
    return False

def list_uploads(username):
    upload_folder = get_upload_folder(username)
    try:
        names = sorted([name for name in os.listdir(upload_folder)]) 
    except:
        names = []
    uploads = []
    class Upload: pass
    for name in names:
        if name.endswith(".meta"):
            fname = os.path.join(upload_folder,name)
            stat = os.stat(fname)
            xmlname = name.rsplit(".",maxsplit=1)[0]
            meta = get_meta(fname)
            status = meta["status"]
            status_text = None
            if status == "uploaded":
                status_text = _("UPLOADED")
            elif status == "loading":
                if stat.st_mtime < time.time() - 60: # not updated within last minute -> assume failure
                    status_text = _("ERROR")
                else:
                    status_text = _("LOADING") 
            elif status == "done":
                status_text = _("DONE")
            elif status == "failed":
                status_text = _("FAILED")
            if status_text:
                upload = Upload()
                upload.xmlname = xmlname
                upload.status = status_text
                upload.done = (status_text == _("DONE"))
                upload.uploaded = (status_text == _("UPLOADED"))
                upload.loading = (status_text == _("LOADING"))
                upload.upload_time = meta["upload_time"]
                upload.upload_time_s = time.strftime("%Y-%m-%d %H.%M.%S",time.localtime(upload.upload_time))
                uploads.append(upload)
    return sorted(uploads,key=lambda x: x.upload_time)


def removefile(fname): 
    try:
        os.remove(fname)
    except FileNotFoundError:
        pass



def delete_files(username, xmlfile):
    upload_folder = get_upload_folder(username)
    removefile(os.path.join(upload_folder,xmlfile))
    removefile(os.path.join(upload_folder,xmlfile+".meta"))
    removefile(os.path.join(upload_folder,xmlfile+".log"))


