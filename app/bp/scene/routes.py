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
# blacked 7.11.2021/JMä
import io
import os
import traceback
import json
import time
from datetime import datetime
from operator import itemgetter

# from types import SimpleNamespace

import logging

logger = logging.getLogger("stkserver")

from flask import send_file, Response, jsonify, render_template
from flask import request, redirect, url_for, flash
from flask import session as session
from flask_security import current_user, login_required, roles_accepted
from flask_babelex import _

import shareds
from . import bp
from bl.base import Status, StkEncoder
from bl.material import Material
from bl.place import PlaceReader
from bl.source import SourceReader
from bl.family import FamilyReader
from bl.event import EventReader, EventWriter
from bl.note import NoteReader
from bl.person import PersonReader, PersonWriter
from bl.person_reader import PersonReaderTx
from bl.media import MediaReader
from bl.comment import Comment, CommentReader, CommentsUpdater
from bp.graph.models.fanchart import FanChart
from ui.context import UserContext
from ui import jinja_filters
from ui.util import error_print, stk_logger
from models import mediafile

calendars = [_("Julian"), _("Hebrew")]  # just for translations


# ---------------------- Enter with material select ---------------------------


@bp.route("/scene/material/<breed>", methods=["GET", "POST"])
@login_required
@roles_accepted("guest", "research", "audit", "admin")
def material_select(breed):  # set_scope=False, batch_id="", material=None):
    """Select material for browsing and go to Search page.
    
       Parameters for database access and displaying current material
       - breed="common": Browsing Accepted materials (= a collection of multiple batches)
         - input: material and state – no uniq_id
       - breed="batch": Browsing other material types:
         - input: batch id
         - figure from database: material and state
    """
    # 1. User and data context from session and current_user
    ret = Material.set_session_material(session, request, breed, current_user.username)
    # return f"<p>TODO {ret.get('args')}</p><p><a href='/'>Alkuun</a></p>"
    if Status.has_failed(ret):
        flash(
            f"{ _('Opening material failed: ') }: { _(ret.get('statustext')) }",
            "error",
        )
        return redirect("/")

    return redirect(url_for("scene.show_person_search"))


# ------------------------- Menu 1: Material search ------------------------------


