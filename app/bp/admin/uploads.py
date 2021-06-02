#   Isotammi Genealogical Service for combining multiple researchers' results.
#   Created in co-operation with the Genealogical Society of Finland.
#
#   Copyright (C) 2016-2021  Juha Mäkeläinen, Jorma Haapasalo, Kari Kujansuu, 
#                            Timo Nallikari, Pekka Valta
#
#   This program is free software: you can redistribute it and/or modify
#   it under the terms of the GNU General Public License as published by
#   the Free Software Foundation, either version 2 of the License, or
#   (at your option) any later version.
#
#   This program is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU General Public License for more details.
#
#   You should have received a copy of the GNU General Public License
#   along with this program.  If not, see <http://www.gnu.org/licenses/>.

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

import shareds
from bl.base import Status, IsotammiException
from models import email, util, syslog 
from bl.gramps import gramps_loader
from pe.neo4j.cypher.cy_batch_audit import CypherBatch

#==> bl.batch.Batch.BATCH_* 7.5.2021 / JMä
# STATUS_UPLOADED = "uploaded", STATUS_LOADING = "loading", STATUS_DONE = "done"
# STATUS_FAILED = "failed", STATUS_ERROR = "error", STATUS_REMOVED = "removed"


#===============================================================================
# Background loading of a Gramps XML file
# 
# 1. The user uploads an XML file using the user interface. This is handled by
#    the function "upload_gramps". The file is stored in the user specific folder
#    uploads/<username>. A log file with the name <xml-file>.log is created
#    automatically (where <xml-file> is the name of the uploaded file.
# 
# 2. The upload_gramps function redirects to "list_uploads" which shows the XML
#    files uploaded by this user. 
#
# 3. The admin user can see all users' uploads by going to the user list screen
#    and clicking the link 'uploads' or via the link "show all uploads".
#
# 4. The admin user sees a list of the uploaded files for a user but he also sees
#    more information and is able to initiate loading of the file into the Neo4j
#    database called "stkbase". This will call the function 
#    "initiate_background_load_to_stkbase".
# 
# 5. The function "initiate_background_load_to_stkbase" starts a background
#    thread to do the actual database load. The thread executes the function 
#    "background_load_to_stkbase" which calls the actual logic in
#    "gramps_loader.xml_to_stkbase".
#    
#    The folder "uploads/<userid>" also contains a "metadata" file
#    "<xml-file>.meta" for status information. This file contains a text form
#    of a dictionary with keys "status" and "upload_time".
#
#    The status is initially set to "uploaded" while the file has been uploaded
#    by the user. When the load to the database is ongoing the status is
#    "loading". After successful database load the status is set to "done"
#    (these values are mapped to different words in the user interface).
#
#    If an exception occurs during the database load then the status is set to 
#    "failed".
#    
# 6. It is conceivable that the thread doing the load is somehow stopped
#    without being able to rename the file to indicate a completion or failure. 
#    Then the status remains "loading" indefinitely. This situation is noticed
#    by the "i_am_alive" thread whose only purpose is to update the timestamp of
#    ("touch") the log file as long as the loading thread is running. This
#    update will happen every 10 seconds.
#
#    This enables the user interface to notice that the load has failed. The
#    status will be set to "error" if the log file is not updated (touched)
#    for a minute.
#
# 7. If the load completes successfully then the status is set to "done". The
#    result of the load is returned by the "xml_to_stkbase" function as a
#    list of Log records. This list is stored in text format in the log file.
#    The user interface is then able to retrieve the Log records and display
#    them to the user (in function upload_info).
#
# 8. The "uploads" function displays a list of the load operations performed by
#    the user. This function will display the state of the file. The list is
#    automatically updated every 30 seconds.
#
#    Note. For easier Gramps upload testing you may set 'USE_I_AM_ALIVE = False'
#          in instance/config.py, which reduces console output.
# 
#    The user is redirected to this screen immediately after initiating a load
#    operation. The user can also go to the screen from the main display.
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
    from bl.batch import Batch # For status codes

    try:
        meta = eval(open(metaname).read())
        status= meta.get("status")
        if status == Batch.BATCH_LOADING:
            stat = os.stat(metaname)
            if stat.st_mtime < time.time() - 60: # not updated within last minute -> assume failure
                meta["status"] = Batch.BATCH_ERROR
    except Exception as e:
        print(f'bp.admin.uploads.get_meta: error {e.__class__.__name__} {e}')
        meta = {}
    return meta

