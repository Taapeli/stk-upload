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

"""
Created on 8.8.2018

@author: jm

 Administrator operations page urls
 
"""
# blacked 2021-07-25 JMä
import os
import pprint
import time
import threading
import traceback
import logging
from datetime import datetime
from dataclasses import dataclass
from typing import List

logger = logging.getLogger("stkserver")

from flask_babelex import _

import shareds
from bl.root import Root, State
from bl.base import IsotammiException
from models import email, util, syslog
from bl.gramps import gramps_loader
from pe.neo4j.cypher.cy_batch_audit import CypherRoot

# ==> bl.batch.Batch.BATCH_* 7.5.2021 / JMä
# STATUS_UPLOADED = "uploaded", STATUS_LOADING = "loading", STATUS_DONE = "done"
# STATUS_FAILED = "failed", STATUS_ERROR = "error", STATUS_REMOVED = "removed"


# ===============================================================================
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
# ===============================================================================


def get_upload_folder(username):
    """ Returns upload directory for given user"""
    return os.path.join("uploads", username)


def set_meta(username, batch_id, filename, **kwargs):
    """ Stores status information in .meta file """
    upload_folder = get_upload_folder(username)
    name = "{}.meta".format(filename)
    metaname = os.path.join(upload_folder, batch_id, name)
    update_metafile(metaname, **kwargs)


def update_metafile(metaname, **kwargs):
    try:
        meta = eval(open(metaname).read())
    except FileNotFoundError:
        meta = {}
    meta.update(kwargs)
    open(metaname, "w").write(pprint.pformat(meta))


def get_meta(root):
    """ Reads status information from .meta file """
    
    try:
        metaname = root.metaname
        meta = eval(open(metaname).read())
        status = meta.get("status")
        if status == State.FILE_LOADING:
            stat = os.stat(metaname)
            if (
                stat.st_mtime < time.time() - 60
            ):  # not updated within last minute -> assume failure
                meta["status"] = State.FILE_LOAD_FAILED
                with open(root.logname,"a") as f:
                    print("", file=f)
                    msg = "{}: {}".format(
                            util.format_timestamp(),
                            _("Load failed, no progress in 60 seconds")) 
                    print(msg, file=f)
                update_metafile(metaname, status=State.FILE_LOAD_FAILED)
    except FileNotFoundError as e:
        meta = {}
    except Exception as e:
        print(f"bp.admin.uploads.get_meta: error {e.__class__.__name__} {e}")
        meta = {}
    return meta


def i_am_alive(metaname, parent_thread):
    """ Checks if background thread is still alive """
    while os.path.exists(metaname) and parent_thread.is_alive():
        print(parent_thread.progress)
        update_metafile(metaname, progress=parent_thread.progress)
        time.sleep(shareds.PROGRESS_UPDATE_RATE)


def background_load_to_stkbase(batch:Root) -> None:
    """ Imports gramps xml data to database """

    update_metafile(batch.metaname, progress={})
    steps = []
    try:
        update_metafile(batch.metaname, status=State.FILE_LOADING)

        this_thread = threading.current_thread()
        this_thread.progress = {} # type: ignore

        counts = gramps_loader.analyze_xml(batch.user, batch.id, batch.xmlname)
        update_metafile(batch.metaname, counts=counts, progress={})

        # Start background process monitoring
        if shareds.app.config.get("USE_I_AM_ALIVE", True):
            threading.Thread(
                target=lambda: i_am_alive(batch.metaname, this_thread),
                name="i_am_alive for " + batch.xmlname,
            ).start()

        # Read the Gramps xml file, and save the information to db
        res = gramps_loader.xml_to_stkbase(batch)

        steps = res.get("steps", [])
        for step in steps:
            print(f"    {step}")

        if os.path.exists(batch.metaname):
            update_metafile(batch.metaname, status=State.ROOT_CANDIDATE)
        msg = "{}:\nStored the file {} from user {} to neo4j".format(
            util.format_timestamp(), batch.file, batch.user
        )
        msg += "\nBatch id: {}".format(batch.id)
        msg += "\nLog file: {}".format(batch.logname)
        msg += "\n"
        for step in steps:
            msg += "\n{}".format(step)
        msg += "\n"
        open(batch.logname, "w", encoding="utf-8").write(msg)
        email.email_admin("Stk: Gramps XML file stored", msg)
        syslog.log(type="completed save to database", file=batch.xmlname, user=batch.user)
    except Exception as e:
        # traceback.print_exc()
        print(
            f"bp.admin.uploads.background_load_to_stkbase: {e.__class__.__name__} {e}"
        )
        res = traceback.format_exc()
        print(res)
        update_metafile(batch.metaname, status=State.FILE_LOAD_FAILED)
        msg = f"{util.format_timestamp()}:\nStoring the file {batch.file} from user {batch.user} to database FAILED"
        msg += f"\nLog file: {batch.logname}\n" + res
        for step in steps:
            msg += f"\n{step}"
        msg += "\n"
        if isinstance(e, IsotammiException):
            pprint.pprint(e.kwargs)
            msg += pprint.pformat(e.kwargs)
        open(batch.logname, "w", encoding="utf-8").write(msg)
        email.email_admin("Stk: Gramps XML file storing FAILED", msg)
        syslog.log(type="gramps store to database failed", file=batch.xmlname, user=batch.user)


