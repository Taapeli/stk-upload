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

import json
import traceback

import logging

logger = logging.getLogger("stkserver")

from flask import render_template, request, redirect, url_for, send_from_directory
from flask import flash, session, jsonify
from flask_security import login_required, roles_accepted, roles_required, current_user
from flask_babelex import _

import shareds
from ui.user_context import UserContext
from bl.base import Status
from bl.person import PersonWriter

from setups import User
from bp.admin.forms import UpdateUserProfileForm, UpdateUserForm
from bl.admin.models.data_admin import DataAdmin
from bl.admin.models.user_admin import UserAdmin
from bl.root import Root

from . import bp
from . import uploads
from ..gedcom.models import gedcom_utils
from .. import gedcom

from models import util, email, syslog


# Admin start page
@bp.route("/admin", methods=["GET", "POST"])
@login_required
@roles_accepted("admin", "master")
def admin():
    """ Home page for administrator """
    logger.info("-> bp.admin.routes.admin")
    return render_template("/admin/admin.html")


@bp.route("/admin/clear_db/<string:opt>")
@login_required
@roles_required("admin")
def clear_db(opt):
    """ Clear database - with no confirmation! """
    try:
        updater = DataAdmin(current_user)
        result = updater.db_reset(opt)  # dbutil.alusta_kanta()
        logger.info(f"-> bp.admin.routes.clear_db/{opt} n={result['count']}")
        return render_template("/talletettu.html", text=result["msg"])
    except Exception as e:
        traceback.print_exc()
        return redirect(
            url_for("virhesivu", code=1, text=", ".join((str(e), result["msg"])))
        )


@bp.route("/admin/clear_my_own")
@login_required
@roles_accepted("research")
def clear_my_db():
    """ Clear database - with no confirmation! """
    try:
        updater = DataAdmin(current_user)
        msg = updater.db_reset("my_own")  # dbutil.alusta_kanta()
        logger.info(f"-> bp.admin.routes.clear_my_db")
        return render_template("/talletettu.html", text=msg)
    except Exception as e:
        return redirect(url_for("virhesivu", code=1, text=str(e)))


@bp.route("/admin/start_initiate")
@login_required
@roles_accepted("admin")
def start_initiate():
    """ Check and initiate important nodes and constraints and schema fixes.
    """
    from database.accessDB import re_initiate_nodes_constraints_fixes, initialize_db

    logger.info(f"-> bp.admin.routes.start_initiate")

    # Remove (:Lock{id:'initial'})
    re_initiate_nodes_constraints_fixes()

    initialize_db()
    flash(_("Database initial check done."))
    return redirect(url_for("admin.admin"))


@bp.route("/admin/clear_batches", methods=["GET", "POST"])
@login_required
@roles_accepted("research", "admin", "audit")
def clear_empty_batches():
    """ Show or clear unused batches. """
    user = None
    clear = False
    cnt = -1
    try:
        if request.form:
            clear = request.form.get("clear", False)
            if clear:
                cnt = Root.drop_empty_batches()
                if cnt == 0:
                    flash(_("No empty batches removed"), "warning")
                pass
        logger.info(f"-> bp.admin.routes.clear_empty_batches {cnt}")
        batches = Root.list_empty_batches()
    except Exception as e:
        return redirect(url_for("virhesivu", code=1, text=str(e)))

    logger.info(
        f"-> bp.admin.routes.clear_empty_batches/{'clean' if clear else 'show'}"
    )
    return render_template(
        "/admin/batch_clear.html", uploads=batches, user=user, removed=cnt
    )