def _note_item_format(rec, searchtext, min_length=100):
    """ Display an excerpt from Note.text that is at least this long
    """
    import re

    def generate_choices(q):
        choices = []
        for i, _c in enumerate(q):
            choice = fr"{q[0:i]}\w{q[i:]}"  # add any character
            choices.append(choice)
            choice = fr"{q[0:i]}\w{q[i+1:]}"  # replace any character
            choices.append(choice)
            choice = fr"{q[0:i]}{q[i+1:]}"  # remove any character
            choices.append(choice)
        return choices

    # print(rec)
    note = rec.get("note")
    # id = note.get('id')
    text = note.get("text")
    labels = rec.get("labels")
    startpos = -1
    if searchtext.startswith("'") and searchtext.endswith("'"):
        searchtext = searchtext[1:-1]
    if searchtext.startswith('"') and searchtext.endswith('"'):
        searchwords = [searchtext[1:-1]]
    else:
        searchwords = [searchtext] + searchtext.split()
    for wordnum, searchword in enumerate(searchwords):
        if searchword.endswith("~"):
            searchword = searchword[:-1]
            choices = generate_choices(searchword)
            choices = [searchword] + choices
            print(choices)
            regextext = "(" + "|".join(choices) + ")"
        else:
            regextext = searchword
            regextext = regextext.replace("\\", r"\\")
            regextext = regextext.replace("(", r"\(").replace(")", r"\)")
            regextext = regextext.replace("[", r"\[").replace("]", r"\]")
            regextext = regextext.replace(
                "*", r"\w*?"
            )  # asterisk means word characters only, ? indicate non-greedy search

        regex = fr"\W({regextext})\W"

        m = re.search(
            regex, f" {text.lower()} "
        )  # add delimiters to start and end (will match \W)
        if m:
            # print(m)
            # print(m.start(1),m.end(1),len(text))
            startpos = m.start(1) - 1
            endpos = m.end(1) - 1
        if startpos != -1:
            # display at least min_length/2 characters before and after the match
            xstart = max(0, startpos - min_length // 2)
            xend = endpos + min_length // 2

            # if needed, increase the size up to min_length characters
            if xstart == 0 and xend < xstart + min_length:
                xend = xstart + min_length
            if xend >= len(text) and xstart > len(text) - min_length:
                xstart = max(0, len(text) - min_length)

            # break at space if possible
            xstart = text.rfind(" ", 0, xstart) + 1
            xend1 = text.find(" ", xend)
            if xend1 != -1:
                xend = xend1

            excerpt = text[xstart:xend]
            excerpt = (
                excerpt[0 : endpos - xstart] + "</match>" + excerpt[endpos - xstart :]
            )
            excerpt = (
                excerpt[0 : startpos - xstart]
                + "<match>"
                + excerpt[startpos - xstart :]
            )
            if xstart > 0:
                excerpt = "..." + excerpt
            if xend < len(text) - 1:
                excerpt = excerpt + "..."
            break  # found a match
        else:
            excerpt = text[0:min_length]
            if wordnum < len(searchwords) - 1:
                continue  # try again except for last word
    referrers = rec.get("referrers")
    score = rec.get("score")
    return dict(
        note=note,
        id=id,
        labels=labels,
        referrers=referrers,
        score=score,
        # x=dict(x),
        excerpt=repr(excerpt)[1:-1],
    )


def _note_search(args):
    """ Free text search by Note.text.
    """
    print(args)
    u_context = UserContext()
    u_context.count = request.args.get("c", 100, type=int)
    searchtext = args["key"].lower()
    displaylist = []

    try:
        with NoteReader("read_tx", u_context) as service:
            res = service.note_search(args)
            for item in res["items"]:
                # print("item", item)
                # note = item[0]
                # x = item[1]
                displaylist.append(_note_item_format(item, searchtext))

        # from pprint import  pprint
        # pprint(displaylist[0:5])
    except Exception as e:
        traceback.print_exc()
        flash(str(e))
        stk_logger(u_context, f"-> bp.scene.routes._note_search FAILED")

    return render_template(
        "/scene/persons_search.html",
        menuno=0,
        items=displaylist,
        user_context=u_context,
        rule="notetext",
        key=searchtext,
    )


def _do_get_persons(u_context, args):
    """Execute persons list query by arguments and optionally set material type.

        Search form
            GET    /search                                    --> args={pg:search,rule:start}
        Search by refname
            GET    /search?rule=ref,key=<str>                 --> args={pg:search,rule:ref,key:str}
        Search form
            POST   /search                                    --> args={pg:search,rule:start}
        Search by name starting or years
            POST   /search rule=<rule>,key=<str>              --> args={pg:search,rule:ref,key:str}

        Persons, current list page
            GET    /all                                       --> args={pg:all}
        Persons, forward
            GET    /all?fw=<sortname>&c=<count>               --> args={pg:all,fw:sortname,c:count}

    #     Persons, by years range
    #         GET    /all?years=<y1-y2>                         --> args={pg:all,years:y1_y2}
    #     Persons fw,years
    #         GET    /all?years=<y1-y2>&fw=<sortname>&c=<count> --> args={pg:all,fw:sortname,c:count,years:y1_y2}
    #     Search by years range
    #         POST   /search years=<y1-y2>                      --> args={pg:search,years:y1_y2}
    #     Search by name & years
    #         POST   /search rule=<rule>,key=<str>,years=<y1-y2> --> args={pg:search,rule:ref,key:str,years:y1_y2}
    """
    if args.get("pg") == "search":
        # No scope
        # u_context.set_scope_from_request()
        if args.get("rule", "init") == "init" or args.get("key", "") == "":
            # Initializing this batch.
            return {
                "rule": "init",
                "status": Status.NOT_STARTED,
                # "u_context": u_context,
            }
    else:  # pg:'all'
        # u_context.set_scope_from_request("person_scope")
        args["rule"] = "all"
    # request_args = UserContext.get_request_args()
    u_context.set_scope("person_scope")
    u_context.count = int(u_context.get("c", 100))

    with PersonReaderTx("read_tx", u_context) as service:
        res = service.get_person_search(args)
        # for i in res.get("items"): print(f"_do_get_persons: @{i.user} {i.sortname}")

    # res["u_context"] = u_context
    return res


# @bp.route('/scene/persons', methods=['POST', 'GET'])
@bp.route("/scene/persons/all", methods=["GET"])
@login_required
@roles_accepted("guest", "research", "audit", "admin")
def show_persons():
    """Persons listings."""
    t0 = time.time()
    u_context = UserContext()
    # Request may include fw, bw, count or years
    run_args = u_context.set_scope_from_request("person_scope")
    run_args["pg"] = "all"
    # years = request.args.get('years')
    # if years: run_args['years'] = years
    # fw = request.args.get("fw")
    # if fw: run_args["fw"] = fw
    # c = request.args.get("c")
    # if c: run_args["c"] = c

    # 1. User and data context from session and current_user
    print(f"{request.method} All persons {run_args}")

    res = _do_get_persons(u_context, run_args)
    # u_context = res.get("u_context")

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
    print(f"Got {len(found)} persons {num_hidden} hidden, fw={u_context.first}")
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
def show_person_search():  # (set_scope=None, batch_id=None):
    """
    Start material browsing with Persons search page.

    Uses the material defined in SecureCookieSession session
    """
    t0 = time.time()
    try:

        # 1. User and data context from session and current_user
        u_context = UserContext()
        run_args = {"pg": "search"}
        rule = u_context.get("rule", "init")
        run_args["rule"] = rule
        key = u_context.get("key", "")
        if key:
            run_args["key"] = key

        # Breed from routes.material_select:
        new_breed = session.pop("breed", "")  # Remove from session
        if new_breed:
            # Select another material (batch or common data)
            u_context.breed = new_breed
            # ['batch', 'Candidate', 'Family Tree', '2021-10-20.004']
            _current_context, new_state, new_material, new_batch_id = (
                u_context.material.get_current()
            )
            run_args["set_scope"] = True
            run_args["state"] = new_state
            run_args["material"] = new_material
            run_args["batch_id"] = new_batch_id

        logger.debug(
            "#(1)bp.scene.routes.show_person_search: "
            f"{request.method} {u_context.material.get_request_args(session, request)} => "
            f'({session["current_context"]!r}, {session["state"]!r}, '
            f'{session["material_type"]!r}, {session["batch_id"]!r})'
        )

        # ------ Free text search by Note texts
        if rule == "notetext":
            return _note_search(run_args)

        # ------ Person search by names or years
        # 'person_scope': ('Manninen#Matti#', '> end') from request
        new_args = u_context.set_scope_from_request("person_scope")
        run_args.update(new_args)

        res = _do_get_persons(u_context, run_args)
        logger.info(
            f"#(2)bp.scene.routes.show_person_search: "
            f"{ u_context.material.get_current() } Persons with {run_args} "
        )
        if Status.has_failed(res, strict=False):
            flash(f'{res.get("statustext","error")}', "error")

        found = res.get("items", [])
        num_hidden = res.get("num_hidden", 0)
        hidden_txt = f" hide={num_hidden}" if num_hidden > 0 else ""
        status = res["status"]
        elapsed = time.time() - t0
        stk_logger(
            u_context,
            "-> bp.scene.routes.show_person_search/"
            f"{rule} n={len(found)}{hidden_txt} e={elapsed:.3f}",
        )
        print(
            f"bp.scene.routes.show_person_search: Got {len(found)} persons "
            f"{num_hidden} hidden, {rule}={key}, status={status}"
        )

        surnamestats = []
        placenamestats = []
        if rule == "init":
            # Start material search page:
            #    - show name clouds and
            #    - store material type to session.material_type
            minfont = 6
            maxfont = 20

            # Most common surnames cloud
            with PersonReader("read", u_context) as service:
                surnamestats = service.get_surname_list(47)
                # {name, count, uuid}
                for i, stat in enumerate(surnamestats):
                    stat["order"] = i
                    stat["fontsize"] = maxfont - i * (maxfont - minfont) / len(
                        surnamestats
                    )
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

    except Exception as e:
        error_print("show_person_search", e)
        # Set default values
        found = []
        num_hidden = 0
        status = ""
        rule = ""
        surnamestats = []
        placenamestats = []
        flash(str(e))

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
    u_context = UserContext()

    with PersonReaderTx("read_tx", u_context) as service:
        result = service.get_person_data(uuid)

    # result {'person':PersonBl, 'objs':{uniq_id:obj}, 'jscode':str, 'root':{material,root_user,batch_id}}
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
        # Batch or Audit node data like {'material', 'root_user', 'id'}
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


@bp.route("/scene/hx-person/famtree", methods=["GET"])
#     @login_required
@roles_accepted("guest", "research", "audit", "admin")
def show_person_family_tree_hx(uuid=None):
    """
    Htmx-component for displaying selected relatives tab: the families details.
    """
    uuid = request.args.get("uuid", uuid)
    u_context = UserContext()

    with PersonReaderTx("read_tx", u_context) as service:
        result = service.get_person_data(uuid)

    # result {'person':PersonBl, 'objs':{uniq_id:obj}, 'jscode':str, 'root':{material,root_user,batch_id}}
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
        "/scene/hx-person/famtree.html",
        person=person,
        obj=objs,
        jscode=jscode,
        menuno=12,
        root=root,
        last_year_allowed=last_year_allowed,
        user_context=u_context,
        may_edit=may_edit,
    )


