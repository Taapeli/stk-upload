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
    Gramps xml file upload

Created on 15.8.2018

@author: jm
"""
# blacked 2021-07-25 JMä
import os
import time
import logging
import traceback
from types import SimpleNamespace
from urllib.parse import unquote_plus
from time import sleep

logger = logging.getLogger("stkserver")

from flask import (
    render_template,
    session,
    request,
    redirect,
    url_for,
    send_from_directory,
    flash,
    jsonify,
)

# from flask import session as user_session
from flask_security import login_required, roles_accepted, current_user
from flask_babelex import _

import shareds
from bl.base import Status
from bl.batch.root import Root, BatchReader #, State, BatchUpdater
from bl.batch.root_updater import RootUpdater
from models import syslog, util #, loadfile

from ui.batch_ops import RESEARCHER_FUNCTIONS, RESEARCHER_OPERATIONS
from ui.context import UserContext
from ui.util import error_print, stk_logger
from ..admin import uploads

from . import bp
from bl.gramps import gramps_loader
from bl.gramps import gramps_utils
from bl.stats import get_stats

# @bp.route("/gramps")
# def obsolete_gramps_index():

# @bp.route("/gramps/show_log/<xmlfile>")
# @bp.route("/gramps/show_log/")
# def obsolete_show_upload_log(xmlfile=""):


@bp.route("/gramps/uploads")
@login_required
@roles_accepted("research", "admin")
def list_uploads():
    """ User uploads list.
        Steps 1.& 3. of audit path: The user can  select one to Audit queue
        Step 2. /audit/requested/<batch_id>
    """
    u_context = UserContext()
    active_batch=u_context.material.batch_id

    upload_list = uploads.list_uploads(current_user.username)
    logger.info(f"-> bp.gramps.routes.list_uploads n={len(upload_list)}")
    gramps_runner = shareds.app.config.get("GRAMPS_RUNNER")
    gramps_verify = gramps_runner and os.path.exists(gramps_runner)

    if shareds.app.config.get("USE_I_AM_ALIVE", True):
        inter = shareds.PROGRESS_UPDATE_RATE * 1000
    else:
        # For debugging: don't poll progress bar very often
        inter = shareds.PROGRESS_UPDATE_RATE * 10000

    # for upl in upload_list:
    #     print(f"#bp.gramps.routes.list_uploads: {upl}")
    return render_template(
        "/gramps/uploads.html",
        interval=inter,
        uploads=upload_list,
        active_batch=active_batch,
        gramps_verify=gramps_verify,
    )


@bp.route("/gramps/upload", methods=["POST"])
@login_required
@roles_accepted("research", "admin")
def upload_gramps():
    """Load a gramps xml file to temp directory for processing in the server
    """
    try:
        infile = request.files["filenm"]
        file_type = request.form["material"]    # = 'xml_file' !

        # Create Root node in managed transaction
        with RootUpdater("update") as bl_service:
            root = bl_service.create_batch(current_user.username, infile)

        # Create upload log file
        msg = f"{util.format_timestamp()}: User {current_user.name} "\
              f"({current_user.username}) uploaded the file {root.file!r} "\
              f"for id={root.id}"
        open(root.logname, "w", encoding="utf-8").write(msg)
        syslog.log(type="gramps file uploaded", file=infile.filename, batch=root.id)
        logger.info(
            f'-> bp.gramps.routes.upload_gramps/{file_type} f="{infile.filename}"'
            f" e={shareds.tdiff:.3f}sek"
        )
        # Start storing the XML file objects as database nodes in background
        uploads.initiate_background_load_to_stkbase(root)
        flash(
            _("The batch %(id)s upload has started in background. ", id=root.id) +
            _("You can follow the process below, but you can also leave or do something else. ") +
            _("Come back later to see the results.")
        )

    except Exception as e:
        traceback.print_exc()
        flash( _("Failed to create a new batch - ") + str(e) )

    # Return to the uploads page
    return redirect(url_for("gramps.list_uploads"))


# @bp.route("/gramps/start_upload/<xmlname>")
# def start_load_to_stkbase(xmlname):


@bp.route("/gramps/virhe_lataus/<int:code>/<text>")
@login_required
@roles_accepted("research", "admin") 
def error_page(code, text=""):
    """ Virhesivu näytetään """
    logger.info(f"bp.gramps.routes.error_page/{code}")
    return render_template("virhe_lataus.html", code=code, text=text)


@bp.route("/gramps/xml_analyze/<xmlfile>")
@login_required
@roles_accepted("research", "admin")
def xml_analyze(xmlfile):
    references = gramps_loader.analyze(current_user.username, xmlfile)
    logger.info(f'bp.gramps.routes.xml_analyze f="{os.path.basename(xmlfile)}"')
    return render_template(
        "/gramps/analyze_xml.html", references=references, file=xmlfile
    )


@bp.route("/gramps/gramps_analyze/<batch_id>")
@login_required
@roles_accepted("research", "admin", "audit")
def gramps_analyze(batch_id):
    batch = Root.get_batch(current_user.username, batch_id)
    logger.info(f'bp.gramps.routes.gramps_analyze b="{batch_id}"')
    base, ext = os.path.splitext(batch.xmlname)
    newfile = base + "_checked" + ext
    
    return render_template("/gramps/gramps_analyze.html",
                           batch_id=batch_id,
                           file=batch.xmlname,
                           newfile=newfile)


@bp.route("/gramps/gramps_analyze_json/<batch_id>/<newfile>")
@login_required
@roles_accepted("research", "admin", "audit")
def gramps_analyze_json(batch_id, newfile):
    batch = Root.get_batch(current_user.username, batch_id)
    gramps_runner = shareds.app.config.get("GRAMPS_RUNNER")
    print("gramps_runner",gramps_runner)
    if gramps_runner:
        lang = session.get("lang","")
        print("lang",lang)
        msgs = gramps_utils.gramps_verify(gramps_runner, lang, current_user.username, batch_id, batch.xmlname, newfile)
    else:
        msgs = {}
    logger.info(f'bp.gramps.routes.gramps_analyze_json f="{os.path.basename(batch.xmlname)}"')
    return jsonify(msgs)


@bp.route("/gramps/xml_delete/<xmlfile>")
@login_required
@roles_accepted("research", "admin")
def xml_delete(xmlfile):
    uploads.delete_files(current_user.username, xmlfile)
    logger.info(f'-> bp.gramps.routes.xml_delete f="{os.path.basename(xmlfile)}"')
    syslog.log(type="gramps file deleted", file=xmlfile)
    return redirect(url_for("gramps.list_uploads"))


# @bp.route("/gramps/xml_download/<xmlfile>")
# @login_required
# @roles_accepted("research", "admin")
# def xml_download(xmlfile):
#     xml_folder = uploads.get_upload_folder(current_user.username)
#     xml_folder = os.path.abspath(xml_folder)
#     return send_from_directory(
#         directory=xml_folder,
#         filename=xmlfile,
#         mimetype="application/gzip",
#         as_attachment=True,
#     )

@bp.route("/gramps/batch_download/<batch_id>")
@login_required
@roles_accepted("research", "admin")
def gramps_batch_download(batch_id):
    batch = Root.get_batch(current_user.username, batch_id)
    if batch:
        xml_folder, xname = os.path.split(batch.file)
        if batch.xmlname:
            xname = batch.xmlname
        xml_folder = os.path.abspath(xml_folder)
        try:
            return send_from_directory(xml_folder, xname,
                mimetype="application/gzip",
                as_attachment=True,
            )
        except Exception as e:
            print(f"bp.gramps.routes.gramps_batch_download: {e}")
            msg = _("The file \"%(n)s\" does not exist", n=xname)
            flash(msg)
            return redirect(url_for("gramps.list_uploads"))
            
@bp.route("/gramps/download_checked_file/<batch_id>")
@login_required
@roles_accepted("research", "admin")
def download_checked_file(batch_id):
    batch = Root.get_batch(current_user.username, batch_id)
    if batch:
        xml_folder, xname = os.path.split(batch.file)
        if batch.xmlname:
            xname = batch.xmlname
        base,ext = os.path.splitext(xname)
        xname = base + "_checked" + ext
        xml_folder = os.path.abspath(xml_folder)
        try:
            return send_from_directory(xml_folder, xname,
                mimetype="application/gzip",
                as_attachment=True,
                cache_timeout=0,  # change to max_age in Flask 2.x
            )
        except Exception as e:
            traceback.print_exc()
            print(f"bp.gramps.routes.gramps_batch_download: {e}")
            msg = _("The file \"%(n)s\" does not exist", n=xname)
            flash(msg)
            return redirect(url_for("gramps.list_uploads"))

@bp.route("/gramps/show_upload_log/<batch_id>")
@login_required
@roles_accepted("research")
def show_upload_log_from_batch_id(batch_id):
    msg=""
    try:
        batch = Root.get_batch(current_user.username, batch_id)
        if batch.file and not batch.logname:
            # Old style v2021.1 Root without logname info
            batch.logname = batch.file + ".log"        
        msg = open(batch.logname, encoding="utf-8").read()
        logger.info(f"-> bp.gramps.routes.show_upload_log_from_batch_id f='{batch.logname}'")
    except Exception as e:
        print(f"bp.gramps.routes.show_upload_log_from_batch_id: {e}")
        if not msg:
            msg = _("The log file for \"%(n)s\" does not exist any more", n=batch_id)
        flash(msg)
        return redirect(url_for("gramps.list_uploads"))

    return render_template("/admin/load_result.html", msg=msg)


@bp.route("/gramps/batch_delete/<batch_id>")
@login_required
@roles_accepted("research", "admin")
def batch_delete(batch_id):
    def xremove(path): 
        if os.path.exists(path):
            os.remove(path)

    def remove_old_style_files(path):  
        xremove(path)
        xremove(path.replace("_clean.", ".") )
        xremove(path.replace(".gramps", "_clean.gramps") )
        xremove(path.replace(".gpkg", "_clean.gpkg"))  
        xremove(path + ".meta")  
        xremove(path + ".log")  
        
    referrer = request.headers.get("Referer")

    batch = Root.get_batch(current_user.username, batch_id)
    if not batch:
        flash(_("Batch not found"), "error")
        return redirect(referrer)

    fname_parts = batch.file.split("/")  # uploads/<user>/<batch_id>/<file>
    if len(fname_parts) == 4 and fname_parts[2] == batch_id: # "new style" naming
        upload_dir = os.path.split(batch.file)[0]
        import shutil
        print("shutil.rmtree", upload_dir)
        try:
            shutil.rmtree(upload_dir)
        except FileNotFoundError:
            pass
    else:
        remove_old_style_files(batch.file) 
            
    ret = Root.delete_batch(current_user.username, batch_id)
    if Status.has_failed(ret):
        flash(_("Could not delete Batch id %(batch_id)s", batch_id=batch_id), "error")
        logger.warning(f'bp.gramps.routes.batch_delete ERROR {ret.get("statustext")}')
        syslog.log(type="batch_id delete FAILED", batch_id=batch_id)
    else:
        n = ret.get("total")
        logger.info(f"-> bp.gramps.routes.batch_delete f={batch_id}, n={n}")
        syslog.log(type="batch_id deleted", batch_id=batch_id)
        flash(
            _(
                "Batch %(batch_id)s has been deleted, %(n)s nodes",
                batch_id=batch_id,
                n=n,
            ),
            "info",
        )
    #return redirect(referrer)
    return redirect(url_for("gramps.list_uploads"))


@bp.route("/gramps/get_progress/<batch_id>")
@login_required
@roles_accepted("research", "admin")
def get_progress(batch_id):
    """ Calculate upload process status.
    """
    with BatchReader("update") as batch_service:
        res = batch_service.batch_get_one(current_user.username, batch_id)
        if Status.has_failed(res):
            print(f"bp.gramps.routes.get_progress: error {res.get('statustext')}")
            rsp = {
                "status": 'Failed',
                "progress": 0,
                "batch_id": batch_id,
            }
            return jsonify(rsp)
 
        batch = res['item']
        if not batch.metaname:
            print(f"bp.gramps.routes.get_progress: no metaname")
            rsp = {
                "status": 'Failed',
                "progress": 0,
                "batch_id": batch_id,
            }
            return jsonify(rsp)
        meta = uploads.get_meta(batch)
    
        status = meta.get("status")
        if status is None:
            return jsonify({"status": "error"})
    
        counts = meta.get("counts")
        if counts is None:
            print(f"bp.gramps.routes.get_progress: no counts")
            sleep(3)
            return jsonify({"status": status, "progress": 0})
    
        progress = meta.get("progress")
        if progress is None:
            print(f"bp.gramps.routes.get_progress: no progress")
            sleep(3)
            return jsonify({"status": status, "progress": 0})
    
        # Some object types are weighted because of long execution time
        total = 0
        total += counts["citation_cnt"]
        total += counts["event_cnt"]
        total += counts["family_cnt"] * 2
        total += counts["note_cnt"]
        total += counts["person_cnt"] * 3 # '2' should include refnames update
        total += counts["place_cnt"] * 2
        total += counts["object_cnt"]
        total += counts["source_cnt"]
        total += counts["repository_cnt"]
        done = 0
        done += progress.get("Citation", 0)
        done += progress.get("EventBl", 0)
        done += progress.get("FamilyBl", 0) * 2
        done += progress.get("Note", 0)
        done += progress.get("PersonBl", 0) * 3
        done += progress.get("PlaceBl", 0) * 2
        done += progress.get("MediaBl", 0)
        done += progress.get("Source_gramps", 0)
        done += progress.get("Repository", 0)
        done += progress.get("refnames", 0)
        # Why total may be 0? The default is set to 50% progress!
        rsp = {
            "status": status,
            "progress": 99 * done // total if total else 50,
            "batch_id": batch_id,
        }
        print(f"# bp.gramps.routes.get_progress: {done}/{total}, {rsp}")
        return jsonify(rsp)

@bp.route("/gramps/commands/<batch_id>")
@login_required
@roles_accepted("research")
def get_commands(batch_id):
    """ Available commands for details page.
    
        If has argument '?caller=scene', don't show browse command
    """
    caller = request.args.get('caller', 'uploads')

    with BatchReader("update") as batch_service:
        res = batch_service.batch_get_one(current_user.username, batch_id)
        if Status.has_failed(res):
            return _("Failed to retrieve commands")
 
        batch = res['item']

        commands = []
        # Boolean vector of allowed researcher operations for this State 
        ops = RESEARCHER_OPERATIONS.get(batch.state)
        if ops:
            for i in range(len(RESEARCHER_FUNCTIONS)):
                #print("#bp.gramps.routes.get_commands:",caller,batch.state,ops[i],RESEARCHER_FUNCTIONS[i])
                if ops[i]:
                    # If allowed function, add (url, title) tuple to commands
                    cmd, title = RESEARCHER_FUNCTIONS[i]
                    # The batch_id is appended to given command
                    confirm = False
                    if cmd.startswith("/gramps/batch_delete/"):
                        confirm = True
                    if not (caller == "scene" and cmd.startswith("/scene/material/batch")):
                        # Add parameters
                        cmd = unquote_plus(cmd.format(state=batch.state, batch_id=batch.id))
                        commands.append( (cmd, _(title), confirm) )

        return render_template("/gramps/commands.html", 
                               batch_id=batch_id, 
                               description=batch.description, 
                               commands=commands)

@bp.route("/gramps/details/<batch_id>")
@login_required
@roles_accepted("research", "admin")
def batch_details(batch_id):
    """ Show details page by batch_id. """
    t0 = time.time()
    user_context = UserContext()
    from bl.stats import create_stats_data

    res = create_stats_data(batch_id, current_user)
    # { "batch", "objects", "events" }
    elapsed = time.time() - t0
    stk_logger(user_context, 
               f"-> bp.gramps.routes.batch_details e={elapsed:.3f}")
    return render_template(
       "/gramps/details.html",
       batch=res["batch"],
       user_context=user_context,
       object_stats=res["objects"],
       event_stats=res["events"],
       elapsed=elapsed,
    )

@bp.route("/gramps/details/update_description", methods=["post"])
@login_required
@roles_accepted("research", "admin")
def batch_update_description():
    """ Update description field in detail page. """
    batch_id = request.form["batch_id"]
    description = request.form["description"]
    msg = ""
    with RootUpdater("update") as service:
        ret = service.batch_update_descr(batch_id, description, current_user.username)
        if Status.has_failed(ret):
            msg = (_("Update did not succeed: " + ret["errortext"]))
        else:
            msg = (_("Updated"))

    return msg

# =================== experimental scripting tool ======================

@bp.route("/scripting/<batch_id>", methods=["get"])
@bp.route("/scripting", methods=["post"])
@login_required
@roles_accepted("audit")
def scripting(batch_id=None):
    #from pprint import pprint
    enabled = shareds.app.config.get("SCRIPTING_TOOL_ENABLED")
    if enabled is not True:
        raise RuntimeError(_("Scripting tool is not enabled"))
    if request.method == "POST":
        batch_id = request.form.get("batch_id")
    with BatchReader("update") as root_service:
        res = root_service.batch_get_one(current_user.username, batch_id)
        if Status.has_failed(res):
            raise RuntimeError(_("Failed to retrieve batch"))
 
        batch = res['item']
    if request.method == "POST":
        #pprint(request.form)
        from bl.scripting.scripting_tool import Executor
        executor = Executor(batch_id)
        return executor.execute(SimpleNamespace(**request.form))
    else:
        return render_template(
            "/gramps/scripting.html",
           batch=batch,
    )

@bp.route("/scripting_attrs", methods=["post"])
@login_required
@roles_accepted("audit")
def scripting_attrs(batch_id=None):
    from bl.scripting.scripting_tool import get_attrs
    attrs = get_attrs(request.form.get("scope"))
    return ",".join(attrs)
