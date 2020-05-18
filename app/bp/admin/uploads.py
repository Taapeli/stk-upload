'''
Created on 8.8.2018

@author: jm

 Administrator operations page urls
 
'''
import os
import pprint
import time
import threading
#from pathlib import Path
import traceback

import logging 
logger = logging.getLogger('stkserver')

from flask_babelex import _

from models import email, util, syslog 
from ..gramps import gramps_loader
import shareds
from models.gen.cypher import Cypher_batch

STATUS_UPLOADED     = "uploaded"
STATUS_LOADING      = "loading"
STATUS_DONE         = "done"
STATUS_FAILED       = "failed"
STATUS_ERROR        = "error"
STATUS_REMOVED      = "removed"

#===============================================================================
# Background loading of a Gramps XML file
# 
# 1. The user uploads an XML file using the user interface. This is handled by the function "upload_gramps". 
#    The file is stored in the user specific folder uploads/<username>. A log file with the name <xml-file>.log
#    is created automatically (where <xml-file> is the name of the uploaded file.
# 
# 2. The upload_gramps function redirects to "list_uploads" which shows the XML files uploaded by this user. 
#
# 3. The admin user can see all users' uploads by going to the user list screen and clicking the link 'uploads' or via the
#    link "show all uploads"
#
# 4. The admin user sees a list of the uploaded files for a user but he also sees more information and is able to initiate
#    loading of the file into the Neo4j database. This will call the function "initiate_background_load_to_neo4j"
# 
# 5. The function "initiate_background_load_to_neo4j" starts a background thread to do the actual database load. 
#    The thread executes the function "background_load_to_neo4j" which calls the actual logic in
#    "gramps_loader.xml_to_neo4j"
#    
#    The folder "uploads/<userid>" also contains a "metadata" file "<xml-file>.meta" for status information. 
#    This file contains a text form of a dictionary with keys "status" and "upload_time".
#
#    The status is initially set to "uploaded" while the file has been uploaded by the user. 
#    When the load to the database is ongoing the status is "loading". After successful database load 
#    the status is set to "done" (these values are mapped to different words in the user interface).
#
#    If an exception occurs during the database load then the status is set to "failed".
#    
# 6. It is conceivable that the thread doing the load is somehow stopped without being able to rename the file
#    to indicate a completion or failure. Then the status remains "loading" indefinitely. 
#    This situation is noticed by the "i_am_alive" thread whose only purpose is to update the timestamp of
#    ("touch") the log file as long as the loading thread is running. This update will happen every 10 seconds.
#
#    This enables the user interface to notice that the load has failed. The status will be set to "error"
#    if the log file is not updated (touched) for a minute.
#
# 7. If the load completes successfully then the status is set to "done". The result of the load is 
#    returned by the "xml_to_neo4j" function as a list of Log records. 
#    This list is stored in text format in the log file.
#    The user interface is then able to retrieve the Log records and display them to the user (in function
#    upload_info).
#
# 8. The "uploads" function displays a list of the load operations performed by the user. This function 
#    will display the state of the file. The list is automatically updated every 30 seconds.
# 
#    The user is redirected to this screen immediately after initiating a load operation. The user can also 
#    go to the screen from the main display.
#===============================================================================
   

def get_upload_folder(username): 
    ''' Returns upload directory for given user'''
    return os.path.join("uploads", username)

def set_meta(username,filename,**kwargs):
    ''' Stores status information in .meta file '''
    upload_folder = get_upload_folder(username) 
    name = "{}.meta".format(filename)
    metaname = os.path.join(upload_folder,name)
    update_metafile(metaname,**kwargs)

def update_metafile(metaname,**kwargs):
    try:
        meta = eval(open(metaname).read())
    except FileNotFoundError:
        meta = {}
    meta.update(kwargs)
    open(metaname,"w").write(pprint.pformat(meta))

def get_meta(metaname):
    ''' Reads status information from .meta file '''
    try:
        meta = eval(open(metaname).read())
        status= meta.get("status")
        if status == STATUS_LOADING:
            stat = os.stat(metaname)
            if stat.st_mtime < time.time() - 60: # not updated within last minute -> assume failure
                meta["status"] = STATUS_ERROR
    except FileNotFoundError:
        meta = {}
    return meta

def i_am_alive(metaname,parent_thread):
    ''' Checks, if backgroud thread is still alive '''
    while os.path.exists(metaname) and parent_thread.is_alive():
        print(parent_thread.progress)
        update_metafile(metaname,
                        progress=parent_thread.progress)
        time.sleep(10)

