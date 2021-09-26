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

# Flask routes program for Stk application
# @ Sss 2016
# JMä 29.12.2015

# Blacked 2021-05-18 / JMä
import logging
import traceback
from operator import itemgetter

from werkzeug.utils import redirect
from flask.helpers import url_for

from ..gedcom.models import gedcom_utils
from ui.user_context import UserContext
from bl.person import PersonReader
import shareds
from bl.root import Root
#from bp.dupsearch.models.search import batches

logger = logging.getLogger("stkserver")

from flask import render_template, request, session, flash
from flask_security import login_required, current_user, utils as secutils

# rom flask_security import login_required, roles_accepted, current_user, utils as secutils
from flask_babelex import _, get_locale

from models import email
from bp.api import api

from bp.start.forms import JoinForm

""" Application route definitions
"""


@shareds.app.before_request
def force_https():
    if not shareds.app.config.get("FORCE_HTTPS"):
        return
    if request.endpoint in shareds.app.view_functions and not request.is_secure:
        host = request.host.split(":")[0]
        if host in {"localhost", "127.0.0.1"}:
            return
        return redirect(request.url.replace("http://", "https://"))


@shareds.app.route("/home")
def home():
    "  Home page. "
    from routes import entry

    return redirect(entry)


@shareds.app.route("/start/guest", methods=["GET", "POST"])
def start_guest():
    """Scene start page for a guest user."""
    user = shareds.user_datastore.get_user("guest")
    secutils.login_user(user)
    lang = request.args.get("lang")
    if lang:
        session["lang"] = lang

    logger.info(f"-> bp.start.routes.start_guest, lang={lang}")
    return redirect("/scene/persons/search")
    # is_demo = shareds.app.config.get('DEMO', False)
    # return render_template('/start/osolete_index_guest.html', is_demo=is_demo)


@shareds.app.route("/start/persons/search", methods=["GET", "POST"])
def start_guest_search():
    """Scene start page for a guest user."""
    user = shareds.user_datastore.get_user("guest")
    secutils.login_user(user)
    lang = request.args.get("lang")
    if lang:
        session["lang"] = lang

    logger.info(f"-> bp.start.routes.start_guest_search, lang={lang}")
    # See: https://stackoverflow.com/questions/15473626/make-a-post-request-while-redirecting-in-flask/15480983#15480983
    return redirect("/scene/persons/search", code=307)


@shareds.app.route("/start/logged", methods=["GET", "POST"])
@login_required
# @roles_accepted('member', 'gedcom', 'research', 'audit', 'admin')
def start_logged():
    """Opening the home page for logged in user (from login page or home button)
    or anonymous user (home).

    Note. The home page for anonymous user is routes.entry in app/routes.py
    """
    if "gedcom_user" in session:
        del session["gedcom_user"]

    role_names = [role.name for role in current_user.roles]
    logger.info(f"-> bp.start.routes.start_logged")
    logger.debug(
        f"bp.start.routes.start_logged"
        f" lang={get_locale().language}"
        f" user={current_user.username}/{current_user.email}"
        f" roles= {role_names}"
    )

    print(f"start_logged: is_authenticated={current_user.is_authenticated}, "\
          f"to_be_approved={current_user.has_role('to_be_approved')}")
    if current_user.is_authenticated and current_user.has_role("to_be_approved"):
        # Home page for logged in user
        logger.info(f"-> start.routes.entry/join")
        return redirect(url_for("join"))

    surnamestats = []
    is_demo = shareds.app.config.get("DEMO", False)
    if is_demo:
        # Get surname cloud data
        u_context = UserContext(session, current_user, request)
        u_context.user = None

        with PersonReader("read", u_context) as service:
            print(f"#> routes.entry: datastore = {service}")
            minfont = 6
            maxfont = 20
            # maxnames = 40
            surnamestats = service.get_surname_list()
            print(f"#start_logged DEMO: show {len(surnamestats)} surnames")
            for i, stat in enumerate(surnamestats):
                stat["order"] = i
                stat["fontsize"] = maxfont - i * (maxfont - minfont) / len(surnamestats)
            surnamestats.sort(key=itemgetter("surname"))

    my_batches = Root.get_my_batches(current_user.username)
    return render_template(
        "/start/index_logged.html", is_demo=is_demo, surnamestats=surnamestats,
        batches=my_batches # sorted(my_batches, key=itemgetter("id"))
    )


