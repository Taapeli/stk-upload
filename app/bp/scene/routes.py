#   Isotammi Geneological Service for combining multiple researchers' results.
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

'''
Created on 12.8.2018

@author: jm
'''
import io
import os
import traceback
import json

import logging 
from operator import itemgetter
logger = logging.getLogger('stkserver')
import time
from datetime import datetime

import shareds
from flask import send_file, Response, jsonify
from flask import render_template, request, redirect, url_for, flash, session as user_session
from flask_security import current_user, login_required, roles_accepted
from flask_babelex import _

from . import bp
from bl.base import Status, StkEncoder
from bl.place import PlaceDataReader
from bl.source import SourceDataStore
from bl.family import FamilyReader
from bl.event import EventReader, EventWriter
from bl.person import PersonReader
from bl.media import MediaReader

from ui.user_context import UserContext
from ui import jinja_filters

from bp.scene.models import media
#from models.gen.family_combo import Family_combo
#from models.gen.source import Source
#from models.gen.obsolete_media import Media
from models.obsolete_datareader import obsolete_read_persons_with_events

# Select the read driver for current database
from pe.neo4j.readservice import Neo4jReadService
readservice = Neo4jReadService(shareds.driver)

from pe.neo4j.writeservice import Neo4jWriteService
writeservice = Neo4jWriteService(shareds.driver)


def stk_logger(context, msg:str):
    """ Emit logger info message with Use Case mark uc=<code> .
    """
    if not context:
        logger.info(msg)
        return
    uc = context.use_case()
    if (msg[:2] != '->') or (uc == ''):
        logger.info(msg)
        return
    logger.info(f'-> {msg[2:]} uc={uc}')
    return


# ------------------------- Menu 1: Person search ------------------------------

def _do_get_persons(args):
    ''' Execute persons list query by arguments.

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
    '''
    u_context = UserContext(user_session, current_user, request)
    if args.get('pg') == 'search':
        # No scope
        u_context.set_scope_from_request()
        if args.get('rule', 'start') == "start" or args.get('key', '') == "":
            return {'rule':'start', 'status':Status.NOT_STARTED}, u_context
    else: # pg:'all'
        u_context.set_scope_from_request(request, 'person_scope')
        args['rule'] = 'all'
    
    u_context.count = request.args.get('c', 100, type=int)
    reader = PersonReader(readservice, u_context)
    
    res = reader.get_person_search(args)

    #print(f'Query {args} produced {len(res["items"])} persons, where {res["num_hidden"]} hidden.')
#     if res.get('status') != Status.OK:
#         flash(f'{_("No persons found")}: {res.get("statustext")}','error')

    return res, u_context


#@bp.route('/scene/persons', methods=['POST', 'GET'])
@bp.route('/scene/persons/all', methods=['GET'])
@login_required
@roles_accepted('guest', 'research', 'audit', 'admin')
def show_persons():
    ''' Persons listings.
    '''
    t0 = time.time()
    args = {'pg':'all'}
#     years = request.args.get('years')
#     if years: args['years'] = years
    fw = request.args.get('fw')
    if fw:    args['fw'] = fw
    c = request.args.get('c')
    if c:     args['c'] = c
    print(f'{request.method} All persons {args}')

    res, u_context = _do_get_persons(args)

    found = res.get('items',[])
    num_hidden = res.get('num_hidden',0)
    hidden = f" hide={num_hidden}" if num_hidden > 0 else ""
    elapsed = time.time() - t0
    stk_logger(u_context, f"-> bp.scene.routes.show_persons"
                    f" n={len(found)}/{hidden} e={elapsed:.3f}")
    print(f'Got {len(found)} persons {num_hidden} hidden, fw={fw}')
    return render_template("/scene/persons_list.html", 
                           persons=found, menuno=12, 
                           num_hidden=num_hidden,
                           user_context=u_context,
                           elapsed=elapsed)


