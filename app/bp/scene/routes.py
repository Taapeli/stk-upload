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
Created on 12.8.2018

@author: jm
"""
# blacked 25.5.2021/JMä
import io
import os
import traceback
import json

import logging

logger = logging.getLogger("stkserver")
from operator import itemgetter
import time
from datetime import datetime
from types import SimpleNamespace


from flask import send_file, Response, jsonify
from flask import (
    render_template,
    request,
    redirect,
    url_for,
    flash,
    session as user_session,
)
from flask_security import current_user, login_required, roles_accepted
from flask_babelex import _

import shareds
from models import util

from . import bp
from bl.base import Status, StkEncoder
from bl.place import PlaceReader
from bl.source import SourceReader
from bl.family import FamilyReader
from bl.event import EventReader, EventWriter
from bl.person import PersonReader, PersonWriter
from bl.person_reader import PersonReaderTx
from bl.media import MediaReader
from bl.comment import CommentReader

from ui.user_context import UserContext
from ui import jinja_filters

from bp.scene.models import media
from bp.graph.models.fanchart import FanChart

# Select the read driver for current database
# from database.accessDB import get_dataservice
# opt = "read_tx" --> Neo4jReadServiceTx # initiate when used
# opt = "read" --> Neo4jReadService


calendars = [_("Julian"), _("Hebrew")]  # just for translations


def stk_logger(context, msg: str):
    """Emit logger info message with Use Case mark uc=<code> ."""
    if not context:
        logger.info(msg)
        return
    uc = context.use_case()
    if (msg[:2] != "->") or (uc == ""):
        logger.info(msg)
        return
    logger.info(f"-> {msg[2:]} uc={uc}")
    return


# ------------------------- Menu 1: Person search ------------------------------


def _do_get_persons(args):
    """Execute persons list query by arguments.

        Persons, current
            GET    /all                                       --> args={pg:all}
        Persons, forward
            GET    /all?fw=<sortname>&c=<count>               --> args={pg:all,fw:sortname,c:count}
    #     Persons, by years range
    #         GET    /all?years=<y1-y2>                         --> args={pg:all,years:y1_y2}
    #     Persons fw,years
    #         GET    /all?years=<y1-y2>&fw=<sortname>&c=<count> --> args={pg:all,fw:sortname,c:count,years:y1_y2}
        Search form
            GET    /search                                    --> args={pg:search,rule:start}
        Search by refname
            GET    /search?rule=ref,key=<str>                 --> args={pg:search,rule:ref,key:str}
        Search form
            POST   /search                                    --> args={pg:search,rule:start}
        Search by name starting or years
            POST   /search rule=<rule>,key=<str>              --> args={pg:search,rule:ref,key:str}
    #     Search by years range
    #         POST   /search years=<y1-y2>                      --> args={pg:search,years:y1_y2}
    #     Search by name & years
    #         POST   /search rule=<rule>,key=<str>,years=<y1-y2> --> args={pg:search,rule:ref,key:str,years:y1_y2}
    """
    u_context = UserContext(user_session, current_user, request)
    if args.get("pg") == "search":
        # No scope
        u_context.set_scope_from_request()
        if args.get("rule", "start") == "start" or args.get("key", "") == "":
            return {"rule": "start", "status": Status.NOT_STARTED}, u_context
    else:  # pg:'all'
        u_context.set_scope_from_request(request, "person_scope")
        args["rule"] = "all"
    u_context.count = request.args.get("c", 100, type=int)

    with PersonReaderTx("read_tx", u_context) as service:
        res = service.get_person_search(args)

    return res, u_context


# @bp.route('/scene/persons', methods=['POST', 'GET'])
@bp.route("/scene/persons/all", methods=["GET"])
@login_required
@roles_accepted("guest", "research", "audit", "admin")
def show_persons():
    """Persons listings."""
    t0 = time.time()
    args = {"pg": "all"}
    #     years = request.args.get('years')
    #     if years: args['years'] = years
    fw = request.args.get("fw")
    if fw:
        args["fw"] = fw
    c = request.args.get("c")
    if c:
        args["c"] = c
    print(f"{request.method} All persons {args}")

    res, u_context = _do_get_persons(args)

    if Status.has_failed(res):
        flash(_("Data read failed."), "error")
        stk_logger(u_context, f"-> bp.scene.routes.show_persons FAILED")
    found = res.get("items", [])
    num_hidden = res.get("num_hidden", 0)
    hidden = f" hide={num_hidden}" if num_hidden > 0 else ""
    elapsed = time.time() - t0
    stk_logger(
        u_context,
        f"-> bp.scene.routes.show_persons" f" n={len(found)}/{hidden} e={elapsed:.3f}",
    )
    print(f"Got {len(found)} persons {num_hidden} hidden, fw={fw}")
    return render_template(
        "/scene/persons_list.html",
        persons=found,
        menuno=12,
        num_hidden=num_hidden,
        user_context=u_context,
        elapsed=elapsed,
    )


@bp.route("/scene/persons/search", methods=["GET", "POST"])
@login_required
@roles_accepted("guest", "research", "audit", "admin")
def show_person_search():
    """Persons search page."""
    t0 = time.time()
    args = {"pg": "search"}
    rq = request.args if request.method == "GET" else request.form
    rule = rq.get("rule")
    if rule:
        args["rule"] = rule
    key = rq.get("key")
    if key:
        args["key"] = key

    res, u_context = _do_get_persons(args)
    print(f"show_person_search {request.method} "
          f"{u_context.state} {u_context.material} Persons {args} ")
    if Status.has_failed(res, strict=False):
        flash(f'{res.get("statustext","error")}', "error")

    found = res.get("items", [])
    num_hidden = res.get("num_hidden", 0)
    hidden = f" hide={num_hidden}" if num_hidden > 0 else ""
    status = res["status"]
    elapsed = time.time() - t0
    stk_logger(
        u_context,
        f"-> bp.scene.routes.show_person_search/{rule}"
        f" n={len(found)}{hidden} e={elapsed:.3f}",
    )
    print(
        f"Got {len(found)} persons {num_hidden} hidden, {rule}={key}, status={status}"
    )

    surnamestats = []
    placenamestats = []
    if args.get("rule") is None:
        # Start search page: show name clouds
        minfont = 6
        maxfont = 20

        # Most common surnames cloud
        with PersonReader("read", u_context) as service:
            surnamestats = service.get_surname_list(47)
            # {name, count, uuid}
            for i, stat in enumerate(surnamestats):
                stat["order"] = i
                stat["fontsize"] = maxfont - i * (maxfont - minfont) / len(surnamestats)
            surnamestats.sort(key=itemgetter("surname"))

        # Most common place names cloud
        with PlaceReader("read", u_context) as service:
            placenamestats = service.get_placename_list(40)
            # {name, count, uuid}
            for i, stat in enumerate(placenamestats):
                stat["order"] = i
                stat["fontsize"] = maxfont - i * (maxfont - minfont) / len(
                    placenamestats
                )
            placenamestats.sort(key=itemgetter("placename"))

    return render_template(
        "/scene/persons_search.html",
        menuno=0,
        persons=found,
        user_context=u_context,
        num_hidden=num_hidden,
        rule=rule,
        key=key,
        status=status,
        surnamestats=surnamestats,
        placenamestats=placenamestats,
        elapsed=time.time() - t0,
    )


# -------------------------- Menu 12 Persons by user ---------------------------


@bp.route("/scene/person", methods=["GET"])
#     @login_required
@roles_accepted("guest", "research", "audit", "admin")
def show_person(uuid=None, fanchart=False):
    """One Person with all connected nodes - NEW version 3.

    Arguments:
    - uuid=     persons uuid
    - fanchart= by default family details shown, fanchart navigation uses this
    """
    t0 = time.time()
    uuid = request.args.get("uuid", uuid)
    fanchart_shown = request.args.get("fanchart", fanchart)
    dbg = request.args.get("debug", None)
    u_context = UserContext(user_session, current_user, request)

    with PersonReaderTx("read_tx", u_context) as service:
        result = service.get_person_data(uuid)

    # result {'person':PersonBl, 'objs':{uniq_id:obj}, 'jscode':str, 'root':{root_type,root_user,batch_id}}
    if Status.has_failed(result):
        flash(f'{result.get("statustext","error")}', "error")
        person = None
        objs = []
        jscode = ""
        print(f"# No Person found!")
    else:
        person = result.get("person")
        objs = result.get("objs", [])
        print(f"# Person with {len(objs)} objects")
        jscode = result.get("jscode", "")
        # Batch or Audit node data like {'root_type', 'root_user', 'id'}
        person.root = result.get("root")

    stk_logger(u_context, f"-> bp.scene.routes.show_person n={len(objs)}")

    last_year_allowed = datetime.now().year - shareds.PRIVACY_LIMIT
    may_edit = current_user.has_role("audit")  # or current_user.has_role('admin')
    # may_edit = 0
    return render_template(
        "/scene/person.html",
        person=person,
        obj=objs,
        jscode=jscode,
        menuno=12,
        debug=dbg,
        last_year_allowed=last_year_allowed,
        elapsed=time.time() - t0,
        user_context=u_context,
        may_edit=may_edit,
        fanchart_shown=fanchart_shown,
    )


@bp.route("/scene/person_famtree_hx", methods=["GET"])
#     @login_required
@roles_accepted("guest", "research", "audit", "admin")
def show_person_family_tree_hx(uuid=None):
    """
    Content of the selected tab for the families section: family details.
    """
    uuid = request.args.get("uuid", uuid)
    u_context = UserContext(user_session, current_user, request)

    with PersonReaderTx("read_tx", u_context) as service:
        result = service.get_person_data(uuid)

    # result {'person':PersonBl, 'objs':{uniq_id:obj}, 'jscode':str, 'root':{root_type,root_user,batch_id}}
    if Status.has_failed(result):
        flash(f'{result.get("statustext","error")}', "error")
    person = result.get("person")
    objs = result.get("objs", [])
    print(f"# Person with {len(objs)} objects")
    jscode = result.get("jscode", "")
    root = result.get("root")

    stk_logger(u_context, f"-> bp.scene.routes.show_person n={len(objs)}")

    last_year_allowed = datetime.now().year - shareds.PRIVACY_LIMIT
    may_edit = current_user.has_role("audit")  # or current_user.has_role('admin')
    return render_template(
        "/scene/person_famtree_hx.html",
        person=person,
        obj=objs,
        jscode=jscode,
        menuno=12,
        root=root,
        last_year_allowed=last_year_allowed,
        user_context=u_context,
        may_edit=may_edit,
    )


@bp.route("/scene/person_fanchart_hx", methods=["GET"])
#     @login_required
@roles_accepted("guest", "research", "audit", "admin")
def show_person_fanchart_hx(uuid=None):
    """
    Content of the selected tab for the families section: fanchart.
    """
    t0 = time.time()
    uuid = request.args.get("uuid", uuid)
    u_context = UserContext(user_session, current_user, request)

    with PersonReaderTx("read_tx", u_context) as service:
        result = service.get_person_data(uuid)

    # result {'person':PersonBl, 'objs':{uniq_id:obj}, 'jscode':str, 'root':{root_type,root_user,batch_id}}
    if Status.has_failed(result):
        flash(f'{result.get("statustext","error")}', "error")
    person = result.get("person")

    fanchart = FanChart().get(uuid)
    n = len(fanchart.get("children", []))
    t1 = time.time() - t0
    stk_logger(u_context, f"-> show_person_fanchart_hx n={n} e={t1:.3f}")
    return render_template(
        "/scene/person_fanchart_hx.html",
        person=person,
        fanchart_data=json.dumps(fanchart),
    )


@bp.route("/scene/nametypes/<uniq_id>/<typename>", methods=["GET"])
@roles_accepted("audit")
def get_person_nametypes(uniq_id, typename):
    s = f"""
        <select name='nametype' 
            id='name_{uniq_id}'
            hx-put='changetype/{uniq_id}' 
            hx-target='#msg_{uniq_id}' 
            hx-swap='innerHTML settle:1s'>
    """
    found = False
    for t in ["Birth Name", "Married Name", "Also Known As", "Unknown"]:
        s += f"\n    <option value='{t}'"
        if typename == t:
            s += " selected"
            found = True
        s += ">" + _(t) + "</option>"
    if not found:
        s += f"\n    <option value='{typename}' selected>" + _(typename)
    s += "\n</select>"
    s += f"<span class='msg' id='msg_{uniq_id}'></span>"
    return s


@bp.route("/scene/changetype/<uniq_id>", methods=["PUT"])
@roles_accepted("audit")
def person_name_changetype(uniq_id):
    try:
        nametype_list = request.form.getlist("nametype")
        uid_list = request.form.getlist("order")
        index = uid_list.index(uniq_id)
        nametype = nametype_list[index]
        u_context = UserContext(user_session, current_user, request)

        with PersonWriter("simple", u_context) as service:
            service.set_name_type(int(uniq_id), nametype)
        return _("type changed")  # will be displayed in <span class='msg' ...>
    except:
        return _("type change FAILED")  # will be displayed in <span class='msg' ...>


@bp.route("/scene/get_person_names/<uuid>", methods=["PUT"])
@roles_accepted("guest", "research", "audit", "admin")
def get_person_names(uuid):
    u_context = UserContext(user_session, current_user, request)

    args = {}
    with PersonReader("read", u_context) as service:
        result = service.get_person_data(uuid, args)

    if Status.has_failed(result):
        flash(f'{result.get("statustext","error")}', "error")
    person = result.get("person")
    objs = result.get("objs", [])
    stk_logger(u_context, f"-> bp.scene.routes.set_primary_name")
    may_edit = current_user.has_role("audit") or current_user.has_role("admin")
    return render_template(
        "/scene/person_names.html", person=person, obj=objs, may_edit=may_edit
    )


@bp.route("/scene/get_person_primary_name/<uuid>", methods=["PUT"])
@roles_accepted("guest", "research", "audit", "admin")
def get_person_primary_name(uuid):
    u_context = UserContext(user_session, current_user, request)

    with PersonReaderTx("read_tx", u_context) as service:
        result = service.get_person_data(uuid)

    if Status.has_failed(result):
        flash(f'{result.get("statustext","error")}', "error")
    person = result.get("person")
    stk_logger(u_context, f"-> bp.scene.routes.get_person_primary_name")
    return render_template("/scene/person_name.html", person=person)


@bp.route("/scene/set_primary_name/<uuid>/<int:old_order>", methods=["PUT"])
@roles_accepted("audit", "admin")
def set_primary_name(uuid, old_order):
    u_context = UserContext(user_session, current_user, request)

    # writeservice = get_dataservice("update")
    with PersonWriter("update", u_context) as service:
        service.set_primary_name(uuid, old_order)
    return get_person_names(uuid)


@bp.route("/scene/sort_names", methods=["PUT"])
@roles_accepted("audit", "admin")
def sort_names():
    uuid = request.form.get("uuid")
    uid_list = request.form.getlist("order")
    uid_list = [int(uid) for uid in uid_list]
    u_context = UserContext(user_session, current_user, request)

    # writeservice = get_dataservice("update")
    with PersonWriter("simple", u_context) as service:
        service.set_name_orders(uid_list)
    return get_person_primary_name(uuid)


# @bp.route('/scene/event/<int:uniq_id>')
@bp.route("/older/event/uuid=<string:uuid>")
@login_required
@roles_accepted("guest", "research", "audit", "admin")
def obsolete_show_event_v1(uuid):
    """Event page with accompanied persons and families.

    Derived from bp.obsolete_tools.routes.show_baptism_data()
    """
    u_context = UserContext(user_session, current_user, request)

    with EventReader("read", u_context) as service:
        # reader = EventReader(readservice, u_context)
        res = service.get_event_data(uuid)

    status = res.get("status")
    if status != Status.OK:
        flash(f'{_("Event not found")}: {res.get("statustext")}', "error")
    event = res.get("event", None)
    members = res.get("members", [])

    stk_logger(u_context, f"-> bp.scene.routes.show_event_page n={len(members)}")
    return render_template("/scene/event_htmx.html", event=event, participants=members)


@bp.route("/scene/edit_event/uuid=<string:uuid>")
@login_required
@roles_accepted("guest", "research", "audit", "admin")
def edit_event(uuid):
    u_context = UserContext(user_session, current_user, request)

    with EventReader("read", u_context) as service:
        # datastore = EventReader(readservice, u_context)
        print(f"#> bp.scene.routes.edit_event: with {service}")
        res = service.get_event_data(uuid, {})

    status = res.get("status")
    if status != Status.OK:
        flash(f'{_("Event not found")}: {res.get("statustext")}', "error")
    event = res.get("event", None)
    members = res.get("members", [])

    stk_logger(u_context, f"-> bp.scene.routes.show_event_page n={len(members)}")
    return render_template("/scene/edit_event.html", event=event, participants=members)


@bp.route("/scene/event/uuid=<string:uuid>")
@login_required
@roles_accepted("guest", "research", "audit", "admin")
def show_event_vue(uuid):
    """ Show Event page template which marshals data by Vue. """
    u_context = UserContext(user_session, current_user, request)
    return render_template("/scene/event_vue.html", uuid=uuid, user_context=u_context)


@bp.route("/scene/json/event", methods=["POST", "GET"])
@login_required
@roles_accepted("guest", "research", "audit", "admin")
def json_get_event():
    """Get Event page data."""
    t0 = time.time()
    try:
        args = request.args
        if args:
            print(f"got request args: {args}")
        else:
            args = json.loads(request.data)
            print(f"got request data: {args}")
        uuid = args.get("uuid")
        if not uuid:
            print("bp.scene.routes.json_get_person_families: Missing uuid")
            return jsonify(
                {"records": [], "status": Status.ERROR, "statusText": "Missing uuid"}
            )

        u_context = UserContext(user_session, current_user, request)
        with EventReader("read", u_context) as service:
            # reader = EventReader(readservice, u_context)
            res = service.get_event_data(uuid, args)

        status = res.get("status")
        if status != Status.OK:
            flash(f'{_("Event not found")}: {res.get("statustext")}', "error")
        if status == Status.NOT_FOUND:
            return jsonify(
                {
                    "event": None,
                    "members": [],
                    "statusText": _("No event found"),
                    "status": status,
                }
            )
        elif status != Status.OK:
            return jsonify(
                {
                    "event": None,
                    "members": [],
                    "statusText": _("No event found"),
                    "status": status,
                }
            )
        # Event
        event = res.get("event", None)
        event.type_lang = jinja_filters.translate(event.type, "evt").title()
        # Event members
        members = res.get("members", [])
        for m in members:
            if m.label == "Person":
                m.href = "/scene/person?uuid=" + m.uuid
                m.names[0].type_lang = jinja_filters.translate(m.names[0].type, "nt")
            elif m.label == "Family":
                m.href = "/scene/family?uuid=" + m.uuid
            m.role_lang = jinja_filters.translate(m.role, "role") if m.role else ""
        # Actually there is one place and one pl.uppers
        places = res.get("places", [])
        for pl in places:
            pl.href = "/scene/location/uuid=" + pl.uuid
            pl.type_lang = jinja_filters.translate(pl.type, "lt").title()
            for up in pl.uppers:
                up.href = "/scene/location/uuid=" + up.uuid
                up.type_lang = jinja_filters.translate(up.type, "lt_in").title()
        # Event notes
        notes = res.get("notes", [])
        # Medias
        medias = res.get("medias", [])
        for m in medias:
            m.href = "/scene/media?uuid=" + m.uuid

        res_dict = {
            "event": event,
            "members": members,
            "notes": notes,
            "places": places,
            "medias": medias,
            "allow_edit": u_context.allow_edit,
            "translations": {"myself": _("Self")},
        }
        response = StkEncoder.jsonify(res_dict)
        # print(response)
        t1 = time.time() - t0
        stk_logger(
            u_context, f"-> bp.scene.routes.json_get_event n={len(members)} e={t1:.3f}"
        )
        return response

    except Exception as e:
        traceback.print_exc()
        return jsonify(
            {
                "records": [],
                "status": Status.ERROR,
                "member": uuid,
                "statusText": f"Failed {e.__class__.__name__}",
            }
        )


@bp.route("/scene/update/event", methods=["POST"])
@login_required
@roles_accepted("audit")
def json_update_event():
    """Update Event"""
    t0 = time.time()
    try:
        args = request.args
        if args:
            # print(f'got request args: {args}')
            pass
        else:
            args = json.loads(request.data)
            # print(f'got request data: {args}')
        uuid = args.get("uuid")
        u_context = UserContext(user_session, current_user, request)

        # writeservice = get_dataservice("update")
        with EventWriter("update", u_context) as service:
            rec = service.update_event(uuid, args)
        if rec.get("status") != Status.OK:
            return rec
        event = rec.get("item")
        statusText = rec.get("statusText", "")
        event.type_lang = jinja_filters.translate(event.type, "evt").title()
        res_dict = {"status": Status.OK, "event": event, "statusText": statusText}
        response = StkEncoder.jsonify(res_dict)
        # print(response)
        t1 = time.time() - t0
        stk_logger(u_context, f"-> bp.scene.routes.json_update_event e={t1:.3f}")
        return response
    except Exception as e:
        traceback.print_exc()
        return jsonify(
            {
                "records": [],
                "status": Status.ERROR,
                "member": uuid,
                "statusText": f"Failed: {e}",
            }
        )


# ------------------------------ Menu 3: Families --------------------------------


@bp.route("/scene/families")
@login_required
@roles_accepted("guest", "research", "audit", "admin")
def show_families():
    """List of Families for menu(3)"""
    print(f"--- {request}")
    print(f"--- {user_session}")
    # Set context by owner and the data selections
    u_context = UserContext(user_session, current_user, request)
    # Which range of data is shown
    u_context.set_scope_from_request(request, "person_scope")
    opt = request.args.get("o", "father", type=str)
    u_context.order = "man" if opt == "father" else "wife"
    u_context.count = request.args.get("c", 100, type=int)
    t0 = time.time()

    with FamilyReader("read", u_context) as service:
        # 'families' has Family objects
        families = service.get_families()

    stk_logger(u_context, f"-> bp.scene.routes.show_families/{opt} n={len(families)}")
    return render_template(
        "/scene/families.html",
        families=families,
        user_context=u_context,
        elapsed=time.time() - t0,
    )


@bp.route("/scene/family", methods=["GET"])
@login_required
@roles_accepted("guest", "research", "audit", "admin")
def show_family_page(uuid=None):
    """One Family."""
    uuid = request.args.get("uuid", uuid)
    if not uuid:
        return redirect(url_for("virhesivu", code=1, text="Missing Family key"))
    t0 = time.time()
    u_context = UserContext(user_session, current_user, request)

    with FamilyReader("read", u_context) as service:
        # reader = FamilyReader(readservice, u_context)
        res = service.get_family_data(uuid)

    stk_logger(u_context, "-> bp.scene.routes.show_family_page")
    status = res.get("status")
    if status != Status.OK:
        if status == Status.ERROR:
            flash(f'{res.get("statustext")}', "error")
        else:
            flash(f'{ _("This item is not available") }', "warning")

    return render_template(
        "/scene/family.html",
        menuno=3,
        family=res["item"],
        user_context=u_context,
        elapsed=time.time() - t0,
    )


@bp.route("/scene/json/families", methods=["POST", "GET"])
@login_required
@roles_accepted("guest", "research", "audit", "admin")
def json_get_person_families():
    """Get all families for a Person as json structure.

    The families are ordered by marriage time.
    """
    t0 = time.time()
    try:
        args = request.args
        if args:
            print(f"got request args: {args}")
        else:
            args = json.loads(request.data)
            print(f"got request data: {args}")
        uuid = args.get("uuid")
        if not uuid:
            print("bp.scene.routes.json_get_person_families: Missing uuid")
            return jsonify(
                {"records": [], "status": Status.ERROR, "statusText": "Missing uuid"}
            )

        u_context = UserContext(user_session, current_user, request)
        with FamilyReader("read", u_context) as service:
            # reader = FamilyReader(readservice, u_context)
            res = service.get_person_families(uuid)

        if res.get("status") == Status.NOT_FOUND:
            return jsonify(
                {
                    "member": uuid,
                    "records": [],
                    "statusText": _("No families"),
                    "status": Status.NOT_FOUND,
                }
            )

        items = res["items"]
        res_dict = {
            "records": items,
            "member": uuid,
            "statusText": f"Löytyi {len(items)} perhettä",
            "translations": {"family": _("Family"), "children": _("Children")},
        }
        response = StkEncoder.jsonify(res_dict)

        t1 = time.time() - t0
        stk_logger(
            u_context,
            f"-> bp.scene.routes.show_person_families_json n={len(items)} e={t1:.3f}",
        )
        # print(response)
        return response

    except Exception as e:
        traceback.print_exc()
        return jsonify(
            {
                "records": [],
                "status": Status.ERROR,
                "member": uuid,
                "statusText": f"Failed {e.__class__.__name__}",
            }
        )


# ------------------------------ Menu 4: Places --------------------------------


@bp.route("/scene/locations")
@login_required
@roles_accepted("guest", "research", "audit", "admin")
def show_places():
    """List of Places for menu(4)"""
    t0 = time.time()
    print(f"--- {request}")
    print(f"--- {user_session}")
    # Set context by owner and the data selections
    u_context = UserContext(user_session, current_user, request)
    # Which range of data is shown
    u_context.set_scope_from_request(request, "place_scope")
    u_context.count = request.args.get("c", 50, type=int)

    with PlaceReader("read", u_context) as service:
        # reader = PlaceReader(readservice, u_context)
        # The 'items' list has Place objects, which include also the lists of
        # nearest upper and lower Places as place[i].upper[] and place[i].lower[]
        res = service.get_place_list()

    if res["status"] == Status.NOT_FOUND:
        print(f'bp.scene.routes.show_places: {_("No places found")}')
    elif res["status"] != Status.OK:
        print(
            f'bp.scene.routes.show_places: {_("Could not get places")}: {res.get("statustext")}'
        )

    elapsed = time.time() - t0
    stk_logger(
        u_context,
        f"-> bp.scene.routes.show_places n={len(res.get('items'))} e={elapsed:.3f}",
    )
    return render_template(
        "/scene/places.html",
        places=res["items"],
        menuno=4,
        user_context=u_context,
        elapsed=elapsed,
    )


@bp.route("/scene/location/uuid=<locid>")
@login_required
@roles_accepted("guest", "research", "audit", "admin")
def show_place(locid):
    """Home page for a Place, shows events and place hierarchy."""
    t0 = time.time()
    u_context = UserContext(user_session, current_user, request)
    try:
        with PlaceReader("read", u_context) as service:
            # reader = PlaceReader(readservice, u_context)
            res = service.get_places_w_events(locid)

        if res["status"] == Status.NOT_FOUND:
            print(f'bp.scene.routes.show_place: {_("Place not found")}')
        elif res["status"] != Status.OK:
            print(
                f'bp.scene.routes.show_place: {_("Place not found")}: {res.get("statustext")}'
            )

    except KeyError as e:
        traceback.print_exc()
        return redirect(url_for("virhesivu", code=1, text=str(e)))

    cnt = len(res.get("events")) if res.get("events", False) else 0
    stk_logger(u_context, f"-> bp.scene.routes.show_place n={cnt}")
    return render_template(
        "/scene/place_events.html",
        place=res.get("place"),
        pl_hierarchy=res.get("hierarchy"),
        events=res.get("events"),
        user_context=u_context,
        elapsed=time.time() - t0,
    )


# ------------------------------ Menu 5: Sources --------------------------------


@bp.route("/scene/sources")
@bp.route("/scene/sources/<series>")
@login_required
@roles_accepted("guest", "research", "audit", "admin")
def show_sources(series=None):
    """Lähdeluettelon näyttäminen ruudulla for menu(5)

    Possible args example: ?years=1800-1899&series=birth
    - source years (#todo)
    - series, one of {"birth", "baptism", "wedding", "death", "move"}
    Missing series or years = all
    Theme may also be expressed in url path

    """
    print(f"--- {request}")
    print(f"--- {user_session}")
    t0 = time.time()
    # Set context by owner and the data selections
    u_context = UserContext(user_session, current_user, request)
    # Which range of data is shown
    u_context.set_scope_from_request(request, "source_scope")
    u_context.count = request.args.get("c", 100, type=int)

    with SourceReader("read", u_context) as service:
        if series:
            u_context.series = series
        # try:
        res = service.get_source_list()
        if res["status"] == Status.NOT_FOUND:
            print("bp.scene.routes.show_sources: No sources found")
        elif res["status"] != Status.OK:
            print(f'bp.scene.routes.show_sources: Error {res.get("statustext")}')
        # except KeyError as e:
        # return redirect(url_for('virhesivu', code=1, text=str(e)))

    series = u_context.series if u_context.series else "all"
    stk_logger(
        u_context, f"-> bp.scene.routes.show_sources/{series} n={len(res['items'])}"
    )
    return render_template(
        "/scene/sources.html",
        sources=res["items"],
        user_context=u_context,
        elapsed=time.time() - t0,
    )


@bp.route("/scene/source", methods=["GET"])
# @bp.route('/scene/source=<string:sourceid>')
@login_required
@roles_accepted("guest", "research", "audit", "admin")
def show_source_page(sourceid=None):
    """Home page for a Source with referring Event and Person data"""
    uuid = request.args.get("uuid", sourceid)
    if not uuid:
        return redirect(url_for("virhesivu", code=1, text="Missing Source key"))
    u_context = UserContext(user_session, current_user, request)
    try:
        with SourceReader("read", u_context) as service:
            res = service.get_source_with_references(uuid, u_context)

        if res["status"] == Status.NOT_FOUND:
            msg = res.get("statustext", _("No objects found"))
            flash(msg, "error")
        if res["status"] != Status.OK:
            flash(f'{res.get("statustext", _("error"))}', "error")

        stk_logger(
            u_context, f"-> bp.scene.routes.show_source_page n={len(res['citations'])}"
        )

    except KeyError as e:
        msg = f"bp.scene.routes.show_source_page: {e.__class__.__name__} {e}"
        flash(f'{ _("Program error")}', "error")
        logger.error(msg)

    #     for c in res['citations']:
    #         for i in c.citators:
    #             if i.id[0] == "F":  print(f'{c} – family {i} {i.clearname}')
    #             else:               print(f'{c} – person {i} {i.sortname}')
    return render_template(
        "/scene/source_events.html",
        source=res["item"],
        citations=res["citations"],
        user_context=u_context,
    )


# ------------------------------ Menu 6: Media --------------------------------


@bp.route("/scene/medias")
@login_required
@roles_accepted("guest", "research", "audit", "admin")
def show_medias():
    """List of Medias for menu(6)"""
    t0 = time.time()
    print(f"--- {request}")
    print(f"--- {user_session}")
    # Set context by owner and the data selections
    u_context = UserContext(user_session, current_user, request)
    # Which range of data is shown
    u_context.set_scope_from_request(request, "media_scope")
    u_context.count = 20

    with MediaReader("read", u_context) as service:
        res = service.read_my_media_list()

    if Status.has_failed(res, False):
        flash(f'{res.get("statustext","error")}', "error")
    medias = res.get("items", [])

    stk_logger(u_context, f"-> bp.scene.media.show_medias fw n={len(medias)}")
    return render_template(
        "/scene/medias.html",
        medias=medias,
        user_context=u_context,
        elapsed=time.time() - t0,
    )


@bp.route("/scene/media", methods=["GET"])
@login_required
@roles_accepted("guest", "research", "audit", "admin")
def show_media(uuid=None):
    """
    One Media
    """
    uuid = request.args.get("uuid", uuid)
    u_context = UserContext(user_session, current_user, request)
    with MediaReader("read", u_context) as service:
        res = service.get_one(uuid)

    status = res.get("status")
    if status != Status.OK:
        print(f'bp.scene.routes.show_media: error {status} {res.get("statustext")}')
        if status == Status.ERROR:
            flash(f'{res.get("statustext")}', "error")
        else:
            flash(f'{ _("This item is not available") }', "warning")

    medium = res.get("item", None)
    if medium:
        fullname, mimetype = media.get_fullname(medium.uuid)
        stk_logger(u_context, f"-> bp.scene.routes.show_media n={len(medium.ref)}")
    else:
        flash(f'{res.get("statustext","error")}', "error")
        fullname = None
        mimetype = None
    if mimetype == "application/pdf":
        size = 0
    else:
        size = media.get_image_size(fullname)

    return render_template(
        "/scene/media.html", media=medium, size=size, user_context=u_context, menuno=6
    )


# ----------- Access media file ---------------


@bp.route("/scene/media/<fname>")
@login_required
@roles_accepted("guest", "research", "audit", "admin")
def fetch_media(fname):
    """Fetch media file to display full screen.

    Example:
    http://127.0.0.1:5000/scene/media/kuva2?id=63995268bd2348aeb6c70b5259f6743f&crop=0,21,100,91&full=1

    Arguments:
        id    uuid of Media
        crop  pixel coordinates as "left,upper,right,lower" %
        full  "1" = show full size, "0" thumbnail size (default)
    """
    uuid = request.args.get("id")
    crop = request.args.get("crop")
    # show_thumb for cropped image only
    show_thumb = request.args.get("full", "0") == "0"
    fullname, mimetype = media.get_fullname(uuid)
    try:
        if crop:
            # crop dimensions are diescribed as % of width and height
            image = media.get_cropped_image(fullname, crop, show_thumb)
            logger.debug("-> bp.scene.routes.fetch_media cropped png")
            # Create a png image in memery and display it
            buffer = io.BytesIO()
            image.save(buffer, format="PNG")
            return Response(buffer.getvalue(), mimetype="image/png")
        else:
            logger.debug("-> bp.scene.routes.fetch_media full")
            return send_file(fullname, mimetype=mimetype)
    except FileNotFoundError:
        # Show default image
        ret = send_file(os.path.join("static", "image/noone.jpg"), mimetype=mimetype)
        logger.debug(f"-> bp.scene.routes.fetch_media none")
        return ret


@bp.route("/scene/thumbnail")
@login_required
@roles_accepted("guest", "research", "audit", "admin")
def fetch_thumbnail():
    """Fetch thumbnail file to display"""
    uuid = request.args.get("id")
    crop = request.args.get("crop")
    if crop == "None":
        crop = None
    thumb_mime = "image/jpg"
    thumbname = "(no file)"
    try:
        thumbname, cl = media.get_thumbname(uuid, crop)
        if cl == "jpg":
            ret = send_file(thumbname, mimetype=thumb_mime)
        elif cl == "pdf":
            ret = send_file(
                os.path.join("static", "image/a_pdf.png"), mimetype=thumb_mime
            )
        else:
            ret = send_file(
                os.path.join("static", "image/noone.jpg"), mimetype=thumb_mime
            )
        logger.debug(f"-> bp.scene.routes.fetch_thumbnail ok")
    except FileNotFoundError:
        # Show default image
        ret = send_file(os.path.join("static", "image/noone.jpg"), mimetype=thumb_mime)
        logger.debug(f"-> bp.scene.routes.fetch_thumbnail none")

    return ret


# ------------------------------ Menu 7: Comment --------------------------------


@bp.route("/scene/batch_comments")
@login_required
@roles_accepted("guest", "research", "audit", "admin")
def show_comments():
    """List of Comments for menu(7)"""
    t0 = time.time()
    print(f"--- {request}")
    print(f"--- {user_session}")
    # Set context by owner and the data selections
    u_context = UserContext(user_session, current_user, request)
    # Which range of data is shown
    u_context.set_scope_from_request(request, "comment_scope")
    u_context.count = 20

    with CommentReader("read", u_context) as service:
        res = service.read_my_comment_list()

    if Status.has_failed(res, False):
        flash(f'{res.get("statustext","error")}', "error")
    comments = res.get("items", [])

    stk_logger(u_context, f"-> bp.scene.comment.show_comments fw n={len(comments)}")
    return render_template(
        "/scene/comments.html",
        comments=comments,
        user_context=u_context,
        elapsed=time.time() - t0,
    )


# ----------- Access htmx components ---------------


@bp.route("/scene/comments")
@login_required
@roles_accepted("guest", "research", "audit", "admin")
def comments():
    """Page with comments and a field to add a new comment"""
    return render_template("/scene/comments/comments.html")


@bp.route("/scene/comments/comments_header")
@login_required
@roles_accepted("guest", "research", "audit", "admin")
def comments_header():
    """Comments header"""
    if "audit" in current_user.roles:
        return render_template("/scene/comments/comments_header.html")
    else:
        return ""


@bp.route("/scene/comments/fetch_comments")
@login_required
@roles_accepted("guest", "research", "audit", "admin")
def fetch_comments():
    """Fetch comments"""
    u_context = UserContext(user_session, current_user, request)
    uniq_id = int(request.args.get("uniq_id"))
    # uuid = request.args.get("uuid")
    if request.args.get("start"):
        start = float(request.args.get("start"))
    else:
        start = datetime.now().timestamp()

    query = """
        match (p) -[:COMMENT] -> (c:Comment)
            where id(p) = $uniq_id and c.timestamp <= $start
        return c as comment order by c.timestamp desc limit 5
    """
    result = shareds.driver.session().run(query, uniq_id=uniq_id, start=start)
    comments = []
    last_timestamp = None
    for record in result:
        node = record["comment"]
        c = SimpleNamespace()
        c.user = node["user"]
        c.comment_text = node["text"]
        c.timestr = node["timestr"]
        c.timestamp = node["timestamp"]
        comments.append(c)
        last_timestamp = c.timestamp
    if last_timestamp is None:
        return "<span id='no_comments'>" + _("No previous comments") + "</span>"
    else:
        stk_logger(u_context, f"-> bp.scene.routes.fetch_comments n={len(comments)}")
        return render_template(
            "/scene/comments/fetch_comments.html",
            comments=comments[0:4],
            last_timestamp=last_timestamp,
            there_is_more=len(comments) > 4,
        )


@bp.route("/scene/comments/add_comment", methods=["post"])
@login_required
@roles_accepted("guest", "research", "audit", "admin")
def add_comment():
    """Add a comment"""
    u_context = UserContext(user_session, current_user, request)
    # uuid = request.form.get("uuid")
    uniq_id = int(request.form.get("uniq_id"))
    comment_text = request.form.get("comment_text")
    if comment_text.strip() == "":
        return ""
    user = current_user.username
    timestamp = time.time()
    timestr = util.format_timestamp(timestamp)
    res = (
        shareds.driver.session()
        .run(
            """
        match (p) where id(p) = $uniq_id 
        create (p) -[:COMMENT] -> 
            (c:Comment{user:$user,text:$text,timestamp:$timestamp,timestr:$timestr})
        return c
        """,
            uniq_id=uniq_id,
            user=user,
            text=comment_text,
            timestamp=timestamp,
            timestr=timestr,
        )
        .single()
    )
    if res:
        stk_logger(u_context, "-> bp.scene.routes.add_comment")
        return render_template(
            "/scene/comments/add_comment.html",
            timestamp=timestr,
            user=user,
            comment_text=comment_text,
        )
    else:
        return ""