@shareds.app.route("/thankyou")
def thankyou():
    return render_template("/start/thankyou.html")


@shareds.app.route("/join", methods=["GET", "POST"])
@login_required
def join():
    from bl.admin.models.user_admin import UserProfile, UserAdmin

    form = JoinForm()
    logger.info("-> bp.start.routes.join")
    if form.validate_on_submit():
        msg = ""
        username = request.form["username"]
        for name, value in request.form.items():
            if name == "csrf_token":
                continue
            if name == "submit":
                continue
            msg += f"\n{name}: {value}"
        msg += f"\n\nApprove user: http://{request.host}/admin/update_user/{username}"
        if email.email_admin(
            "New user request for Isotammi", msg, sender=request.form.get("email")
        ):
            flash(_("Join message sent"))
        else:
            flash(_("Sending join message failed"))
        print("GSF_membership", request.form.get("GSF_membership"))
        profile = UserProfile(
            name=request.form.get("name"),
            username=request.form.get("username"),
            email=request.form.get("email"),
            language=request.form.get("language"),
            GSF_membership=request.form.get("GSF_membership"),
            research_years=request.form.get("research_years"),
            software=request.form.get("software"),
            researched_names=request.form.get("researched_names"),
            researched_places=request.form.get("researched_places"),
            text_message=request.form.get("text_message"),
        )
        # Store to UserProfile node
        UserAdmin.update_user_profile(profile)
        return redirect(url_for("thankyou"))

    return render_template("/start/join.html", form=form)


@shareds.app.route("/message")
@login_required
def my_message():
    return render_template("/start/my_message.html")


@shareds.app.route("/send_email", methods=["post"])
@login_required
def send_email():
    subject = request.form["subject"]
    body = request.form["message"]
    ok = email.email_admin(
        _(subject), body, sender=(current_user.name, current_user.email)
    )
    if ok:
        return "ok"
    else:
        return "failed"


@shareds.app.route("/settings", methods=["GET", "POST"])
@login_required
def my_settings():
    lang = request.form.get("lang")
    is_guest = current_user.username == "guest"
    referrer = request.form.get("referrer", default=request.referrer)
    if lang:
        try:
            from bl.admin.models.user_admin import UserAdmin  # can't import earlier

            current_user.language = lang
            result = UserAdmin.update_user_language(current_user.username, lang)
            if not result:
                flash(_("Update did not work1"), category="flash_error")
            session["lang"] = lang
        except:
            flash(_("Update did not work"), category="flash_error")
            traceback.print_exc()

    labels, user_batches = Root.get_user_stats(current_user.username)
    print(f"#bp.start.routes.my_settings: User batches {user_batches}")

    gedcoms = gedcom_utils.list_gedcoms(current_user.username)
    print(f"#bp.start.routes.my_settings: Gedcoms {gedcoms}")

    userprofile = shareds.user_datastore.get_userprofile(current_user.username)

    logger.info("-> bp.start.routes.my_settings")
    return render_template(
        "/start/my_settings.html",
        is_guest=is_guest,
        referrer=referrer,
        roles=current_user.roles,
        apikey=api.get_apikey(current_user),
        labels=labels,
        batches=user_batches,
        gedcoms=gedcoms,
        userprofile=userprofile,
    )

# @shareds.app.route("/my_batches/", methods=["GET"])
# @shareds.app.route("/my_batches/<selected_batch_id>", methods=["GET"])
# @login_required
# def my_batches(selected_batch_id=None):
#     batches = [
#         {"batch_id": "2021-08-07.501","batch_file":"X1testtree.gramps"},
#         {"batch_id": "2021-08-07.502","batch_file":"X2testtree.gramps"},
#     ]
#     return render_template(
#         "/start/hx-batches.html",
#     batches=batches
#     )
    

# # Admin start page in bp.admin
# @shareds.app.route('/admin',  methods=['GET', 'POST'])
# @login_required
# @roles_accepted('admin', 'master')
# def admin():
#     """ Home page for administrator """
#     logger.info("-> bp.start.routes.admin")
#     return render_template('/admin/admin.html')
