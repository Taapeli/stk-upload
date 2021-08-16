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

logger = logging.getLogger("stkserver")

from flask import (
    render_template,
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
from bl.root import State, Root
from models import loadfile, email, util, syslog

# from ui.user_context import UserContext
from ..admin import uploads

from . import bp
from bl.gramps import gramps_loader
from bl.gramps import gramps_utils


@bp.route("/gramps")
@login_required
@roles_accepted("research", "admin")
def gramps_index():
    return "Error: bp.gramps.routes.gramps_index is obsolete!"
    """ Home page gramps input file processing """
    logger.info("-> bp.start.routes.gramps_index")
    return render_template("/gramps/obsolete_index_gramps.html")


@bp.route("/gramps/show_log/<xmlfile>")
@login_required
@roles_accepted("research")
def show_upload_log(xmlfile):
    upload_folder = uploads.get_upload_folder(current_user.username)
    fname = os.path.join(upload_folder, xmlfile + ".log")
    msg = open(fname, encoding="utf-8").read()
    logger.info(f"-> bp.gramps.routes.show_upload_log f='{xmlfile}'")
    return render_template("/admin/load_result.html", msg=msg)


@bp.route("/gramps/uploads")
@login_required
@roles_accepted("research", "admin")
def list_uploads():
    upload_list = uploads.list_uploads(current_user.username)
    logger.info(f"-> bp.gramps.routes.list_uploads n={len(upload_list)}")
    gramps_runner = shareds.app.config.get("GRAMPS_RUNNER")
    gramps_verify = gramps_runner and os.path.exists(gramps_runner)

    if shareds.app.config.get("USE_I_AM_ALIVE", True):
        inter = shareds.PROGRESS_UPDATE_RATE * 1000
    else:
        # For debugging: don't poll progress bar very often
        inter = shareds.PROGRESS_UPDATE_RATE * 10000

    for upl in upload_list:
        print(f"#upload: {upl}")

    return render_template(
        "/gramps/uploads.html",
        interval=inter,
        uploads=upload_list,
        gramps_verify=gramps_verify,
    )


@bp.route("/gramps/upload", methods=["POST"])
@login_required
@roles_accepted("research", "admin")
def upload_gramps():
    """Load a gramps xml file to temp directory for processing in the server"""

    try:
        infile = request.files["filenm"]
        material = request.form["material"]
        # logger.debug("Got a {} file '{}'".format(material, infile.filename))

        t0 = time.time()
        upload_folder = uploads.get_upload_folder(current_user.username)
        os.makedirs(upload_folder, exist_ok=True)

        pathname = loadfile.upload_file(infile, upload_folder)
        isotammi_metadata = gramps_loader.get_isotammi_metadata(
            current_user.username, infile.filename
        )
        if isotammi_metadata:
            material_type = isotammi_metadata[0]
            description = isotammi_metadata[1]
        else:
            material_type = ""
            description = ""

        shareds.tdiff = time.time() - t0

        logname = pathname + ".log"
        uploads.set_meta(
            current_user.username,
            infile.filename,
            status=State.FILE_UPLOADED,
            upload_time=time.time(),
            material_type=material_type,
            description=description,
        )
        msg = f"{util.format_timestamp()}: User {current_user.name} ({current_user.username}) uploaded the file {pathname}"
        open(logname, "w", encoding="utf-8").write(msg)
        email.email_admin("Stk: Gramps XML file uploaded", msg)
        syslog.log(type="gramps file uploaded", file=infile.filename)
        logger.info(
            f'-> bp.gramps.routes.upload_gramps/{material} f="{infile.filename}"'
            f" e={shareds.tdiff:.3f}sek"
        )
    except Exception as e:
        traceback.print_exc()
        return redirect(url_for("gramps.error_page", code=1, text=str(e)))

    return redirect(url_for("gramps.list_uploads"))
    # return redirect(url_for('gramps.save_loaded_gramps', filename=infile.filename))


@bp.route("/gramps/start_upload/<xmlname>")
@login_required
@roles_accepted("research")
def start_load_to_stkbase(xmlname):
    """The uploaded Gramps xml file is imported to database in background process.
    A 'i_am_alive' process for monitoring the bg process is also started.
    """
    uploads.initiate_background_load_to_stkbase(current_user.username, xmlname)
    logger.info(
        f'-> bp.gramps.routes.start_load_to_stkbase f="{os.path.basename(xmlname)}"'
    )
    flash(_("Data import from %(i)s to database has been started.", i=xmlname), "info")
    return redirect(url_for("gramps.list_uploads"))


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


@bp.route("/gramps/gramps_analyze/<xmlfile>")
@login_required
@roles_accepted("research", "admin", "audit")
def gramps_analyze(xmlfile):
    logger.info(f'bp.gramps.routes.gramps_analyze f="{os.path.basename(xmlfile)}"')
    return render_template("/gramps/gramps_analyze.html", file=xmlfile)


@bp.route("/gramps/gramps_analyze_json/<xmlfile>")
@login_required
@roles_accepted("research", "admin", "audit")
def gramps_analyze_json(xmlfile):
    gramps_runner = shareds.app.config.get("GRAMPS_RUNNER")
    if gramps_runner:
        msgs = gramps_utils.gramps_verify(gramps_runner, current_user.username, xmlfile)
    else:
        msgs = {}
    logger.info(f'bp.gramps.routes.gramps_analyze_json f="{os.path.basename(xmlfile)}"')
    return jsonify(msgs)


@bp.route("/gramps/xml_delete/<xmlfile>")
@login_required
@roles_accepted("research", "admin")
def xml_delete(xmlfile):
    uploads.delete_files(current_user.username, xmlfile)
    logger.info(f'-> bp.gramps.routes.xml_delete f="{os.path.basename(xmlfile)}"')
    syslog.log(type="gramps file deleted", file=xmlfile)
    return redirect(url_for("gramps.list_uploads"))


@bp.route("/gramps/xml_download/<xmlfile>")
@login_required
@roles_accepted("research", "admin")
def xml_download(xmlfile):
    xml_folder = uploads.get_upload_folder(current_user.username)
    xml_folder = os.path.abspath(xml_folder)
    return send_from_directory(
        directory=xml_folder,
        filename=xmlfile,
        mimetype="application/gzip",
        as_attachment=True,
    )


#                                attachment_filename=xmlfile+".gz")


@bp.route("/gramps/batch_delete/<batch_id>")
@login_required
@roles_accepted("research", "admin")
def batch_delete(batch_id):
    filename = Root.get_filename(current_user.username, batch_id)
    if filename:
        # Remove file, if exists
        metafile = filename.replace("_clean.", ".") + ".meta"
        if os.path.exists(metafile):
            data = eval(open(metafile).read())
            if data.get("batch_id") == batch_id:
                del data["batch_id"]
                data["status"] = State.ROOT_REMOVED
                open(metafile, "w").write(repr(data))
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
    referrer = request.headers.get("Referer")
    return redirect(referrer)


@bp.route("/gramps/get_progress/<xmlfile>")
@login_required
@roles_accepted("research", "admin")
def get_progress(xmlfile):
    xml_folder = uploads.get_upload_folder(current_user.username)
    xml_folder = os.path.abspath(xml_folder)
    filename = os.path.join(xml_folder, xmlfile)
    metaname = filename.replace("_clean.", ".") + ".meta"
    meta = uploads.get_meta(metaname)

    status = meta.get("status")
    if status is None:
        return jsonify({"status": "error"})

    counts = meta.get("counts")
    if counts is None:
        return jsonify({"status": status, "progress": 0})

    progress = meta.get("progress")
    if progress is None:
        return jsonify({"status": status, "progress": 0})

    total = 0
    total += counts["citation_cnt"]
    total += counts["event_cnt"]
    total += counts["family_cnt"]
    total += counts["note_cnt"]
    total += 2 * counts["person_cnt"]  # include refnames update
    total += counts["place_cnt"]
    total += counts["object_cnt"]
    total += counts["source_cnt"]
    total += counts["repository_cnt"]
    done = 0
    done += progress.get("Citation", 0)
    done += progress.get("EventBl", 0)
    done += progress.get("FamilyBl", 0)
    done += progress.get("Note", 0)
    done += progress.get("PersonBl", 0)
    done += progress.get("PlaceBl", 0)
    done += progress.get("MediaBl", 0)
    done += progress.get("Source_gramps", 0)
    done += progress.get("Repository", 0)
    done += progress.get("refnames", 0)
    rsp = {
        "status": status,
        "progress": 99 * done // total,
        "batch_id": meta.get("batch_id"),
    }
    return jsonify(rsp)