# TODO Ei varmaan pitäisi enää olla käytössä käytössä?
@bp.route("/admin/set/estimated_dates")
@bp.route("/admin/set/estimated_dates/<int:uid>")
@login_required
@roles_required("admin")
def estimate_dates(uid=None):
    """ syntymä- ja kuolinaikojen arvioiden asettaminen henkilöille """
    # logger.warning(f"OBSOLETE? -> bp.admin.routes.estimate_dates sel={uid}")
    if uid:
        uids = list(uid)
    else:
        uids = []
    # message = dataupdater.set_person_estimated_dates(uids)
    # ext = _("estimated lifetime")
    # return render_template("/talletettu.html", text=msg, info=ext)

    u_context = UserContext(session, current_user, request)
    with PersonWriter("update", u_context) as service:
        ret = service.set_estimated_lifetimes(uids)

    if Status.has_failed(ret):
        msg = ret.get("statustext")
        logger.error(f"bp.admin.routes.estimate_dates {msg}")
        flash(ret.get("statustext"), "error")
    else:
        msg = _("Estimated {} person lifetimes").format(ret["count"])
        flash(msg, "info")
    print("bp.admin.routes.estimate_dates: " + msg)
    return redirect(url_for("admin.admin"))


# # Ei ilmeisesti käytössä
# @bp.route('/admin/aseta/confidence')
# @roles_required('admin')
# def aseta_confidence():
#     """ tietojen laatuarvion asettaminen henkilöille """
#     dburi = dbutil.get_server_location()
#     message = dataupdater.set_confidence_value()
#     return render_template("/talletettu.html", text=message, uri=dburi)


@bp.route("/admin/list_users", methods=["GET"])
@login_required
@roles_accepted("admin", "audit", "master")
def list_users():
    def keyfunc(attrname):
        def f(user):
            return getattr(user, attrname).lower()

        return f

    sortby = request.args.get("sortby")
    lista = shareds.user_datastore.get_users()
    if sortby:
        lista.sort(key=keyfunc(sortby))

    logging.info(f"-> bp.admin.routes.list_users n={len(lista)}")
    return render_template("/admin/list_users.html", users=lista, sortby=sortby)


@bp.route("/admin/update_user/<username>", methods=["GET", "POST"])
@login_required
@roles_accepted("admin", "master")
def update_user(username):
    """ A User is created or approved or ...
    """
    # d = Domain("translations/sv/LC_MESSAGES")
    # s = d.gettext("Return")
    # print("s:",s)

    form = UpdateUserForm()
    if form.validate_on_submit():
        # Create a setups.User object
        user = User(
            id=form.id.data,
            email=form.email.data,
            username=form.username.data,
            name=form.name.data,
            language=form.language.data,
            is_active=form.is_active.data,
            roles=form.roles.data,
            confirmed_at=form.confirmed_at.data,
            last_login_at=form.last_login_at.data,
            last_login_ip=form.last_login_ip.data,
            current_login_at=form.current_login_at.data,
            current_login_ip=form.current_login_ip.data,
            login_count=form.login_count.data,
        )
        updated_user = UserAdmin.update_user(user)
        if updated_user.username == current_user.username:
            session["lang"] = form.language.data
        if form.approve.data:
            # use user's language; see https://stackoverflow.com/a/46036518
            from flask import Flask
            from flask_babelex import Locale

            app = Flask("app")
            host = request.host  # save the actual host
            with app.test_request_context() as ctx:
                lang = form.language.data
                ctx.babel_locale = Locale.parse(lang)
                subject = _("Isotammi user approved")
                msg = _(
                    "You are now approved to use Isotammi at {server} with user name {user}."
                )
                msg = msg.format(server=f"http://{host}", user=form.username.data)
            email.email_from_admin(subject, msg, form.email.data)
        logging.info(f"-> bp.admin.routes.update_user u={form.email.data}")
        flash(_("User updated"))
        # Return to same page
        return redirect(url_for("admin.update_user", username=updated_user.username))

    # Fill form fields by updated values
    user = shareds.user_datastore.get_user(username)
    form.id.data = user.id
    form.email.data = user.email
    form.username.data = user.username
    form.name.data = user.name
    form.language.data = user.language
    form.is_active.data = user.is_active
    form.roles.data = [role.name for role in user.roles]
    form.confirmed_at.data = user.confirmed_at
    form.last_login_at.data = user.last_login_at
    form.last_login_ip.data = user.last_login_ip
    form.current_login_at.data = user.current_login_at
    form.current_login_ip.data = user.current_login_ip
    form.login_count.data = user.login_count

    userprofile = shareds.user_datastore.get_userprofile(username)
    form2 = UpdateUserProfileForm()
    if userprofile:  # 'master' does not have a profile
        form2.agreed_at.data = userprofile.agreed_at
        form2.GSF_membership.data = userprofile.GSF_membership
        form2.software.data = userprofile.software
        form2.research_years.data = userprofile.research_years
        form2.researched_names.data = userprofile.researched_names
        form2.researched_places.data = userprofile.researched_places
        form2.software.data = userprofile.software
        form2.software.data = userprofile.software
        form2.text_message.data = userprofile.text_message
    # Return to same page
    return render_template(
        "/admin/update_user.html", username=user.username, form=form, form2=form2
    )


