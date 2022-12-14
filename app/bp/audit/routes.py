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
from bl.base import Status, IsotammiException
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
from ui.util import stk_logger

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


# ------------------- Change User Batch to Approved data ----------------------
# Researcher steps:
#    1.  /gramps/uploads
#    2.  "Send for auditing" -> /audit/requested/<batch_id>
#        - "request"   Candidate -> Audit request
#    2.1  "revert"    Candidate <- Audit request
#
# Auditor steps:
#    3.                           /audit/list_uploads
#    4. "Pick audit operation" -> /audit/pick/<batch_id>   (pick_auditing.html)
#    5. "Start auditing"       -> /audit/selected "start",batch_id  -> list_uploads
#       - "start"   Audit request -> Auditing
#    5.1 "Withdraw from audition" -> Audit requested
#    6. "Accept auditing"      -> /audit/selected "accept",batch_id -> list_uploads
#       - "accept"    Auditing -> Accepted
#    7. "Reject auditing"      -> /audit/selected "reject",batch_id -> list_uploads
#       - "reject"    Auditing -> Rejected
# -----------------------------------------------------------------------------

@bp.route("/audit/user/<oper>/<batch_id>", methods=["GET"])
@login_required
@roles_accepted("research")
def audit_researcher_ops(oper=None, batch_id=None):
    """ Select Researcher operation for Batch by oper.
        - "request": User moves Batch to Audit queue by setting state="Audit requested" or
        - "withdraw": User withdraws audit request.
    """
    try:
        user_id = current_user.username
        # Optional return page like "/scene/details/"
        ret_page = request.args.get('ret', '')
        operation = oper
        if not batch_id:
            batch_id = session.get('batch_id')
        if not oper:
            operation = session.get('oper')
            #request.form["oper"]
    
        with RootUpdater("update") as service: 
            if operation == "request":
                # Candidate -> Audit requested
                msg = _("Audit request for ") + batch_id
                res = service.change_state(batch_id, user_id, State.ROOT_AUDIT_REQUESTED)
            elif operation == "withdraw":
                # Auditing -> Audit requested 'luovu, keskeytä'
                msg = _("Withdrawing audit request for ") + batch_id
                res = service.change_state(batch_id, user_id, State.ROOT_CANDIDATE)
            else:
                if ret_page:
                    return redirect(ret_page)
                else:
                    return redirect(url_for("gramps.list_uploads", batch_id=batch_id))

    except Exception as e:
        error_print("audit_researcher_ops", e)
        if ret_page:
            return redirect(ret_page)
        else:
            return redirect(url_for("gramps.list_uploads"))

    if not res or Status.has_failed(res):
        flash(_(msg) + _(" failed"), "error")
    else:
        flash(_(msg) + _(" succeeded"))

    print(f"bp.audit.routes.audit_researcher_ops/{operation}: {res.get('status')} for node {res.get('identity')}")
    syslog.log(type=f"Audit {operation}", batch=batch_id, by=user_id, msg=msg)
    if ret_page:
        return redirect(ret_page)
    else:
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
        #user_audit = current_user.username
        username, root, labels = Root.get_batch_stats(batch_id)
        # labels = [(' Person', 9), ('Citation', 39), ...]
        if not root:
            flash(_("No such batch ") + str(batch_id), "error")
            return redirect(url_for("audit.list_uploads", batch_id=batch_id))

        total = 0
        for _label, cnt in labels:
            total += cnt
        auditor_names = [a[0] for a in root.auditors]
        i_am_auditor = (current_user.username in auditor_names)
        prev_names = [a[0] for a in root.prev_audits]
        i_was_auditor = (current_user.username in prev_names)
        print(f"#bp.audit.routes.audit_pick: {root}, "
              f"auditors={','.join(auditor_names)}/{','.join(prev_names)}, "
              f"user={current_user.username}")
        auditing_by_other = len(auditor_names) > 0 and not i_am_auditor
        can_browse = root.state_transition("browse", i_am_auditor or i_was_auditor)
        can_download = root.state_transition("download", i_am_auditor or i_was_auditor)
        can_start = root.state_transition("start", i_am_auditor)
        can_accept = root.state_transition("accept", i_am_auditor)
        can_delete = root.state_transition("delete", i_am_auditor)
        print(f"#bp.audit.routes.audit_pick: i_am/was auditor={i_am_auditor}/{i_was_auditor} "
              f"can browse={can_browse} download={can_download} start={can_start} "
              f"accept/withdraw/reject={can_accept} delete={can_delete}")
    except Exception as e:
        error_print("audit_pick", e)
        return redirect(url_for("audit.list_uploads"))

    return render_template("/audit/pick_auditing.html",
        user=username, 
        root=root,
        basename=os.path.basename(root.file),
        i_am_auditor=i_am_auditor,
        auditing_by_other=auditing_by_other,
        can_browse=can_browse,
        can_download=can_download,
        can_start=can_start,
        can_accept=can_accept, # & withdraw and reject
        label_nodes=labels,
        total=total,
        auditor_name=current_user.name,
    )