def i_am_alive(metaname,parent_thread):
    ''' Checks, if backgroud thread is still alive '''
    while os.path.exists(metaname) and parent_thread.is_alive():
        print(parent_thread.progress)
        update_metafile(metaname,
                        progress=parent_thread.progress)
        time.sleep(shareds.PROGRESS_UPDATE_RATE)

def background_load_to_stkbase(username,filename):
    ''' Imports gramps xml data to database '''
    from bl.batch import Batch # For status codes
    
    upload_folder = get_upload_folder(username) 
    pathname = os.path.join(upload_folder,filename)
    metaname = pathname+".meta"
    logname =  pathname+".log"
    update_metafile(metaname, progress={})
    steps = []
    try:
        os.makedirs(upload_folder, exist_ok=True)
        set_meta(username,filename, status=Batch.BATCH_LOADING)
        this_thread = threading.current_thread()
        this_thread.progress = {}
        counts = gramps_loader.analyze_xml(username, filename)
        update_metafile(metaname,counts=counts,progress={})
        # Start background process monitoring
        if shareds.app.config.get("USE_I_AM_ALIVE", True):
            threading.Thread(target=lambda: i_am_alive(metaname, this_thread),
                             name="i_am_alive for " + filename).start()

        # Read the Gramps xml file, and save the information to db
        res = gramps_loader.xml_to_stkbase(pathname,username)

        steps = res.get('steps',[])
        batch_id = res.get('batch_id',"-")

        for step in steps:
            print(f"    {step}")
        if not batch_id:
            return {'status': Status.ERROR,
                    'statustext': "Run Failed: no batch created."}

        if os.path.exists(metaname): 
            set_meta(username,filename, batch_id=batch_id, status=Batch.BATCH_CANDIDATE) #prev. BATCH_DONE)
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
        syslog.log(type="completed save to database", file=filename, user=username)
    except Exception as e:
        #traceback.print_exc()
        print(f'bp.admin.uploads.background_load_to_stkbase: {e.__class__.__name__} {e}')
        res = traceback.format_exc()
        print(res)
        set_meta(username,filename,status=Batch.BATCH_FAILED)
        msg = f"{util.format_timestamp()}:\nStoring the file {pathname} from user {username} to database FAILED"
        msg += f"\nLog file: {logname}\n" + res
        for step in steps:
            msg += f"\n{step}"
        msg += "\n"
        if isinstance(e, IsotammiException):
            pprint.pprint(e.kwargs)
            msg += pprint.pformat(e.kwargs)
        open(logname,"w", encoding='utf-8').write(msg)
        email.email_admin(
                    "Stk: Gramps XML file storing FAILED",
                    msg )
        syslog.log(type="gramps store to database failed",file=filename,user=username)