@bp.route("/scene/hx-person/fanchart", methods=["GET"])
#     @login_required
@roles_accepted("guest", "research", "audit", "admin")
def show_person_fanchart_hx(uuid=None):
    """
    Htmx-component for displaying selected relatives tab: fanchart.
    """
    t0 = time.time()
    uuid = request.args.get("uuid", uuid)
    u_context = UserContext()

    with PersonReaderTx("read_tx", u_context) as service:
        result = service.get_person_data(uuid)

    # result {'person':PersonBl, 'objs':{uniq_id:obj}, 'jscode':str, 'root':{material,root_user,batch_id}}
    if Status.has_failed(result):
        flash(f'{result.get("statustext","error")}', "error")
    person = result.get("person")

    fanchart = FanChart().get(uuid)
    n = len(fanchart.get("children", []))
    t1 = time.time() - t0
    stk_logger(u_context, f"-> show_person_fanchart_hx n={n} e={t1:.3f}")
    return render_template(
        "/scene/hx-person/fanchart.html",
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
        u_context = UserContext()

        with PersonWriter("simple", u_context) as service:
            service.set_name_type(int(uniq_id), nametype)
        return _("type changed")  # will be displayed in <span class='msg' ...>
    except:
        return _("type change FAILED")  # will be displayed in <span class='msg' ...>


@bp.route("/scene/get_person_names/<uuid>", methods=["PUT"])
@roles_accepted("guest", "research", "audit", "admin")
def get_person_names(uuid):
    u_context = UserContext()

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
    u_context = UserContext()

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
    u_context = UserContext()

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
    u_context = UserContext()

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
    u_context = UserContext()

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
    u_context = UserContext()

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
    u_context = UserContext()
    return render_template("/scene/event_vue.html", uuid=uuid, user_context=u_context)


@bp.route("/scene/json/event", methods=["POST", "GET"])
@login_required
@roles_accepted("guest", "research", "audit", "admin")
def json_get_event():
    """Get Event page data."""
    t0 = time.time()
    u_context = UserContext()
    args = Material.get_request_args(session, request)
    try:
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
        u_context = UserContext()

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
    print(f"--- {session}")
    # Set context by owner and the data selections
    u_context = UserContext()
    # Which range of data is shown
    u_context.set_scope_from_request("person_scope")
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
    u_context = UserContext()

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

        u_context = UserContext()
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
    print(f"--- {session}")
    # Set context by owner and the data selections
    u_context = UserContext()
    # Which range of data is shown
    u_context.set_scope_from_request("place_scope")
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
    u_context = UserContext()
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
        "/scene/place.html",
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
    print(f"--- {session}")
    t0 = time.time()
    # Set context by owner and the data selections
    u_context = UserContext()
    # Which range of data is shown
    u_context.set_scope_from_request("source_scope")
    u_context.count = int(u_context.get("c", 100))
    u_context.series = series

    with SourceReader("read", u_context) as service:
        # if series: u_context.series = series
        res = service.get_source_list()
        if res["status"] == Status.NOT_FOUND:
            print("bp.scene.routes.show_sources: No sources found")
        elif res["status"] != Status.OK:
            print(f'bp.scene.routes.show_sources: Error {res.get("statustext")}')

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
    u_context = UserContext()
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
    print(f"--- {session}")
    # Set context by owner and the data selections
    u_context = UserContext()
    # Which range of data is shown
    u_context.set_scope_from_request("media_scope")
    u_context.count = 20

    with MediaReader("read", u_context) as service:
        res = service.read_my_media_list()

    if Status.has_failed(res, False):
        flash(f'{res.get("statustext","error")}', "error")
    medias = res.get("items", [])

    stk_logger(u_context, f"-> bp.scene.routes.show_medias fw n={len(medias)}")
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
    u_context = UserContext()
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
        fullname, mimetype = mediafile.get_fullname(medium.uuid)
        stk_logger(u_context, f"-> bp.scene.routes.show_media n={len(medium.ref)}")
    else:
        flash(f'{res.get("statustext","error")}', "error")
        fullname = None
        mimetype = None
    if mimetype == "application/pdf":
        size = 0
    else:
        size = mediafile.get_image_size(fullname)

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
    fullname, mimetype = mediafile.get_fullname(uuid)
    try:
        if crop:
            # crop dimensions are diescribed as % of width and height
            image = mediafile.get_cropped_image(fullname, crop, show_thumb)
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
        thumbname, cl = mediafile.get_thumbname(uuid, crop)
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
        # logger.debug(f"-> bp.scene.routes.fetch_thumbnail ok")
    except FileNotFoundError:
        # Show default image
        ret = send_file(os.path.join("static", "image/noone.jpg"), mimetype=thumb_mime)
        logger.debug(f"bp.scene.routes.fetch_thumbnail none")
    except Exception as e:
        error_print("fetch_thumbnail", e)
        return redirect(url_for("entry"))

    return ret


# ------------------------------ Menu 7: Comment --------------------------------


@bp.route("/scene/topics")
@login_required
@roles_accepted("guest", "research", "audit", "admin")
def show_topics():
    """List of Discussions for menu(7)"""
    t0 = time.time()
    print(f"--- {request}")
    print(f"--- {session}")
    # Set context by owner and the data selections
    u_context = UserContext()
    # Which range of data is shown
    u_context.set_scope_from_request("comment_scope")
    u_context.count = 20

    with CommentReader("read", u_context) as service:
        res = service.read_my_comment_list()

    if Status.has_failed(res, False):
        flash(f'{res.get("statustext","error")}', "error")
    comments = res.get("items", [])

    stk_logger(u_context, f"-> bp.scene.routes.show_topics n={len(comments)}")
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
    return render_template("/scene/hx-comment/comments.html")


@bp.route("/scene/hx-comment/comments_header")
@login_required
@roles_accepted("guest", "research", "audit", "admin")
def comments_header():
    """Discussions header"""
    if "audit" in current_user.roles:
        return render_template("/scene/hx-comment/comments_header.html")
    else:
        return ""


@bp.route("/scene/hx-comment/fetch_comments")
@login_required
@roles_accepted("guest", "research", "audit", "admin")
def fetch_comments():
    """Fetch topics and comments to given object """
    from pe.neo4j.cypher.cy_comment import CypherComment

    u_context = UserContext()
    uniq_id = int(request.args.get("uniq_id"))
    # uuid = request.args.get("uuid")
    if request.args.get("start"):
        start = float(request.args.get("start"))
    else:
        # Neo4j timestamp
        start = datetime.now().timestamp() * 1000.0

    try:
        result = shareds.driver.session().run(
            CypherComment.fetch_obj_comments, uniq_id=uniq_id, start=start
        )
        comments = []
        last_timestamp = None
        for record in result:
            node = record["comment"]
            c = Comment.from_node(node)
            c.user = record["commenter"]
            comments.append(c)
            last_timestamp = c.timestamp
        if last_timestamp is None:
            return "<span id='no_comments'>" + _("No previous comments") + "</span>"
        else:
            stk_logger(
                u_context, f"-> bp.scene.routes.fetch_comments n={len(comments)}"
            )
            return render_template(
                "/scene/hx-comment/fetch_comments.html",
                comments=comments[0:4],
                last_timestamp=last_timestamp,
                there_is_more=len(comments) > 4,
            )
    except Exception as e:
        error_print("fetch_comments", e, do_flash=False)
        return f"{ _('Sorry, operation failed') }: {e.__class__.__name__} {e}"


@bp.route("/scene/hx-comment/add_comment", methods=["post"])
@login_required
@roles_accepted("guest", "research", "audit", "admin")
def add_comment():
    """Add a comment"""

    u_context = UserContext()
    # uuid = request.form.get("uuid")
    uniq_id = int(request.form.get("uniq_id", 0))
    comment_text = request.form.get("comment_text")
    if comment_text.strip() == "":
        return ""
    user = current_user.username
    comment = None
    try:
        with CommentsUpdater("update") as comment_service:
            res = comment_service.add_comment(user, uniq_id, comment_text)
            if res:
                if Status.has_failed(res, strict=True):
                    flash(f'{res.get("statustext","error")}', "error")
                    return ""
                comment = res.get("comment")
            else:
                msg = f'{_("The operation failed due to error")}: {res.get("statustext","error")}'
                print("bp.scene.routes.add_comment" + msg)
                logger.error("bp.scene.routes.add_comment" + msg)
                flash(msg)
                return ""

    except Exception as e:
        error_print("add_comment", e, do_flash=False)
        return f"{ _('Sorry, operation failed') }: {e.__class__.__name__} {e}"

    stk_logger(u_context, "-> bp.scene.routes.add_comment")
    return render_template("/scene/hx-comment/add_comment.html", comment=comment)