@bp.route("/admin/list_uploads/<username>", methods=["GET"])
@login_required
@roles_accepted("admin", "audit")
def list_uploads(username):
    """ List uploads; also from '/audit/list_uploads' page. """
    upload_list = uploads.list_uploads(username)
    logger.info(f"-> bp.admin.routes.list_uploads u={username}")
    return render_template("/admin/uploads.html", uploads=upload_list, user=username)


@bp.route("/admin/list_uploads_all", methods=["POST"])
@login_required
@roles_accepted("admin", "audit")
def list_uploads_for_users():
    requested_users = request.form.getlist("select_user")
    if len(requested_users) == 0:
        users = shareds.user_datastore.get_users()  # default: all users
    else:
        users = [
            user
            for user in shareds.user_datastore.get_users()
            if user.username in requested_users
        ]
    upload_list = list(uploads.list_uploads_all(users))
    logger.info(f"-> bp.admin.routes.list_uploads_for_users n={len(upload_list)}")
    return render_template("/admin/uploads.html", uploads=upload_list, users=users)


@bp.route("/admin/list_uploads_all", methods=["GET"])
@login_required
@roles_accepted("admin")
def list_uploads_all():
    users = shareds.user_datastore.get_users()
    upload_list = list(uploads.list_uploads_all(users))
    logger.info(f"-> bp.admin.routes.list_uploads_all n={len(upload_list)}")
    return render_template("/admin/uploads.html", uploads=upload_list)


@bp.route("/admin/start_upload/<username>/<xmlname>", methods=["GET"])
@login_required
@roles_accepted("admin", "audit")
def start_load_to_stkbase(username, xmlname):
    uploads.initiate_background_load_to_stkbase(username, xmlname)
    logger.info(f'-> bp.admin.routes.start_load_to_stkbase u={username} f="{xmlname}"')
    flash(_("Data import from %(i)s to database has been started.", i=xmlname), "info")
    return redirect(url_for("admin.list_uploads", username=username))


@bp.route("/admin/list_threads", methods=["GET"])
@login_required
@roles_accepted("admin", "audit")
def list_threads():
    """ Thread list for debugging. """
    import threading

    s = "<pre>\n"
    s += "Threads:\n"
    for t in threading.enumerate():
        s += "  " + t.name + "\n"
    s += "-----------\n"
    s += "Current thread: " + threading.current_thread().name
    s += "</pre>"
    return s


# @bp.route("/admin/xml_download/<username>/<xmlfile>")
# @login_required
# @roles_accepted("admin")
# def admin_xml_download(username, xmlfile):
#removed 8.10.2021/JMä


@bp.route("/admin/show_upload_log/<username>/<xmlfile>/<batch_id>")
@login_required
@roles_accepted("member", "admin", "audit")
def show_upload_log(username, xmlfile, batch_id=None):
    upload_folder = uploads.get_upload_folder(username)
    for fname in [
            os.path.join(upload_folder, batch_id, xmlfile + ".log"),
            os.path.join(upload_folder, xmlfile + ".log")
        ]:
        try:
            msg = open(fname, encoding="utf-8").read()
            break
        except FileNotFoundError:
            #print(f"bp.admin.routes.show_upload_log: no file {fname}")
            pass

    logger.info(f"-> bp.admin.routes.show_upload_log f={fname}")
    return render_template("/admin/load_result.html", msg=msg)