def background_load_to_neo4j(username,filename):
    ''' Imports gramps xml data to database '''
    upload_folder = get_upload_folder(username) 
    pathname = os.path.join(upload_folder,filename)
    metaname = pathname+".meta"
    logname =  pathname+".log"
    update_metafile(metaname, progress={})
    steps = []
    try:
        os.makedirs(upload_folder, exist_ok=True)
        set_meta(username,filename,status=STATUS_LOADING)
        this_thread = threading.current_thread()
        this_thread.progress = {}
        counts = gramps_loader.analyze_xml(username, filename)
        update_metafile(metaname,counts=counts,progress={})
        threading.Thread(target=lambda: i_am_alive(metaname,this_thread),name="i_am_alive for " + filename).start()
        steps,batch_id = gramps_loader.xml_to_neo4j(pathname,username)
        for step in steps:
            print(step)
        if not batch_id:
            raise RuntimeError("Run Failed, missing batch_id")

        if os.path.exists(metaname): 
            set_meta(username,filename,
                     batch_id=batch_id,
                     status=STATUS_DONE)
        msg = "{}:\nStored the file {} from user {} to neo4j".format(util.format_timestamp(),pathname,username)
        msg += "\nBatch id: {}".format(batch_id)
        msg += "\nLog file: {}".format(logname)
        msg += "\n"
        for step in steps:
            msg += "\n{}".format(step)
        msg += "\n"
        open(logname,"w", encoding='utf-8').write(msg)
        email.email_admin(
                    "Stk: Gramps XML file stored",
                    msg )
        syslog.log(type="storing to database complete",file=filename,user=username)
    except:
        traceback.print_exc()
        res = traceback.format_exc()
        set_meta(username,filename,status=STATUS_FAILED)
        msg = "{}:\nStoring the file {} from user {} to database FAILED".format(util.format_timestamp(),pathname,username)
        msg += "\nLog file: {}".format(logname)
        msg += "\n" + res
        for step in steps:
            msg += "\n{}".format(step)
        msg += "\n"
        open(logname,"w", encoding='utf-8').write(msg)
        email.email_admin(
                    "Stk: Gramps XML file storing FAILED",
                    msg )
        syslog.log(type="gramps store to database failed",file=filename,user=username)


def initiate_background_load_to_neo4j(userid,filename):
    ''' Starts gramps xml data import to database '''
    #===========================================================================
    # subprocess.Popen("PYTHONPATH=app python runload.py " 
    #                  + pathname + " " 
    #                  + username + " "
    #                  + logname,
    #                   shell=True)
    #===========================================================================
    def background_load_to_neo4j_thread(app):
        with app.app_context():
            background_load_to_neo4j(userid,filename)
        
    threading.Thread(target=background_load_to_neo4j_thread,
                     args=(shareds.app,),
                     name="neo4j load for " + filename).start()
    syslog.log(type="storing to database initiated",file=filename,user=userid)
    return False

#Removed / 3.2.2020/JMä
# def batch_count(username,batch_id):
# def batch_person_count(username,batch_id):

def list_uploads(username):
    ''' Gets a list of uploaded files and their process status.
    
        Also db Batches without upload file are included in the list.
    '''
    # 1. List Batches, their status and Person count
    batches = {}
    result = shareds.driver.session().run(Cypher_batch.get_user_batch_names, 
                                          user=username)
    for record in result:
        # <Record batch='2019-08-12.001' timestamp=None persons=1949>
        batch = record['batch']
        batches[batch] = (record['status'], record['persons'])

    # 2. List uploaded files
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
            xmlname = name.rsplit(".",maxsplit=1)[0]
            meta = get_meta(fname)
            status = meta["status"]
            batch_id = ""
            status_text = None

            if status == STATUS_UPLOADED:
                status_text = _("UPLOADED")
            elif status == STATUS_LOADING:
                status_text = _("STORING") 
            elif status == STATUS_DONE:
                status_text = _("STORED")
                if 'batch_id' in meta:
                    batch_id = meta['batch_id']
            elif status == STATUS_FAILED:
                status_text = _("FAILED")
            elif status == STATUS_ERROR:
                status_text = _("ERROR")
            elif status == STATUS_REMOVED:
                status_text = _("REMOVED")

            if not batch_id in batches:
                if status_text == _("STORED"):
                    status_text = _("REMOVED")
                batch_id = ""
                person_count = 0
            else:
                status, person_count = batches.pop(batch_id)

            if status_text:
                upload = Upload()
                upload.xmlname = xmlname
                upload.status = status_text
                upload.batch_id = batch_id
                upload.count = person_count
                upload.done = (status_text == _("STORED"))
                upload.uploaded = (status_text == _("UPLOADED"))
                upload.loading = (status_text == _("STORING"))
                upload.upload_time = meta["upload_time"]
                upload.upload_time_s = util.format_timestamp(upload.upload_time)
                upload.user = username
                uploads.append(upload)
    
    # 3. Add batches where there is no file
    for batch, item in batches.items():
        upload = Upload()
        upload.batch_id = batch
        status, count = item
        if status == "started":
            upload.status = "?"
        elif status == "completed":
            upload.status = _("STORED")
        upload.count = count
        upload.upload_time = 0.0
        uploads.append(upload)
        
    return sorted(uploads,key=lambda x: x.upload_time)

def list_uploads_all(users):
    for user in users:
        for upload in list_uploads(user.username):
            yield upload 


# def list_empty_batches(username=None):
#     ''' Gets a list of db Batches without any linked data.
# --> models.gen.batch_audit.Batch.list_empty_batches


def removefile(fname): 
    ''' Removing a file '''
    try:
        os.remove(fname)
    except FileNotFoundError:
        pass


def delete_files(username, xmlfile):
    ''' Removing uploaded file with associated .meta and .log '''
    upload_folder = get_upload_folder(username)
    removefile(os.path.join(upload_folder,xmlfile))
    removefile(os.path.join(upload_folder,xmlfile+".meta"))
    removefile(os.path.join(upload_folder,xmlfile+".log"))
    i = xmlfile.rfind(".")
    if i >= 0:
        file_cleaned = xmlfile[:i] + "_clean" + xmlfile[i:]
        removefile(os.path.join(upload_folder,file_cleaned))
        