def initiate_background_load_to_stkbase(userid,filename):
    ''' Starts gramps xml data import to database.
    '''
    #===========================================================================
    # subprocess.Popen("PYTHONPATH=app python runload.py " 
    #                  + pathname + " " 
    #                  + username + " "
    #                  + logname,
    #                   shell=True)
    #===========================================================================
    def background_load_to_stkbase_thread(app):
        with app.app_context():
            background_load_to_stkbase(userid,filename)
        
    threading.Thread(target=background_load_to_stkbase_thread,
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
    from bl.batch import Batch # For status codes

    # 1. List Batches, their status and Person count
    batches = {}
    result = shareds.driver.session().run(CypherBatch.get_user_batch_summary, 
                                          user=username)
    for record in result:
        # Returns batch, person_count, audit_count
        batch_node = record['b']
        b = Batch.from_node(batch_node)
        # augment with additional data
        b.person_count = record['person_count']
        b.audit_count = record['audit_count']
        batches[b.id] = b

    # 2. List uploaded files
    upload_folder = get_upload_folder(username)
    try:
        names = os.listdir(upload_folder)
    except:
        names = []
    uploads = []
    logfile_base = ""
    class Upload: pass
    # There may be 4 files: 
    # - 'test.gramps',      original xml
    # - 'test.gramps.log'   logfile from conversion to db
    # - 'test.gramps.meta'  metafile from file conversion
    # - 'test_clean.gramps' cleaned xml data
    for name in names:
        name_parts = name.split(".")
        if name.endswith(".log"):
            (logfile_base, _x) = name.rsplit(".",1)
        if name.endswith(".meta"):
            #TODO: Tähän tarvitaan try catch, koska kaatuneen gramps-latauksen jälkeen
            #      metatiedosto voi olla rikki tai puuttua
            fname = os.path.join(upload_folder,name)
            xmlname = name.rsplit(".",maxsplit=1)[0]
            meta = get_meta(fname)
            status = meta.get("status",Batch.BATCH_UPLOADED)
            status_text = None
            person_count = 0
            audit_count = 0
            batch_id = meta.get('batch_id',"")
            in_batches = batch_id in batches
            if not in_batches:
                batch_id = ""
                if status == Batch.BATCH_DONE:
                    status = Batch.BATCH_REMOVED
            # print(f"### Batch {batch_id} {status} {name} base={logfile_base}")

            if status == Batch.BATCH_UPLOADED:
                status_text = _("UPLOADED")
            elif status == Batch.BATCH_LOADING:
                status_text = _("STORING") 
            elif status == Batch.BATCH_CANDIDATE or status == Batch.BATCH_DONE:
                status_text = _("CANDIDATE")
                # The meta file does not contain later status values
                if in_batches:
                    #status, person_count, audit_count = batches.pop(batch_id)
                    b = batches.pop(batch_id)
                    status = b.status
                    person_count = b.person_count
                    audit_count = b.audit_count
                    if status == Batch.BATCH_FOR_AUDIT:
                        status_text = _("FOR_AUDIT")
                else:
                    status = Batch.BATCH_REMOVED
            elif status == Batch.BATCH_FAILED:
                status_text = _("FAILED")
            elif status == Batch.BATCH_ERROR:
                status_text = _("ERROR")
            elif status == Batch.BATCH_REMOVED:
                status_text = _("REMOVED")

            if status_text:
                upload = Upload()
                upload.xmlname = xmlname
                upload.status = status_text
                upload.batch_id = batch_id
                upload.count = person_count
                upload.count_a = audit_count
                upload.done = (status_text == _("CANDIDATE") or \
                               status_text == _("FOR_AUDIT"))
                upload.uploaded = (status_text == _("UPLOADED"))
                upload.loading = (status_text == _("STORING"))
                clean_name =  os.path.join(upload_folder, name_parts[0] + "_clean." + name_parts[1])
                upload.has_file = os.path.isfile(clean_name)
                upload.has_log = name.startswith(logfile_base)
                upload.upload_time = meta["upload_time"]
                upload.upload_time_s = util.format_timestamp(upload.upload_time)
                upload.user = username
                upload.material_type = b.material_type if in_batches else meta.get("material_type","") 
                upload.description = b.description if in_batches else meta.get("description","") 
                uploads.append(upload)
    
    # 3. Add batches where there is no meta file
    for batch, b in batches.items():
        upload = Upload()
        upload.batch_id = batch
        if b.status == Batch.BATCH_STARTED:
            upload.status = "?"
        elif b.status == Batch.BATCH_CANDIDATE: # "completed"
            #Todo: Remove later: Old FOR_AUDIT materials are CANDIDATE, too
            upload.status = _("CANDIDATE") + " ?"
        elif audit_count > 0:
            upload.status = f"{ _('FOR_AUDIT') } {audit_count} { _('persons') }"
        upload.count = b.person_count
        upload.count_a = b.audit_count
        upload.has_file = False
        upload.has_log = audit_count > 0 # Rough estimate!
        upload.upload_time = 0.0
        upload.material_type = b.material_type
        upload.description = b.description
        print(f"### Batch {batch} {status} -")
        uploads.append(upload)
    
    return sorted(uploads,key=lambda x: x.upload_time)

def list_uploads_all(users):
    for user in users:
        for upload in list_uploads(user.username):
            yield upload 


# def list_empty_batches(username=None):
#     ''' Gets a list of db Batches without any linked data.
# --> bl.batch.Batch.list_empty_batches


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
        
