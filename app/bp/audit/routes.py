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
Created on 28.11.2019

 Auditor operations page urls
 
"""
# blacked 2021-07-25 JMä
import csv
import json
import time
import logging
from io import StringIO, BytesIO
import os.path

from flask import render_template, request, redirect, url_for, flash
from flask import send_file, send_from_directory
from flask import session
from flask_security import login_required, roles_accepted, current_user
from flask_babelex import _
import urllib.parse

from . import bp

import shareds
from bl.base import Status
from bl.batch.root import Root, State #, BatchUpdater
from bl.batch.root_updater import RootUpdater
from bl.person import Person, PersonWriter
from bl.refname import Refname
#from bl.material import Material
from bp.admin.csv_refnames import load_refnames
from bp.admin import uploads
from models import syslog, loadfile
from ui.context import UserContext
from ui.util import error_print

logger = logging.getLogger("stkserver")

def _get_server_location():
    # Returns server address as a str
    dbloc = shareds.driver.address
    return ":".join((dbloc[0], str(dbloc[1])))


@bp.route("/audit")
@login_required
@roles_accepted("audit")
def audit_home():
    return render_template("/audit/index.html")


# --------------------- Move User Batch to Approved data ----------------------------
# Steps:
#    1.  User: /gramps/uploads                                      (gramps/uploads.html)
#    2.  User: "Send for auditing" -> /audit/requested/<batch_id>   ()
#        - "request"   Candidate -> Audit request
#    2.1 User: "Withdraw from audition queue" -> TODO
#        - "revert"    Candidate <- Audit request
#
#    3. Auditor:                           /audit/list_uploads
#    4. Auditor: "Pick audit operation" -> /audit/pick/<batch_id>   (pick_auditing.html)
#    5. Auditor: "Start auditing"       -> /audit/selected "start",batch_id  -> list_uploads
#       - "start"     Audit request -> Auditing
#    6. Auditor: "Accept auditing"      -> /audit/selected "accept",batch_id -> list_uploads
#       - "accept"    Auditing -> Accepted
#    7. Auditor: "Reject auditing"      -> /audit/selected "reject",batch_id -> list_uploads
#       - "reject"    Auditing -> Rejected
# ------------------------------------------------------------------------------

@bp.route("/audit/user/<oper>/<batch_id>", methods=["GET"])
@login_required
@roles_accepted("research")
def audit_research_op(oper=None, batch_id=None):
    """ Select Researcher operation for Batch by oper.
        - "request": User moves Batch to Audit queue by setting state="Audit requested" or
        - "withdraw": User withdraws audit request.
    """
    try:
        user_id = current_user.username
        operation = oper
        if not batch_id:
            batch_id = session.get('batch_id')
        if not oper:
            operation = session.get('oper')
            #request.form["oper"]
    
        if operation == "request":
            new_state = State.ROOT_AUDIT_REQUESTED
            msg = _("Audit request for ") + batch_id
        elif operation == "withdraw":
            new_state = State.ROOT_CANDIDATE
            msg = _("Withdrawing audit request for ") + batch_id
        else:
            return redirect(url_for("gramps.list_uploads", batch_id=batch_id))

        with RootUpdater("update") as batch_service:
            res = batch_service.change_state(batch_id, user_id, new_state)

    except Exception as e:
        error_print("audit_research_op", e)
        return redirect(url_for("gramps.list_uploads"))

    if not res or Status.has_failed(res):
        flash(_(msg) + _(" failed"), "error")
    else:
        flash(_(msg) + _(" succeeded"))

    print(f"bp.audit.routes.audit_research_op/{operation}: {res.get('status')} for node {res.get('identity')}")
    syslog.log(type=f"Audit {operation}", batch=batch_id, by=user_id, msg=msg)
    return redirect(url_for("gramps.list_uploads", batch_id=batch_id))


@bp.route("/audit/list_uploads", methods=["GET"])
@bp.route("/audit/list_uploads/<batch_id>", methods=["GET"])
@login_required
@roles_accepted("audit")
def list_uploads(batch_id=None):
    """ 3. List Batches.

        In the list of Gramps batches the row of batch_id is highlighted.
    """
    t0 = time.time()
    try:
        users = shareds.user_datastore.get_users()
        root_list = list(uploads.list_uploads_all(users))
        logger.info(f"-> bp.audit.routes.list_uploads n={len(root_list)}")

    except Exception as e:
        error_print("list_uploads", e)
        return redirect(url_for("audit.audit_home"))

    return render_template("/audit/batches.html",
                           uploads=root_list, batch_id=batch_id, elapsed=time.time() - t0)


@bp.route("/audit/pick/<batch_id>", methods=["GET"])
@login_required
@roles_accepted("audit")
def audit_pick(batch_id=None):
    """ 4. Pick Batch for auditor operations.
    """
    try:
        username, root, labels = Root.get_batch_stats(batch_id)
        
        if not root:
            flash(_("No such batch ") + str(batch_id), "error")
            return redirect(url_for("audit.list_uploads", batch_id=batch_id))
    
        total = 0
        for _label, cnt in labels:
            total += cnt
        timestamp = root.timestamp_str()
        auditor_names = [a[0] for a in root.auditors]
        i_am_auditor = (current_user.username in auditor_names)
        
        can_browse = root.state_transition("browse")
        can_start = root.state_transition("start", i_am_auditor)
        can_accept = root.state_transition("accept")
        can_browse = root.state_transition("browse")
        can_browse = root.state_transition("browse")
        can_hold = root.state_transition("hold")
        can_reject = root.state_transition("reject")
        print(f"#bp.audit.routes.audit_pick: i_am_auditor={i_am_auditor} "
              f"can_browse={can_browse} can_start={can_start} "
              f"can_accept={can_accept} can_reject={can_reject}")
    except Exception as e:
        error_print("audit_pick", e)
        return redirect(url_for("audit.list_uploads"))

    print(f"bp.audit.routes.audit_pick: {root}, auditors={auditor_names}, user={current_user.username}")
    return render_template("/audit/pick_auditing.html",
        user=username, 
        root=root,
        basename=os.path.basename(root.file),
        can_browse=can_browse,
        can_start=can_start,
        can_accept=can_accept,
        #can_remove=can_reject,
        can_reject=can_hold,
        label_nodes=labels,
        total=total,
        time=timestamp,
        auditor_name=current_user.name,
    )


@bp.route("/audit/selected", methods=["POST"])
@login_required
@roles_accepted("audit")
def audit_selected_op():
    """ Select Auditor operation for Batch.
    Auditor operations:
        5. - "start"     Audit request -> Auditing
        6. - "accept"    Auditing -> Accepted
        7. - "reject"    Auditing -> Rejected
        x. - "cancel"
    """
    try:
        u_context = UserContext()
        _breed, state, material_type, batch_id = u_context.material.get_current()
        owner_id = u_context.material.request_args.get("user")
        auditor = current_user.username
        operation = "cancel"

        if request.form.get("browse"):
            args = {"batch_id": batch_id, "material_type": material_type, "state": state}
            return redirect("/scene/material/batch?" + urllib.parse.urlencode(args))
        elif request.form.get("download"):
            return redirect(url_for("audit.audit_batch_download", 
                                    batch_id=batch_id, 
                                    username=current_user.username))
            #return redirect(f"/audit/batch_download/{batch_id}/{current_user.username}")
        elif request.form.get("start"):
            operation = "start"
        elif request.form.get("accept"):
            operation = "accept"
        elif request.form.get("reject"):
            operation = "reject"
        logger.info(f"--> bp.audit.routes.audit_selected u={owner_id} b={batch_id} {operation}")
    
        with RootUpdater("update") as batch_service:
    
            if operation == "start":
                # 5. Move from "Audit Requested" to "Auditing" state to "Accepted"
                res = batch_service.select_auditor(batch_id, auditor)
                msg = _("You are now an auditor for batch ") + batch_id
    
            elif operation == "accept":
                # 6. Move from "Auditing" to "Accepted" state
                res = batch_service.change_state(batch_id, 
                                                 owner_id, 
                                                 State.ROOT_ACCEPTED)
                msg = _("Audit batch accepted: ") + batch_id
    
            elif operation == "reject":
                # 7. Move from "Auditing" to "Rejected" state, if no other auditors exist
                res = batch_service.remove_auditor(batch_id, owner_id)
                res = batch_service.change_state(batch_id, 
                                                 owner_id, 
                                                 State.ROOT_REJECTED)
                msg = _("You have rejected the batch ") + batch_id
    
            else:
                return redirect(url_for("audit.list_uploads", batch_id=batch_id))
    
        if Status.has_failed(res):
            msg = f"Audit request {operation} failed"
            flash(_(msg), "error")
        else:
            flash(_(msg))

    except Exception as e:
        error_print("audit_selected_op", e)
        return redirect(url_for("audit.list_uploads"))

    syslog.log(type="Audit state change", 
               batch=batch_id, by=owner_id, msg=msg, op=operation)
    return redirect(url_for("audit.list_uploads", batch_id=batch_id))


@bp.route("/audit/batch_download/<batch_id>/<username>")
@login_required
@roles_accepted("audit")
def audit_batch_download(batch_id, username):
    batch = Root.get_batch(username, batch_id)
    if batch:
        xml_folder, xname = os.path.split(batch.file)
        if batch.xmlname:
            xname = batch.xmlname
        abs_folder = os.path.abspath(xml_folder)

        logger.info(f"--> bp.audit.routes.audit_batch_download u={username} b={batch_id} {xname}")
        syslog.log(type="Auditor xml download", 
                   batch=batch_id, by=username, file=xname)

        return send_from_directory(abs_folder, xname,
            mimetype="application/gzip",
            as_attachment=True,
        )
    else:
        msg = _("Not allowed to load this batch: ")+batch_id+"/"+username
        flash(msg)
        return msg


# --------------------- Delete an approved data batch ----------------------------


@bp.route("/audit/batch_delete/<batch_id>", methods=["POST"])
@login_required
@roles_accepted("audit")
def delete_approved(batch_id):
    """ Confirm approved batch delete
    """
    (msg, _nodes_deleted) = Root.delete_audit(current_user.username, batch_id)
    if msg != "":
        logger.error(msg)
        flash(msg)
    else:
        logger.info(f'-> bp.audit.routes.batch_delete f="{batch_id}"')
        syslog.log(type="approved batch_id deleted", batch_id=batch_id)

    referrer = request.headers.get("Referer")
    return redirect(referrer)


# --------------------- List Approved data batches ----------------------------


@bp.route("/audit/approvals/<who>", methods=["GET", "POST"])
@login_required
@roles_accepted("audit")
def audit_approvals(who=None):
    """ List Audit batches """
    t0 = time.time()
    if who == "all":
        auditor = None
    else:
        auditor = current_user.username
    titles, batches = Root.get_auditor_stats(auditor)
    # {'matti/2020-01-03.001/13.01.2020 20:30': {'Note': 17, 'Place': 30, 'Repository': 3},
    #  'teppo/2020-01-03.002/23.01.2020 15:52': {...} ...}
    total = 0
    for key in batches.keys():
        # print(key + ":")
        for _lbl, cnt in batches[key].items():
            # print (f'    {_lbl} = {cnt}')
            total += cnt
    logger.info(
        f" bp.audit.routes.audit_approvals {auditor} {len(batches)} batches, total {total} nodes"
    )

    return render_template(
        "/audit/approvals.html",
        user=auditor,
        total=total,
        titles=titles,
        batches=batches,
        elapsed=time.time() - t0,
    )

# --------------------- Show user profile ----------------------------

@shareds.app.route("/audit/profile/<user>", methods=["GET"])
@login_required
@roles_accepted("audit")
def user_profile(user):
    """Show user profile.
       - From original method: my_settings()
    """
    t0 = time.time()
    labels, user_batches = Root.get_user_stats(user)
    userprofile = shareds.user_datastore.get_userprofile(user, roles=True)

    logger.info(f"-> bp.audit.routes.user_profile {user}")
    return render_template(
        "/audit/user_profile.html",
        referrer=request.referrer,
        apikey=None,    #api.get_apikey(current_user),
        labels=labels,
        batches=user_batches,
        gedcoms=[],
        userprofile=userprofile,
        elapsed=time.time() - t0,
    )


# --------------------- List classifiers and refnames ----------------------------


@bp.route("/audit/classifiers", methods=["GET"])
@login_required
def list_classifiers():
    # List classifier values and translations
    import ui.jinja_filters

    # Translation is not possible, the original search kay is not known
    # sv = gettext.translation('messages', 'app/translations', languages=['sv'])
    # en = gettext.translation('messages', 'app/translations', languages=['en'])

    key_dicts = ui.jinja_filters.list_translations()
    data = {}
    n = 0
    rows_lt = {}
    for key, values in key_dicts.items():
        # key: 'nt'
        # values: ('Name types', {'Aatelointinimi': 'aateloitu nimi',  ...})
        rows = []
        desc = values[0]
        todo = True
        for term, value in values[1].items():
            if key == "lt_in":
                # Put 'lt_in' value to last column of 'lt' row
                for row in rows_lt:
                    if row[0] == term:
                        row[2] = value
                        todo = False
                        break
                if todo:
                    rows_lt.append([term, " ", value])
            else:
                row = [term, value, ""]
                rows.append(row)
        n += len(values[1])
        data[key] = (desc, rows)
        if key == "lt":
            rows_lt = rows
    # >>> data['marr']
    # ('marriage types', [['Married', 'Avioliitossa', ''], ['Unknown', ...]])

    logger.info(f"-> bp.audit.routes.list_classifiers n={n}")
    return render_template("/audit/classifiers.html", data=data)


# Refnames home page
@bp.route("/audit/refnames")
@login_required
@roles_accepted("audit")
def refnames():
    """ Operations for reference names """
    return render_template("/audit/reference.html")


@bp.route("/audit/set/refnames")
@login_required
@roles_accepted("member", "admin", "audit")
def set_all_person_refnames():
    """ Setting reference names for all persons """
    # dburi = _get_server_location()
    with PersonWriter("update") as service:
        ret = service.set_person_name_properties(ops=["refname"]) or _("Done")
        # return {'refnames', 'sortnames', 'status'}
        if Status.has_failed(ret):
            flash(ret.statustext, "error")
            logger.error(
                f"-> bp.audit.routes.set_all_person_refnames error {ret.get('statustext')}"
            )
        else:
            refname_count = ret.get("refnames", -1)
            sortname_count = ret.get("sortnames", -1)
            msg = f"Updated {sortname_count} person sortnames, {refname_count} refnames"
            flash(msg, "info")
            logger.info(f"-> bp.audit.routes.set_all_person_refnames n={refname_count}")
    return render_template("/audit/refnames")


@bp.route("/audit/download/refnames")
@login_required
@roles_accepted("audit")
def download_refnames():
    """Download reference names as a CSV file"""
    logger.info(f"-> bp.audit.routes.download_refnames")  # n={refname_count}")
    with StringIO() as f:
        writer = csv.writer(f)
        hdrs = "Name,Refname,Reftype,Gender,Source,Note".split(",")
        writer.writerow(hdrs)
        # refnames = datareader.read_refnames()
        refnames = Refname.get_refnames()
        for refname in refnames:
            row = [
                refname.name,
                refname.refname,
                refname.reftype,
                Person.convert_sex_to_str(refname.sex),
                refname.source,
            ]
            writer.writerow(row)
        csvdata = f.getvalue()
        f2 = BytesIO(csvdata.encode("utf-8"))
        f2.seek(0)
        return send_file(
            f2,
            mimetype="text/csv",
            as_attachment=True,
            attachment_filename="refnames.csv",
        )


@bp.route("/audit/upload_csv", methods=["POST"])
@login_required
@roles_accepted("audit")
def upload_csv():
    """ Load a csv file to temp directory for processing in the server
    """
    try:
        infile = request.files["filenm"]
        material_type = request.form["material"]
        logging.info(f"-> bp.audit.routes.upload_csv/{material_type} f='{infile.filename}'")

        loadfile.upload_file(infile)
        if "destroy" in request.form and request.form["destroy"] == "all":
            logger.info("-> bp.audit.routes.upload_csv/delete_all_Refnames")
            # datareader.recreate_refnames()
            Refname.recreate_refnames()

    except Exception as e:
        return redirect(url_for("virhesivu", code=1, text=str(e)))

    return redirect(
        url_for("audit.save_loaded_csv", filename=infile.filename, subj=material_type)
    )


@bp.route("/audit/save/<string:subj>/<string:filename>")
@login_required
@roles_accepted("audit")
def save_loaded_csv(filename, subj):
    """ Save loaded csv data to the database """
    pathname = loadfile.fullname(filename)
    dburi = _get_server_location()
    logging.info(f"-> bp.audit.routes.save_loaded_csv/{subj} f='{filename}'")
    try:
        if subj == "refnames":  # Stores Refname objects
            status = load_refnames(pathname)
        else:
            return redirect(
                url_for(
                    "virhesivu",
                    code=1,
                    text=_("Data type '{}' is not supported").format(subj),
                )
            )
    except KeyError as e:
        return render_template(
            "virhe_lataus.html",
            code=1,
            text=_("Missing proper column title: ") + str(e),
        )
    return render_template("/talletettu.html", text=status, uri=dburi)



#===============================================================================================================
#
# White lists for types
#
#===============================================================================================================
WHITELIST_DIR = "instance/whitelists"

@bp.route("/audit/manage_whitelists", methods=["GET"])
@login_required
@roles_accepted("audit")
def manage_whitelists():
    return render_template("/audit/whitelists.html")

@bp.route("/audit/get_whitelist/<scope>", methods=["GET"])
@login_required
@roles_accepted("audit")
def get_whitelist(scope):
    try:
        return open(f"{WHITELIST_DIR}/{scope}").read().strip()
    except:
        return ""

@bp.route("/audit/get_whitelist_scopes", methods=["GET"])
@login_required
@roles_accepted("audit")
def get_whitelist_scopes():
    try:
        return {"scopes":sorted(os.listdir(WHITELIST_DIR))}
    except:
        return []

@bp.route("/audit/set_whitelist", methods=["POST"])
@login_required
@roles_accepted("audit")
def set_white_list():
    data = json.loads(request.data)
    scope = data.get("scope")
    with open(f"{WHITELIST_DIR}/{scope}","w") as f:
        print(data.get("whitelist",""), file=f)
    return "ok"