@bp.route("/audit/selected", methods=["POST"])
@login_required
@roles_accepted("audit")
def auditor_ops():
    """ Select Auditor operation for Batch.
    Auditor operations:
        0a "browse"    - no State change (5)
        0b "download"  - no State change (5)
        0c "upload_log"  no State change
        5. "start"     Audit request -> Auditing (1,2,3)
        6. "accept"    Auditing -> Accepted (4)
        7. "reject"    Auditing -> Rejected (4)
        8. "withdraw"  Auditing -> Audit requested (4) 'luovu, keskeytä'
        9. "delete"    Rejected -> (does not exist)
        x. "cancel"
   [a.(1) Remove my HAS_ACCESS, if exists, Todo?]
    b.(2) For all auditors: change DOES_AUDIT --> DID_AUDIT, ts_to=now
    c.(3) Add my DOES_AUDIT
    ..(4) Change my DOES_AUDIT -> DID_AUDIT, ts_to=now
    ..(5) Add my HAS_ACCESS, if I don't have HAS_ACCESS and no *_AUDIT exists
    """
    #prev.1 If the user has no DOES_AUDIT permission, create HAS_ACCESS permission
    #prev.2 If the user has HAS_ACCESS permission, replace it with DOES_AUDIT    

    def find_request_op():
        """ Pick the required operation from request. """
        for op in ["browse", "download", "upload_log", "start",
                   "accept", "reject", "withdraw"]:
            if request.form.get(op):
                return op
        return "cancel"

    def allow_batch_access(batch_id, user_audit):
        """ If given auditor has no access permission,
            create a HAS_ACCESS permission. """
        with RootUpdater("update") as service: 
            res = service.set_access(batch_id, user_audit)
            status = res["status"]
            if status == Status.UPDATED:
                msg = _("You have given access permission for batch ") + batch_id
                syslog.log(type="Material access given", batch=batch_id, op="allow_access", msg=msg)
            elif status == Status.OK:
                msg = _("Batch %(bid)s access is OK", bid=batch_id)
            print(f"#bp.audit.routes.allow_batch_access: {msg}")
        return status, msg

    here="bp.audit.routes.auditor_ops"
    msg = ""
    try:
        u_context = UserContext()
        _breed, state, material_type, batch_id = u_context.material.get_current()
        user_owner = u_context.material.request_args.get("user")
        user_audit = current_user.username
        operation = find_request_op()
        print(f"#auditor_ops: {user_audit} {operation} {batch_id}")
        if operation in ["browse", "download"]:
            status, msg = allow_batch_access(batch_id, user_audit)
            if status == Status.UPDATED:
                flash(msg)
                stk_logger(u_context, f"--> {here}/allow b={batch_id}")
                syslog.log(type=f"Access granted", batch=batch_id, msg=msg)

            if operation == "browse":
                # 0a. Go to scene views
                args = {"batch_id": batch_id, "material_type": material_type, "state": state}
                return redirect("/scene/material/batch?" + urllib.parse.urlencode(args))
            else:   # operation == "download":
                # 0b. Download Gramps file
                return redirect(url_for("audit.audit_batch_download", 
                                        batch_id=batch_id, 
                                        username=current_user.username))
        if operation == "upload_log":
            # 0c No State change
            return redirect(url_for("gramps.show_upload_log_from_batch_id", 
                                    batch_id=batch_id))

        with RootUpdater("update") as service:
            logger.info(f"--> {here} u={user_owner} b={batch_id} {operation}")

            if operation == "start":
                # 5. "start"     Audit request -> Auditing (1,2,3)
                #
                # B - ds_batch_end_audition(self, batch_id, auditor_user):
                #     Changes each DOES_AUDIT link with DID_AUDIT
                #     1. Create DID_AUDIT link with new end time
                #     2. Remove DOES_AUDIT link
                res1 = service.end_auditions(batch_id, user_audit)
                if res1.get("status") == Status.UPDATED:
                    msg = res1.get("msg")
                    flash(msg)
                    print(f"--> {here}(B): {msg}")
                    syslog.log(type=f"Auditors removed", batch=batch_id, msg=msg)
                # C - ds_batch_set_auditor(self, batch_id, auditor_user, old_states):
                #     3. Updates Root.state
                #     4. Create DOES_AUDIT link
                res = service.select_auditor(batch_id, user_audit)
                if Status.has_failed(res):
                    raise(IsotammiException, here)
                if res.get("status") == Status.UPDATED:
                    flash( _("You are now an auditor for batch ") + batch_id )
                    msg = res.get("msg")
                    print(f"--> {here}(C): {msg}")
                    syslog.log(type=f"Start auditing", batch=batch_id, msg=msg)
                # ? - (1) Remove HAS_ACCESS, if exists
                # res = service.purge_old_access(batch_id, user_audit)

            elif operation == "accept":
                # 6. Move from "Auditing" to "Accepted" state
                res = service.set_audited(batch_id, user_audit, State.ROOT_ACCEPTED)
                if Status.has_failed(res):
                    msg = _(f"Audit request {operation} failed")
                    flash(msg, "error")
                    return redirect(url_for("audit.audit_pick", batch_id=batch_id))
                else:
                    auditors_list = res.get("auditors")
                    print(f"auditor_ops: Batch {batch_id} accepted by {user_audit!r}, "
                          f"auditors: {auditors_list}")
                    msg = _("Audit batch accepted: ") + batch_id
                    flash(msg)

            elif operation == "reject":
                # 7. Move from "Auditing" to "Rejected" state, if no other auditors exist
                res = service.set_audited(batch_id, user_audit, State.ROOT_REJECTED)
                msg = _("You have rejected the audition of batch %(bid)s",
                        bid=batch_id)
                flash(msg)

            elif operation == "withdraw":
                # 8. Stop auditing this batch. New state is "Audit requested".
                # (4) Change DOES_AUDIT -> DID_AUDIT, ts_to=now
                res = service.remove_auditor(batch_id, user_audit)
                d_days = int(round(res.get('d_days', 0.0)+0.5, 0))
                msg = _("You did audit the batch %(bid)s for %(d)s days",
                        bid=batch_id, d=d_days)
                flash(msg)

            else:
                return redirect(url_for("audit.list_uploads", batch_id=batch_id))

    except Exception as e:
        if msg:
            flash(msg)
        error_print("auditor_ops", e)
        return redirect(url_for("audit.audit_pick", batch_id=batch_id))
        #return redirect(url_for("audit.list_uploads"))

    syslog.log(type="Audit state change", batch=batch_id, op=operation, msg=msg)
    return redirect(url_for("audit.audit_pick", batch_id=batch_id))
    #return redirect(url_for("audit.list_uploads", batch_id=batch_id))