@bp.route('/scene/persons/search', methods=['GET','POST'])
@login_required
@roles_accepted('guest', 'research', 'audit', 'admin')
def show_person_search():
    ''' Persons search page.
    '''
    t0 = time.time()
    args = {'pg':'search'}
    rq = request.args if request.method == "GET" else request.form
    rule = rq.get('rule')
    if rule:  args['rule'] = rule
    key = rq.get('key')
    if key:   args['key'] = key
    print(f'{request.method} Persons {args}')

    res, u_context = _do_get_persons(args)
    if Status.has_failed(res, strict=False):
        flash(f'{res.get("statustext","error")}', 'error')

    found = res.get('items',[])
    num_hidden = res.get('num_hidden',0)
    hidden = f" hide={num_hidden}" if num_hidden > 0 else ""
    status=res['status']
    elapsed = time.time() - t0
    stk_logger(u_context, 
               f"-> bp.scene.routes.show_person_search/{rule}"
               f" n={len(found)}{hidden} e={elapsed:.3f}")
    print(f'Got {len(found)} persons {num_hidden} hidden, {rule}={key}, status={status}')
    
    datastore = PersonReader(readservice, u_context)
        
    minfont = 6
    maxfont = 20
    #maxnames = 47
    surnamestats = datastore.get_surname_list(47)
    for i, stat in enumerate(surnamestats):
        stat['order'] = i
        stat['fontsize'] = maxfont - i*(maxfont-minfont)/len(surnamestats)
    surnamestats.sort(key=itemgetter("surname"))
    
    placereader = PlaceDataReader(readservice, u_context)
        
    minfont = 6
    maxfont = 20
    #maxnames = 40
    placenamestats = placereader.get_placename_stats(40)
    #placenamestats = placenamestats[0:maxnames]
    for i, stat in enumerate(placenamestats):
        stat['order'] = i
        stat['fontsize'] = maxfont - i*(maxfont-minfont)/len(placenamestats)
    placenamestats.sort(key=itemgetter("placename"))

    
    return render_template("/scene/persons_search.html",  menuno=0,
                           persons=found,
                           user_context=u_context, 
                           num_hidden=num_hidden, 
                           rule=rule, 
                           key=key,
                           status=status,
                           surnamestats=surnamestats,
                           placenamestats=placenamestats,
                           elapsed=time.time()-t0)

# @bp.route('/obsolete/search', methods=['POST'])
# @bp.route('/obsolete/ref=<key>', methods=['GET'])
# @login_required
# @roles_accepted('guest', 'research', 'audit', 'admin')
# def obsolete_show_person_search(selection=None):
#     """ Show list of selected Persons for menu(1) or menu(12).
#         GET persons [?years]
#         GET persons/?haku [&years]
#         POST persons form: rule, name [,years]

# @bp.route('/obsolete/persons/v1', methods=['POST', 'GET'])
# @login_required
# @roles_accepted('guest', 'research', 'audit', 'admin')
# def obsolete_show_person_list_v2(selection=None):
#     """ Show list of selected Persons for menu(0). """

@bp.route('/obsolete/persons/ref=<string:refname>')
@bp.route('/obsolete/persons/ref=<string:refname>/<opt>')
@login_required
@roles_accepted('guest', 'research', 'audit', 'admin')
def obsolete_show_persons_by_refname(refname, opt=""):
    """ List persons by refname for menu(0). Called from /list/refnames
    """
    logger.warning("#TODO: fix material selection or remove action show_persons_by_refname")

    u_context = UserContext(user_session, current_user, request)
    keys = ('refname', refname)
    ref = ('ref' in opt)
    order = 0
    args = {'ref': ref, 'order': order}
    if current_user.is_authenticated:
        args['user'] = current_user.username
    print(f'Obsolete! {request.method}: keys={keys}, args={args}')
    persons = obsolete_read_persons_with_events(keys, args=args)
    print(persons)
    persons = []
    stk_logger(u_context, f"-> bp.scene.routes.show_persons_by_refname FAIL?") #n={len(persons)}")
    return render_template("/scene/persons_search.html", persons=persons, menuno=1, 
                           user_context=u_context, order=order, rule=keys)

@bp.route('/obsolete/persons/all/<string:opt>')
@bp.route('/obsolete/persons/all/')
@login_required
@roles_accepted('guest', 'research', 'audit', 'admin')
def obsolete_show_all_persons_list(opt=''):
    """ List all persons for menu(1)    OLD MODEL WITHOUT User selection

        Linked from admin/refnames only

        The string opt may include keys 'ref', 'sn', 'pn' in arbitary order
        with no delimiters. You may write 'refsn', 'ref:sn' 'sn-ref' etc.

        TODO Should have restriction by owner's UserProfile 
    """
    return 'Obsolete! show_all_persons_list<br><a href="javascript:history.back()">Go Back</a>'