@bp.route("/admin/xml_delete/<username>/<xmlfile>")
@login_required
@roles_accepted("admin", "audit")
def xml_delete(username, xmlfile):
    msg = f" Deleting of \"{xmlfile}\" is blocked before the batch is deleted, too!"
    flash(msg)
    print("bp.admin.routes.xml_delete" + msg)
    
    # uploads.delete_files(username, xmlfile)
    # syslog.log(type="gramps file uploaded", file=xmlfile, user=username)
    logger.error(f'-> bp.admin.routes.xml_delete f="{xmlfile}"')
    # TODO: Return to list_uploads_all, if called from there
    return redirect(url_for("admin.list_uploads", username=username))


# ------------------- GEDCOMs -------------------------


def list_gedcoms(users):
    for user in users:
        for f in gedcom_utils.list_gedcoms(user.username):
            yield (user.username, f)


@bp.route("/admin/list_user_gedcoms/<user>", methods=["GET"])
@login_required
@roles_accepted("admin", "audit")
def list_user_gedcoms(user):
    session["gedcom_user"] = user
    logger.info(f"-> bp.admin.routes.list_user_gedcoms u={user}")
    return gedcom.routes.gedcom_list()


@bp.route("/admin/list_user_gedcom/<user>/<gedcomname>", methods=["GET"])
@login_required
@roles_accepted("admin", "audit")
def list_user_gedcom(user, gedcomname):
    session["gedcom_user"] = user
    logger.info(f'-> bp.admin.routes.list_user_gedcom u={user} f="{gedcomname}"')
    return gedcom.routes.gedcom_info(gedcomname)


@bp.route("/admin/list_gedcoms_for_users", methods=["POST"])
@login_required
@roles_accepted("admin", "audit")
def list_gedcoms_for_users():
    requested_users = request.form.getlist("select_user")
    if len(requested_users) == 0:
        users = shareds.user_datastore.get_users()  # default: all users
    else:
        users = [
            user
            for user in shareds.user_datastore.get_users()
            if user.username in requested_users
        ]
    gedcom_list = list(list_gedcoms(users))
    logger.info(f"-> bp.admin.routes.list_gedcoms_for_users n={len(users)}")
    return render_template(
        "/admin/gedcoms.html",
        gedcom_list=gedcom_list,
        num_requested_users=len(requested_users),
        users=users,
        num_users=len(users),
    )


# ------------------- Email -------------------------
@bp.route("/admin/send_email", methods=["POST"])
@login_required
@roles_accepted("admin", "audit")
def send_email():
    requested_users = request.form.getlist("select_user")
    emails = [
        user.email
        for user in shareds.user_datastore.get_users()
        if user.username in requested_users
    ]
    logger.info(f"-> bp.admin.routes.send_email n={len(requested_users)}")
    return render_template(
        "/admin/message.html", users=", ".join(requested_users), emails=emails
    )


@shareds.app.route("/admin/send_emails", methods=["post"])
@login_required
@roles_accepted("admin", "audit")
def send_emails():
    subject = request.form["subject"]
    body = request.form["message"]
    receivers = request.form.getlist("email")
    logger.info(f"-> bp.admin.routes.send_emails n={len(receivers)}")
    for receiver in receivers:
        email.email_from_admin(subject, body, receiver)
    return "ok"


# ------------------- Site map -------------------------


def find_roles(endpoint, endpoints):
    info = endpoints.get(endpoint)
    if not info:
        return False, []
    roles = []
    if info.roles_accepted:
        roles += info.roles_accepted
    if info.roles_required:
        roles += info.roles_required
    return info.login_required, roles