@bp.route("/audit/batch_download/<batch_id>/<username>")
@login_required
@roles_accepted("audit")
def audit_batch_download(batch_id, username):
    batch = Root.get_batch(username, batch_id)
    if batch:
        try:
            xml_folder, xname = os.path.split(batch.file)
            if batch.xmlname:
                xname = batch.xmlname
            abs_folder = os.path.abspath(xml_folder)
            logger.info("--> bp.audit.routes.audit_batch_download "
                        f"u={username} b={batch_id} {xname!r}")
            syslog.log(type="Auditor xml download", 
                       batch=batch_id, by=f"{username} ({batch.rel_type})",
                       file=xname)
    
            return send_from_directory(
                abs_folder, xname,
                mimetype="application/gzip",
                as_attachment=True,
            )
        except Exception as e:
            print(f"audit_batch_download: {e.__class__.__name__}: {e}")
            msg = _("The file does not exist any more: ") + xname
            print(f"audit_batch_download: {msg}")
    else:
        msg = _("Not allowed to load this batch: ")+batch_id+"/"+username

    title = _('Error in file loading')
    return f"<h1>{title}</h1><p><b>{msg}</b></p>"\
        f"<p><a href='javascript:history.back()'>{ _('Return') }</a></p>"
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

# @bp.route("/audit/list/refnames")
# def read_refnames():
#     """ Obsolete: Reads all Refname objects for table display
#         (n:Refname)-[r]->(m)
#
#     NOTE. Refname to basename relations do net exist any more (after 24.4.2020 
#     """
#     recs = Refname.get_refnames()
#     #return (recs)
#     return render_template("/audit/refnames_list.html", names=recs)

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


# --------------------- White lists for types ----------------------------


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