# -------------------------- Menu 12 Persons by user ---------------------------

@bp.route('/scene/person', methods=['GET'])
#     @login_required
@roles_accepted('guest','research', 'audit', 'admin')
def show_person(uuid=None):
    """ One Person with all connected nodes - NEW version 3.

        Arguments:
        - uuid=     persons uuid
        - debug=1   optinal for javascript tests
    """
    t0 = time.time()
    uuid = request.args.get('uuid', uuid)
    dbg = request.args.get('debug', None)
    u_context = UserContext(user_session, current_user, request)
    #args = {}

    from bl.person_reader import PersonReaderTx
    from pe.neo4j.readservice_tx import Neo4jReadServiceTx
    readservice = Neo4jReadServiceTx(shareds.driver)
    reader = PersonReaderTx(readservice, u_context)

    result = reader.get_person_data(uuid) #, args)
    # result {'person':PersonBl, 'objs':{uniq_id:obj}, 'jscode':str, 'root':{root_type,root_user,batch_id}}
    if Status.has_failed(result):
        flash(f'{result.get("statustext","error")}', 'error')
    person = result.get('person')
    objs = result.get('objs',[])
    print (f'# Person with {len(objs)} objects')
    jscode = result.get('jscode','')
    root = result.get('root')

    stk_logger(u_context, f"-> bp.scene.routes.show_person n={len(objs)}")

    last_year_allowed = datetime.now().year - shareds.PRIVACY_LIMIT
    return render_template("/scene/person.html", person=person, obj=objs, 
                           jscode=jscode, menuno=12, debug=dbg, root=root,
                           last_year_allowed=last_year_allowed, 
                           elapsed=time.time()-t0, user_context=u_context)


# @bp.route('/scene/person/uuid=<pid>')
# @bp.route('/scene/person=<int:pid>')
# #     @login_required
# def obsolete_show_person_v1(pid):


#@bp.route('/scene/event/<int:uniq_id>')
@bp.route('/older/event/uuid=<string:uuid>')
@login_required
@roles_accepted('guest', 'research', 'audit', 'admin')
def obsolete_show_event_v1(uuid):
    """ Event page with accompanied persons and families.

        Derived from bp.obsolete_tools.routes.show_baptism_data()
    """
    u_context = UserContext(user_session, current_user, request)
    reader = EventReader(readservice, u_context) 

    res = reader.get_event_data(uuid)

    status = res.get('status')
    if status != Status.OK:
        flash(f'{_("Event not found")}: {res.get("statustext")}','error')
    event = res.get('event', None)
    members = res.get('members', [])

    stk_logger(u_context, f"-> bp.scene.routes.show_event_page n={len(members)}")
    return render_template("/scene/event.html",
                           event=event, participants=members)

@bp.route('/scene/event/uuid=<string:uuid>')
@login_required
@roles_accepted('guest', 'research', 'audit', 'admin')
def show_event_vue(uuid):
    """ Show Event page template which marchals data by Vue. """
    u_context = UserContext(user_session, current_user, request)
    return render_template("/scene/event_vue.html", uuid=uuid, user_context=u_context)