@bp.route("/admin/site-map")
@login_required
@roles_accepted("admin")
def site_map():
    "Show list of application route paths"

    class Link:
        def __init__(
            self,
            url="",
            endpoint="",
            methods="",
            desc="",
            roles="",
            login_required=False,
        ):
            self.url = url
            self.endpoint = endpoint
            self.methods = methods
            self.desc = desc
            self.roles = roles
            self.login_required = login_required

    links = []

    endpoints = util.scan_endpoints()
    logger.info(f"-> bp.admin.routes.site_map n={len(endpoints)}")
    for rule in shareds.app.url_map.iter_rules():
        # if not rule.endpoint.startswith("admin.clear"): continue
        # print(dir(rule.methods))
        # print(rule.methods)
        methods = ""
        roles = ""
        if "GET" in rule.methods:
            methods = "GET"
        if "POST" in rule.methods:
            methods += " POST"
        try:
            # print("{} def {}".format(rule.rule, rule.defaults))
            url = rule.rule
            # url = url_for(rule.endpoint, **(rule.defaults or {}))
            try:
                _view_function = shareds.app.view_functions[rule.endpoint]
                login_required, roles = find_roles(rule.rule, endpoints)
            except:
                traceback.print_exc()
                pass
        except:
            traceback.print_exc()
            url = "-"
        links.append(
            Link(
                url,
                rule.endpoint,
                methods,
                roles=",".join(roles),
                login_required=login_required,
            )
        )

    return render_template("/admin/site-map.html", links=links)


# ------------------- Application log -------------------------
@bp.route("/admin/readlog")
@login_required
@roles_accepted("admin", "audit")
def readlog():
    """ Show log events.
        Layout depend on role: reddish for admin, yellowish for audit
    """
    direction = request.args.get("direction")
    startid_arg = request.args.get("id")
    if startid_arg:
        startid = int(startid_arg)
    else:
        startid = None
    recs = syslog.readlog(direction, startid)
    logger.info(f"-> bp.admin.routes.readlog")  # n={len(recs)}")
    return render_template("/admin/syslog.html", recs=recs)


# ------------------- Access Management -------------------------
@bp.route("/admin/access_management")
@login_required
@roles_accepted("admin")
def access_management():
    return render_template("/admin/access_management.html")


@bp.route("/admin/fetch_users", methods=["GET"])
@login_required
@roles_accepted("admin")
def fetch_users():
    userlist = shareds.user_datastore.get_users()
    users = [
        dict(username=user.username, name=user.name, email=user.email)
        for user in userlist
        if user.username != "master"
    ]
    return jsonify(users)


@bp.route("/admin/fetch_batches", methods=["GET"])
@login_required
@roles_accepted("admin")
def fetch_batches():
    batch_list = list(Root.get_batches())
    for b in batch_list:
        file = b.get("file")
        if file:
            file = (
                file.split("/")[-1]
                .replace("_clean.gramps", ".gramps")
                .replace("_clean.gpkg", ".gpkg")
            )
            b["file"] = file
    return jsonify(batch_list)


@bp.route("/admin/fetch_accesses", methods=["GET"])
@login_required
@roles_accepted("admin")
def fetch_accesses():
    access_list = UserAdmin.get_accesses()
    return jsonify(access_list)


@bp.route("/admin/add_access", methods=["POST"])
@login_required
@roles_accepted("admin")
def add_access():
    data = json.loads(request.data)
    print(data)
    username = data.get("username", "-")
    batchid = data.get("batchid", "-")
    # TODO Should log the batch owner, not batchid?
    logger.info(f"-> bp.admin.routes.add_access u={username} batch={batchid}")
    rsp = UserAdmin.add_access(username, batchid)
    print(rsp)
    print(rsp.get("r"))
    return jsonify(dict(rsp.get("r")))


@bp.route("/admin/delete_accesses", methods=["POST"])
@login_required
@roles_accepted("admin")
def delete_accesses():
    data = json.loads(request.data)
    logger.info(f"-> bp.admin.routes.delete_accesses")
    rsp = UserAdmin.delete_accesses(data)
    return jsonify(rsp)

@bp.route("/admin/build_free_text_search_indexes", methods=["GET"])
@login_required
@roles_accepted("admin")
def build_indexes():
    res = DataAdmin.build_free_text_search_indexes()
    return render_template("/admin/free_text_indexes.html", res=res)