def initiate_background_load_to_stkbase(batch):
    """ Starts gramps xml data import to database.
    """
    # ===========================================================================
    # subprocess.Popen("PYTHONPATH=app python runload.py "
    #                  + pathname + " "
    #                  + username + " "
    #                  + logname,
    #                   shell=True)
    # ===========================================================================
    def background_load_to_stkbase_thread(app):
        with app.app_context():
            background_load_to_stkbase(batch)

    threading.Thread(
        target=background_load_to_stkbase_thread,
        args=(shareds.app,),
        name="neo4j load for " + batch.file,
    ).start()
    syslog.log(type="storing to database initiated", file=batch.file, user=batch.user)
    return False



@dataclass
class Upload:
    """Data entity for upload file/batch."""
    batch_id: str
    xmlname: str
    state: str
    status: str
    material_type: str
    description: str
    user: str
    u_name: str
    auditors: List[List]    # [[username, timestamp, format_timestamp]...]
    count: int
    is_candidate: int  # for Javascript: 0=false, 1=true
    for_auditor: int

    def __str__(self):
        s = f"batch={self.batch_id}" if self.batch_id else "NO BATCH "
        if self.user:
            s += f"@{self.user}"
        if self.count:
            s += f", counts {self.count}"
        if self.auditors:
            s += f", auditors: {[a[0] for a in self.auditors]}"
        return f"{self.material_type}/{self.state}, {s}" #, found {has_file}, {has_log}"

    def for_auditor(self):
        """ Is relevant for auditor? """
        if self.state in [
            State.ROOT_AUDIT_REQUESTED, 
            State.ROOT_AUDITING, 
            State.ROOT_ACCEPTED, 
            State.ROOT_REJECTED]:
            return True
        return False

def list_uploads(username:str) -> List[Upload]:
    """ Gets a list of uploaded batches
    """

    # 1. List Batches from db, their status and Person count
    result = shareds.driver.session().run(
        CypherRoot.get_user_roots_summary, user=username
    )

    uploads = []
    for record in result:
        # <Record 
        #    u_name='Juha P.'
        #    root=<Node id=34475 labels=frozenset({'Root'})
        #        properties={'material': 'Family Tree', 'state': 'Auditing', 
        #            'id': '2021-05-07.001', 'user': 'jpek', 
        #            'timestamp': 1620403991562, ...}> 
        #    person_count=64
        #    auditors=[["juha",1630474129763]]
        # >
        node = record["root"]
        b: Root = Root.from_node(node)
        u_name = record["u_name"]

        meta = get_meta(b)
        status = meta.get("status", State.FILE_UPLOADED)
        if status == State.FILE_LOAD_FAILED:
            state = State.FILE_LOAD_FAILED
        else:
            state = b.state
        audi_rec = record['auditors']
        auditors = []
        for au_user, ts in audi_rec:
            # ["juha",1630474129763]
            if au_user:
                ts_str = util.format_ms_timestamp(ts, "d")
                # ["juha",1630474129763,"1.9.2021"]
                auditors.append((au_user, ts, ts_str))

        upload = Upload(
            batch_id=b.id,
            xmlname=os.path.split(b.file)[1] if b.file else "",
            count=record["person_count"],
            user=b.user,
            u_name=u_name,
            auditors=auditors,
            state=state,
            status=_(state),
            is_candidate=1 if (b.state == State.ROOT_CANDIDATE) else 0,
            for_auditor=1 if b.for_auditor() else 0,
            material_type=b.material,
            description=b.description,
        )
        #print(f"#bp.admin.uploads.list_uploads: {upload}")
        uploads.append(upload)

    return sorted(uploads, key=lambda upload: upload.batch_id)

def list_uploads_all(users) -> List[Upload]:
    """ Get named setups.User objects. """
    uploads = []
    for user in users:
        for upload in list_uploads(user.username):
            uploads.append(upload)
    return sorted(uploads, key=lambda upload: upload.batch_id)

# def list_empty_batches(username=None):
#     ''' Gets a list of db Batches without any linked data.
# --> bl.batch.Batch.list_empty_batches


def removefile(fname):
    """ Removing a file """
    try:
        os.remove(fname)
    except FileNotFoundError:
        pass


def delete_files(username, xmlfile):
    """ Removing uploaded file with associated .meta and .log """
    upload_folder = get_upload_folder(username)
    removefile(os.path.join(upload_folder, xmlfile))
    removefile(os.path.join(upload_folder, xmlfile + ".meta"))
    removefile(os.path.join(upload_folder, xmlfile + ".log"))
    i = xmlfile.rfind(".")
    if i >= 0:
        file_cleaned = xmlfile[:i] + "_clean" + xmlfile[i:]
        removefile(os.path.join(upload_folder, file_cleaned))