@bp.route('/scene/json/event', methods=['POST','GET'])
@login_required
@roles_accepted('guest', 'research', 'audit', 'admin')
def json_get_event():
    """ Get Event page data.
    """
    t0 = time.time()
    try:
        args = request.args
        if args:
            print(f'got request args: {args}')
        else:
            args = json.loads(request.data)
            print(f'got request data: {args}')
        uuid = args.get('uuid')
        if not uuid:
            print("bp.scene.routes.json_get_person_families: Missing uuid")
            return jsonify({"records":[], "status":Status.ERROR,"statusText":"Missing uuid"})

        u_context = UserContext(user_session, current_user, request)
        reader = EventReader(readservice, u_context) 
    
        res = reader.get_event_data(uuid, args)
    
        status = res.get('status')
        if status != Status.OK:
            flash(f'{_("Event not found")}: {res.get("statustext")}','error')
        if status == Status.NOT_FOUND:
            return jsonify({"event":None, "members":[],
                            "statusText":_('No event found'),
                            "status":status})
        elif status != Status.OK:
            return jsonify({"event":None, "members":[],
                            "statusText":_('No event found'),
                            "status":status})
        # Event
        event = res.get('event', None)
        event.type_lang = jinja_filters.translate(event.type, 'evt').title()
        # Event members
        members = res.get('members', [])
        for m in members:
            if m.label == "Person":
                m.href = '/scene/person?uuid=' + m.uuid
                m.names[0].type_lang = jinja_filters.translate(m.names[0].type, 'nt')
            elif m.label == "Family":
                m.href = '/scene/family?uuid=' + m.uuid
            m.role_lang = jinja_filters.translate(m.role, 'role') if m.role  else  ''
        # Actually there is one place and one pl.uppers
        places = res.get('places', [])
        for pl in places:
            pl.href = '/scene/location/uuid=' + pl.uuid
            pl.type_lang = jinja_filters.translate(pl.type, 'lt').title()
            for up in pl.uppers:
                up.href = '/scene/location/uuid=' + up.uuid
                up.type_lang = jinja_filters.translate(up.type, 'lt_in').title()
        # Event notes
        notes = res.get('notes', [])
        # Medias
        medias = res.get('medias', [])
        for m in medias:
            m.href = '/scene/media?uuid=' + m.uuid

        res_dict = {"event": event, 'members': members, 
                    'notes':notes, 'places':places, 'medias':medias,
                    'allow_edit': u_context.allow_edit,
                    'translations':{'myself': _('Self') }
                    }
        response = StkEncoder.jsonify(res_dict)
        print(response)
        t1 = time.time()-t0
        stk_logger(u_context, f"-> bp.scene.routes.json_get_event n={len(members)} e={t1:.3f}")
        return response

    except Exception as e:
        traceback.print_exc()
        return jsonify({"records":[], 
                        "status":Status.ERROR,
                        "member":uuid,
                        "statusText":f"Failed {e.__class__.__name__}"})


@bp.route('/scene/update/event', methods=['POST'])
@login_required
@roles_accepted('audit')
def json_update_event():
    """ Update Event 
    """
    t0 = time.time()
    try:
        args = request.args
        if args:
            #print(f'got request args: {args}')
            pass
        else:
            args = json.loads(request.data)
            #print(f'got request data: {args}')
        uuid = args.get('uuid')
        u_context = UserContext(user_session, current_user, request)
        writer = EventWriter(writeservice, u_context) 
        rec = writer.update_event(uuid, args)
        if rec.get("status") != Status.OK:
            return rec
        event = rec.get("item")
        statusText = rec.get("statusText","")
        event.type_lang = jinja_filters.translate(event.type, 'evt').title()
        res_dict = {"status":Status.OK, "event": event, "statusText": statusText} 
        response = StkEncoder.jsonify(res_dict)
        #print(response)
        t1 = time.time()-t0
        stk_logger(u_context, f"-> bp.scene.routes.json_update_event e={t1:.3f}")
        return response
    except Exception as e:
        traceback.print_exc()
        return jsonify({"records":[], 
                        "status":Status.ERROR,
                        "member":uuid,
                        "statusText":f"Failed: {e}"})
    

# ------------------------------ Menu 3: Families --------------------------------

@bp.route('/scene/families')
@login_required
@roles_accepted('guest', 'research', 'audit', 'admin')
def show_families():
    """ List of Families for menu(3)
    """
    print(f"--- {request}")
    print(f"--- {user_session}")
    # Set context by owner and the data selections
    u_context = UserContext(user_session, current_user, request)
    # Which range of data is shown
    u_context.set_scope_from_request(request, 'person_scope')
    opt = request.args.get('o', 'father', type=str)
    u_context.order = 'man' if opt == 'father' else 'wife'
    u_context.count = request.args.get('c', 100, type=int)
    t0 = time.time()
    
    reader = FamilyReader(readservice, u_context) 

    # 'families' has Family objects
    families = reader.get_families() #o_context=u_context, opt=opt, limit=count)

    stk_logger(u_context, f"-> bp.scene.routes.show_families/{opt} n={len(families)}")
    return render_template("/scene/families.html", families=families, 
                           user_context=u_context, elapsed=time.time()-t0)

# @bp.route('/scene/family=<int:fid>')
# def show_family_page(fid):
#     """ Home page for a Family.    OBSOLETE: use show_family
#         fid = id(Family)
#     """

