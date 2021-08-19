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
import time
import logging
import traceback
from io import StringIO, BytesIO

logger = logging.getLogger("stkserver")

from . import bp

from flask import render_template, request, redirect, url_for, flash
from flask import send_file
from flask_security import login_required, roles_accepted, current_user
from flask_babelex import _

import shareds
from bl.root import Root, State, BatchUpdater
from bl.base import Status
from bl.person import Person, PersonWriter
from bl.refname import Refname
from bl.audit.models.batch_merge import BatchMerger

from bp.admin.csv_refnames import load_refnames
from bp.admin import uploads
from models import syslog, loadfile


@staticmethod
def _get_server_location():
    # Returns server address as a str
    dbloc = shareds.driver.address
    return ":".join((dbloc[0], str(dbloc[1])))


@bp.route("/audit")
@login_required
@roles_accepted("audit")
def audit_home():
    return render_template("/audit/index.html")


# ------------------------- User Gramps uploads --------------------------------


@bp.route("/audit/list_uploads", methods=["GET"])
@login_required
@roles_accepted("audit")
def list_uploads():
    """ Show Batches

        The list of Gramps uploads is filtered by an existing Batch node
    """
    users = shareds.user_datastore.get_users()
    upload_list = list(uploads.list_uploads_all(users))
    logger.info(f"-> bp.audit.routes.list_uploads")
    return render_template("/audit/batches.html", uploads=upload_list)


# --------------------- Move Batch to Approved data ----------------------------


@bp.route("/audit/start/<batch_id>", methods=["GET", "POST"])
@login_required
@roles_accepted("audit")
def audit_start(batch_id):
    """ Confirm Batch move to Isotammi database """
    username, root, labels = Root.get_batch_stats(batch_id)
    total = 0
    for _label, cnt in labels:
        total += cnt
    time = root.timestamp_str()

    return render_template(
        "/audit/move_in_1.html",
        user=username,
        root=root,
        label_nodes=labels,
        total=total,
        time=time,
    )


@bp.route("/audit/requested", methods=["POST"])
@login_required
@roles_accepted("audit")
def audit_requested(batch_id):
    """ Move the accepted Batch to Audit queue """
    userid = request.form["user"]
    batch_id = request.form["batch"]
    #auditor = current_user.username
    msg= "TODO"
    with BatchUpdater("update") as batch_service:
        res = batch_service.change_state(batch_id, 
                                         userid, 
                                         State.ROOT_AUDIT_REQUESTED)
        if Status.has_failed(res):
            msg = "Audit request failed"
            flash(_(msg), "error")
        else:
            msg = "Audit request done"
            flash(_(msg))

    print("bp.audit.routes.audit_requested: {res.status}")
    syslog.log(type="Audit request", batch=batch_id, by=userid, msg=msg)
    return redirect(url_for("audit.audit_start", batch_name=batch_id))


@bp.route("/audit/movenow", methods=["POST"])
@login_required
@roles_accepted("audit")
def obsolete_move_in_2():
    """ Move the accepted Batch to Isotammi database """

    owner = request.form["user"]
    batch_id = request.form["batch"]
    auditor = current_user.username
    logger.info(f" bp.audit.routes.move_in_2 u={owner} b={batch_id}")
    with BatchUpdater("update") as batch_service:
        res = batch_service.change_state(batch_id, owner)
        msg = "Asked for auditing"

    # try:
    #     merger = BatchMerger()
    #     res = merger.obsolete_move_whole_batch(batch_id, owner, auditor)
    #     if res:
    #         msg = "Transfer succeeded"
    #         flash(_(msg))
    #     else:
    #         msg = "Transfer failed"
    #         flash(_(msg), "error")
    # except Exception as e:
    #     traceback.print_exc()
    #     msg = f"BatchMerger.obsolete_move_whole_batch FAILED: {e}"
    #     flash(msg, "error")
    #     logger.error(f"{msg} {e.__class__.__name__} {e}")
    
    syslog.log(type="batch to Common data", batch=batch_id, by=owner, msg=msg)
    return redirect(url_for("audit.audit_start", batch_name=batch_id))


# --------------------- Delete an approved data batch ----------------------------


@bp.route("/audit/batch_delete/<batch_id>", methods=["POST"])
@login_required
@roles_accepted("audit")
def delete_approved(batch_id):
    """ Confirm approved batch delete
    """
    (msg, _nodes_deleted) = Root.delete_audit(current_user.username, batch_id)
    if msg != "":
        logger.error(f"{msg}")
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
        material = request.form["material"]
        logging.info(f"-> bp.audit.routes.upload_csv/{material} f='{infile.filename}'")

        loadfile.upload_file(infile)
        if "destroy" in request.form and request.form["destroy"] == "all":
            logger.info("-> bp.audit.routes.upload_csv/delete_all_Refnames")
            # datareader.recreate_refnames()
            Refname.recreate_refnames()

    except Exception as e:
        return redirect(url_for("virhesivu", code=1, text=str(e)))

    return redirect(
        url_for("audit.save_loaded_csv", filename=infile.filename, subj=material)
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