@bp.route('/scene/family', methods=['GET'])
@login_required
@roles_accepted('guest', 'research', 'audit', 'admin')
def show_family_page(uuid=None):
    """ One Family.
    """
    uuid = request.args.get('uuid', uuid)
    if not uuid:
        return redirect(url_for('virhesivu', code=1, text="Missing Family key"))
    t0 = time.time()
    u_context = UserContext(user_session, current_user, request)
    reader = FamilyReader(readservice, u_context) 

    res = reader.get_family_data(uuid)

    stk_logger(u_context, "-> bp.scene.routes.show_family_page")
    status = res.get('status')
    if status != Status.OK:
        if status == Status.ERROR:
            flash(f'{res.get("statustext")}', 'error')
        else:
            flash(f'{ _("This item is not available") }', 'warning')

    return render_template("/scene/family.html",  menuno=3, family=res['item'],
                           user_context=u_context, elapsed=time.time()-t0)


@bp.route('/scene/json/families', methods=['POST','GET'])
@login_required
@roles_accepted('guest', 'research', 'audit', 'admin')
def json_get_person_families():
    """ Get all families for a Person as json structure.

        The families are ordered by marriage time.
    """
    t0 = time.time()
    try:
        args = request.args
        if args:
            print(f'got request args: {args}')
        else:
            args = json.loads(request.data)
            print(f'got request data: {args}')
        uuid = args.get('uuid')
        if not uuid:
            print("bp.scene.routes.json_get_person_families: Missing uuid")
            return jsonify({"records":[], "status":Status.ERROR,"statusText":"Missing uuid"})

        u_context = UserContext(user_session, current_user, request)
        reader = FamilyReader(readservice, u_context) 

        res = reader.get_person_families(uuid)

        if res.get('status') == Status.NOT_FOUND:
            return jsonify({"member":uuid, "records":[],
                            "statusText":_('No families'),
                            "status":Status.NOT_FOUND})        

        items = res['items']
        res_dict = {'records': items, 
                    "member": uuid, 
                    'statusText': f'Löytyi {len(items)} perhettä',
                    'translations':{'family': _('Family'), 
                                    'children': _('Children')}
                    }
        response = StkEncoder.jsonify(res_dict)

        t1 = time.time()-t0
        stk_logger(u_context, f"-> bp.scene.routes.show_person_families_json n={len(items)} e={t1:.3f}")
        #print(response)
        return response

    except Exception as e:
        traceback.print_exc()
        return jsonify({"records":[], 
                        "status":Status.ERROR,
                        "member":uuid,
                        "statusText":f"Failed {e.__class__.__name__}"})


# ------------------------------ Menu 4: Places --------------------------------

@bp.route('/scene/locations')
@login_required
@roles_accepted('guest', 'research', 'audit', 'admin')
def show_places():
    """ List of Places for menu(4)
    """
    t0 = time.time()
    print(f"--- {request}")
    print(f"--- {user_session}")
    # Set context by owner and the data selections
    u_context = UserContext(user_session, current_user, request)
    # Which range of data is shown
    u_context.set_scope_from_request(request, 'place_scope')
    u_context.count = request.args.get('c', 50, type=int)

    reader = PlaceDataReader(readservice, u_context) 

    # The list has Place objects, which include also the lists of
    # nearest upper and lower Places as place[i].upper[] and place[i].lower[]

    res = reader.get_place_list()

    if res['status'] == Status.NOT_FOUND:
        print(f'bp.scene.routes.show_places: {_("No places found")}')
    elif res['status'] != Status.OK:
        print(f'bp.scene.routes.show_places: {_("Could not get places")}: {res.get("statustext")}')

    elapsed = time.time() - t0
    stk_logger(u_context, f"-> bp.scene.routes.show_places n={len(res.get('items'))} e={elapsed:.3f}")
    return render_template("/scene/places.html", places=res['items'], 
                           menuno=4, user_context=u_context, elapsed=elapsed)


@bp.route('/scene/location/uuid=<locid>')
@login_required
@roles_accepted('guest', 'research', 'audit', 'admin')
def show_place(locid):
    """ Home page for a Place, shows events and place hierarchy.
    """
    t0 = time.time()
    u_context = UserContext(user_session, current_user, request)
    try:
        # Open database connection and start transaction
        # readservice -> Tietokantapalvelu
        #      reader ~= Toimialametodit
        readservice = Neo4jReadService(shareds.driver)
        reader = PlaceDataReader(readservice, u_context) 
    
        res = reader.get_places_w_events(locid)

        if res['status'] == Status.NOT_FOUND:
            print(f'bp.scene.routes.show_place: {_("Place not found")}')
            #return redirect(url_for('virhesivu', code=1, text=f'Ei löytynyt yhtään'))
        if res['status'] != Status.OK:
            print(f'bp.scene.routes.show_place: {_("Place not found")}: {res.get("statustext")}')
            #return redirect(url_for('virhesivu', code=1, text=f'Virhetilanne'))

    except KeyError as e:
        traceback.print_exc()
        return redirect(url_for('virhesivu', code=1, text=str(e)))

    cnt = len(res.get('events')) if res.get('events',False) else 0
    stk_logger(u_context, f"-> bp.scene.routes.show_place n={cnt}")
    return render_template("/scene/place_events.html", 
                           place=res.get('place'), 
                           pl_hierarchy=res.get('hierarchy'),
                           events=res.get('events'),
                           user_context=u_context, elapsed=time.time()-t0)

# ------------------------------ Menu 5: Sources --------------------------------

@bp.route('/scene/sources')
@bp.route('/scene/sources/<series>')
@login_required
@roles_accepted('guest', 'research', 'audit', 'admin')
def show_sources(series=None):
    """ Lähdeluettelon näyttäminen ruudulla for menu(5)
    
        Possible args example: ?years=1800-1899&series=birth
        - source years (#todo)
        - series, one of {"birth", "babtism", "wedding", "death", "move"}
        Missing series or years = all
        Theme may also be expressed in url path

    """
    print(f"--- {request}")
    print(f"--- {user_session}")
    t0 = time.time()
    # Set context by owner and the data selections
    u_context = UserContext(user_session, current_user, request)
    # Which range of data is shown
    u_context.set_scope_from_request(request, 'source_scope')
    u_context.count = request.args.get('c', 100, type=int)

    # readservice -> Tietokantapalvelu
    #      reader ~= Toimialametodit
    readservice = Neo4jReadService(shareds.driver)
    reader = SourceDataStore(readservice, u_context)

    if series:
        u_context.series = series
    try:
        res = reader.get_source_list()
        if res['status'] == Status.NOT_FOUND:
            print('bp.scene.routes.show_sources: No sources found')
        elif res['status'] != Status.OK:
            print(f'bp.scene.routes.show_sources: Error {res.get("statustext")}')
    except KeyError as e:
        return redirect(url_for('virhesivu', code=1, text=str(e)))
    series = u_context.series if u_context.series else "all"
    stk_logger(u_context, f"-> bp.scene.routes.show_sources/{series} n={len(res['items'])}")
    return render_template("/scene/sources.html", sources=res['items'], 
                           user_context=u_context, elapsed=time.time()-t0)


@bp.route('/scene/source', methods=['GET'])
#@bp.route('/scene/source=<string:sourceid>')
@login_required
@roles_accepted('guest', 'research', 'audit', 'admin')
def show_source_page(sourceid=None):
    """ Home page for a Source with referring Event and Person data
    """
    uuid = request.args.get('uuid', sourceid)
    if not uuid:
        return redirect(url_for('virhesivu', code=1, text="Missing Source key"))
    u_context = UserContext(user_session, current_user, request)
    try:
        reader = SourceDataStore(readservice, u_context) 
    
        res = reader.get_source_with_references(uuid, u_context)
        
        if res['status'] == Status.NOT_FOUND:
            msg = res.get('statustext', _('No objects found'))
            return redirect(url_for('virhesivu', code=1, text=msg))
        if res['status'] != Status.OK:
            msg = res.get('statustext', _('Error'))
            return redirect(url_for('virhesivu', code=1, text=msg))

    except KeyError as e:
        return redirect(url_for('virhesivu', code=1, text=str(e)))
    stk_logger(u_context, f"-> bp.scene.routes.show_source_page n={len(res['citations'])}")
#     for c in res.citations:
#         for i in c.citators:
#             if i.id[0] == "F":  print(f'{c} – family {i} {i.clearname}')
#             else:               print(f'{c} – person {i} {i.sortname}')
    return render_template("/scene/source_events.html", source=res['item'],
                           citations=res['citations'], user_context=u_context)

# ------------------------------ Menu 6: Media --------------------------------

@bp.route('/scene/medias')
@login_required
@roles_accepted('guest', 'research', 'audit', 'admin')
def show_medias():
    """ List of Medias for menu(5)
    """
    t0 = time.time()
    print(f"--- {request}")
    print(f"--- {user_session}")
    # Set context by owner and the data selections
    u_context = UserContext(user_session, current_user, request)
    # Which range of data is shown
    u_context.set_scope_from_request(request, 'media_scope')
    u_context.count = 20

    datareader = MediaReader(readservice, u_context)
#   medias = Media.read_my_media_list(u_context, 20)

    res = datareader.read_my_media_list()
    if Status.has_failed(res, False):
        flash(f'{res.get("statustext","error")}', 'error')
    medias = res.get('items', [])

    stk_logger(u_context, f"-> bp.scene.media.show_medias fw n={len(medias)}")
    return render_template("/scene/medias.html", medias=medias, 
                           user_context=u_context, elapsed=time.time()-t0)

@bp.route('/scene/media', methods=['GET'])
@login_required
@roles_accepted('guest', 'research', 'audit', 'admin')
def show_media(uuid=None):
    """ 
        One Media
    """
    uuid = request.args.get('uuid', uuid)
    u_context = UserContext(user_session, current_user, request)
#     if not uuid:
#         return redirect(url_for('virhesivu', code=1, text="Missing Media key"))
    reader = MediaReader(readservice, u_context)

    res = reader.get_one(uuid)

    status = res.get('status')
    if status != Status.OK:
        print(f'bp.scene.routes.show_media: error {status} {res.get("statustext")}')
        if status == Status.ERROR:
            flash(f'{res.get("statustext")}', 'error')
        else:
            flash(f'{ _("This item is not available") }', 'warning')

    medium = res.get('item', None)
    if medium:
        fullname, mimetype = media.get_fullname(medium.uuid)
        stk_logger(u_context, f"-> bp.scene.routes.show_media n={len(medium.ref)}")
    else:
        flash(f'{res.get("statustext","error")}', 'error')
        fullname = None
        mimetype = None
    if mimetype == "application/pdf":
        size = 0
    else:
        size = media.get_image_size(fullname)

    return render_template("/scene/media.html", media=medium, size=size,
                           user_context=u_context, menuno=6)

# ----------- Access media file ---------------

@bp.route('/scene/media/<fname>')
@login_required
@roles_accepted('guest', 'research', 'audit', 'admin')
def fetch_media(fname):
    """ Fetch media file to display full screen.
    
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
            return Response(buffer.getvalue(), mimetype='image/png')
        else:
            logger.debug("-> bp.scene.routes.fetch_media full")
            return send_file(fullname, mimetype=mimetype)        
    except FileNotFoundError:
        # Show default image
        ret = send_file(os.path.join('static', 'image/noone.jpg'), mimetype=mimetype)
        logger.debug(f"-> bp.scene.routes.fetch_media none")
        return ret

@bp.route('/scene/thumbnail')
@login_required
@roles_accepted('guest', 'research', 'audit', 'admin')
def fetch_thumbnail():
    """ Fetch thumbnail file to display
    """
    uuid = request.args.get("id")
    crop = request.args.get("crop")
    if crop == "None":
        crop = None
    thumb_mime='image/jpg'
    thumbname = "(no file)"
    try:
        thumbname, cl = media.get_thumbname(uuid, crop)
        if cl == "jpg":
            ret = send_file(thumbname, mimetype=thumb_mime)
        elif cl == "pdf":
            ret = send_file(os.path.join('static', 'image/a_pdf.png'), mimetype=thumb_mime)
        else:
            ret = send_file(os.path.join('static', 'image/noone.jpg'), mimetype=thumb_mime)
        logger.debug(f"-> bp.scene.routes.fetch_thumbnail ok")
    except FileNotFoundError:
        # Show default image
        ret = send_file(os.path.join('static', 'image/noone.jpg'), mimetype=thumb_mime)
        logger.debug(f"-> bp.scene.routes.fetch_thumbnail none")

    return ret
        
