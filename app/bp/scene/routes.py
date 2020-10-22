'''
Created on 12.8.2018

@author: jm
'''
import io
import os
import traceback
import json

import logging 
logger = logging.getLogger('stkserver')
import time
from datetime import datetime

import shareds
from flask import send_file, Response, jsonify
from flask import render_template, request, redirect, url_for, flash, session as user_session
from flask_security import current_user, login_required, roles_accepted
from flask_babelex import _

from ui.user_context import UserContext
from bl.base import Status, StkEncoder
from bl.place import PlaceReader
from bl.source import SourceReader
from bl.family import FamilyReader
from bl.event import EventReader
from bl.person import PersonReader
#from bl.media import MediaBl_todo
from templates import jinja_filters

from . import bp
#from bp.scene.scene_reader import get_person_full_data
from bp.scene.models import media
from models.gen.family_combo import Family_combo
#from models.gen.source import Source
from models.gen.media import Media

from models.datareader import read_persons_with_events
#from models.datareader import get_person_data_by_id # -- vanhempi versio ---
#from models.datareader import get_event_participants
#from models.datareader import get_place_with_events
#from models.datareader import get_source_with_events
#from templates.jinja_filters import translate

# Select the read driver for current database
from pe.neo4j.read_driver import Neo4jReadDriver
dbreader = Neo4jReadDriver(shareds.driver)


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


# Narrative start page

@bp.route('/scene',  methods=['GET', 'POST'])
def obsolete_scene():
    """ Home page for scene narrative pages ('kertova') for anonymous. 
    
        NOT IN USE!?
    """
    return 'Obsolete: scene<br><a href="javascript:history.back()">Go Back</a>'
#     print(f"--- {request}")
#     print(f"--- {user_session}")
#     u_context = UserContext(user_session, current_user, request)
#     u_context.set_scope_from_request(request, 'person_scope')
#     stk_logger(u_context, f"-> bp.scene.routes.scene '{u_context.scope[0]}'")
#     return render_template('/start/index_scene.html')


# ------------------------- Menu 1: Person search ------------------------------

def _do_get_persons(args):
    ''' Execute persons list query by arguments.

    Persons, current
        GET    /all                                       --> args={pg:all}
    Persons, forward
        GET    /all?fw=<sortname>&c=<count>               --> args={pg:all,fw:sortname,c:count}
    Persons, by years range
        GET    /all?years=<y1-y2>                         --> args={pg:all,years:y1_y2}
    Persons fw,years
        GET    /all?years=<y1-y2>&fw=<sortname>&c=<count> --> args={pg:all,fw:sortname,c:count,years:y1_y2}
    Search form
        GET    /search                                    --> args={pg:search,restart:True}
    Search by refname
        GET    /search?rule=ref,key=<str>                 --> args={pg:search,rule:ref,key:str}
    Search form
        POST   /search                                    --> args={pg:search,restart:True}
    Search by name starting
        POST   /search rule=<rule>,key=<str>              --> args={pg:search,rule:ref,key:str}
    Search by years range
        POST   /search years=<y1-y2>                      --> args={pg:search,years:y1_y2}
    Search by name & years
        POST   /search rule=<rule>,key=<str>,years=<y1-y2> --> args={pg:search,rule:ref,key:str,years:y1_y2}
    '''
    u_context = UserContext(user_session, current_user, request)
    if args.get('pg') == 'search':
        # No scope
        u_context.set_scope_from_request()
    else:
        u_context.set_scope_from_request(request, 'person_scope')
    u_context.count = request.args.get('c', 100, type=int)
    reader = PersonReader(dbreader, u_context)
    
    res = reader.get_person_search(args)
    if res.get('status') != Status.OK:
        flash(f'{_("No persons found")}: {res.get("statustext")}','error')

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
    years = request.args.get('years')
    if years: args['years'] = years
    fw = request.args.get('fw')
    if fw:    args['fw'] = fw
    c = request.args.get('c')
    if c:     args['c'] = c
    print(f'{request.method} All persons {args}')

    res, u_context = _do_get_persons(args)

    found = res.get('items',[])
    hide = res.get('num_hidden',0)
    hidden = f" hide={hide}" if hide > 0 else ""
    elapsed = time.time() - t0
    stk_logger(u_context, f"-> bp.scene.routes.show_persons"
                    f" n={len(found)}/{hidden} e={elapsed:.3f}")
    return render_template("/scene/persons_list.html", 
                           persons=found, menuno=12, 
                           num_hidden=hide, user_context=u_context,
                           elapsed=elapsed)
#     return render_template("/scene/persons_search.html",  menuno=12,
#                            persons=res.get('items'),
#                            user_context=u_context, 
#                            num_hidden=res.get('num_hidden'), 
#                            rule=args.get('key'), elapsed=time.time()-t0)


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
    years = rq.get('years', default=None, type=str)
    if years: args['years'] = years
    if rule is None and years is None:
        args['restart'] = True
    print(f'{request.method} Persons {args}')

    res, u_context = _do_get_persons(args)

    found = res.get('items',[])
    hide = res.get('num_hidden',0)
    hidden = f" hide={hide}" if hide > 0 else ""
    elapsed = time.time() - t0
    stk_logger(u_context, f"-> bp.scene.routes.show_person_search"
                    f" n={len(found)}/{hidden} e={elapsed:.3f}")
    return render_template("/scene/persons_search.html",  menuno=0,
                           persons=found,
                           user_context=u_context, 
                           num_hidden=res.get('num_hidden'), 
                           rule=args.get('rule',''), 
                           key=key, years=years,
                           elapsed=time.time()-t0)

@bp.route('/obsolete/search', methods=['POST'])
@bp.route('/obsolete/ref=<key>', methods=['GET'])
@login_required
@roles_accepted('guest', 'research', 'audit', 'admin')
def obsolete_show_person_search(selection=None):
    """ Show list of selected Persons for menu(1) or menu(12).
    
        GET persons [?years]
        GET persons/?haku [&years]
        POST persons form: rule, name [,years]
        
    """
    t0 = time.time()
    u_context = UserContext(user_session, current_user, request)
    #u_context.set_scope_from_request(request, 'person_scope')
    args={}
    args['user'] = u_context.user
    args['context_code'] = u_context.context
    persons = []
    if request.method == 'POST':
        try:
            # Selection from search form
            keys = (request.form['rule'], request.form['name'])
            theme=keys[0]
            #TODO: filter by user in the read method
            print(f'{request.method}: keys={keys}, theme={theme}, args={args}')
            persons = read_persons_with_events(keys, args)

        except Exception as e:
            logger.error(f"bp.scene.routes.show_person_list error {e}")
            flash("Valitse haettava nimi ja tyyppi", category='warning')
    else:
        # the code below is executed if the request method
        # was GET (no search name given) or the credentials were invalid
        persons = []
        if selection:
            # Use selection context
            keys = selection.split('=')
            theme=keys[0]
        else:
            keys = ('surname',)
            theme=''
        #TODO: filter by user in the read method
        print(f'{request.method}: keys={keys}, theme={theme}, args={args}')
        persons = read_persons_with_events(keys, args)
        

    # If Context is COMMON (1):
    #    - show both own candidate and approved materials
    #    - but hide candadate materials of other users
    # If Context is OWN (2): show all own candidate materials
    select_users = [None] # COMMON, no user
    if u_context.use_owner_filter():
        #select_users.append(None)
        select_users.append(u_context.user)
    hidden=0
    persons_out = []
    for p in persons:
        if p.too_new and p.user != u_context.user:
            print(f'Hide {p.sortname} too_new={p.too_new}, owner {p.user}')
            hidden += 1
        else:
            #print(f'Show {p.sortname} too_new={p.too_new}, owner {p.user}')
            persons_out.append(p)
    stk_logger(u_context, f"-> bp.scene.routes.show_person_list/{theme}-{request.method}"
               f" {u_context.owner_or_common()}"
               f" n={len(persons_out)} hide={len(persons)-len(persons_out)}")

    return render_template("/scene/persons_search.html", persons=persons_out,
                           user_context=u_context, num_hidden=hidden, 
                           menuno=0, rule=keys, elapsed=time.time()-t0)

@bp.route('/obsolete/persons/v1', methods=['POST', 'GET'])
@login_required
@roles_accepted('guest', 'research', 'audit', 'admin')
def obsolete_show_person_list_v2(selection=None):
    """ Show list of selected Persons for menu(0). """
    t0 = time.time()
    u_context = UserContext(user_session, current_user, request)
    #u_context.set_scope_from_request(request, 'person_scope')
    args={}
    args['user'] = u_context.user
    args['context_code'] = u_context.context
    persons = []
    if request.method == 'POST':
        try:
            # Selection from search form
            keys = (request.form['rule'], request.form['name'])
            theme=keys[0]
            #TODO: filter by user in the read method
            persons = read_persons_with_events(keys, args)

        except Exception as e:
            logger.error(f"bp.scene.routes.show_person_list error {e}")
            flash("Valitse haettava nimi ja tyyppi", category='warning')
    else:
        # the code below is executed if the request method
        # was GET (no search name given) or the credentials were invalid
        persons = []
        if selection:
            # Use selection context
            keys = selection.split('=')
            theme=keys[0]
        else:
            keys = ('surname',)
            theme=''
        #TODO: filter by user in the read method
        persons = read_persons_with_events(keys, args)
        

    # If Context is COMMON (1):
    #    - show both own candidate and approved materials
    #    - but hide candadate materials of other users
    # If Context is OWN (2): show all own candidate materials
    select_users = [None] # COMMON, no user
    if u_context.use_owner_filter():
        #select_users.append(None)
        select_users.append(u_context.user)
    hidden=0
    persons_out = []
    for p in persons:
        if p.too_new and p.user != u_context.user:
            print(f'Hide {p.sortname} too_new={p.too_new}, owner {p.user}')
            hidden += 1
        else:
            #print(f'Show {p.sortname} too_new={p.too_new}, owner {p.user}')
            persons_out.append(p)
    stk_logger(u_context, f"-> bp.scene.routes.show_person_list/{theme}-{request.method}"
               f" {u_context.owner_or_common()}"
               f" n={len(persons_out)} hide={len(persons)-len(persons_out)}")

    return render_template("/scene/persons_search.html", persons=persons_out,
                           user_context=u_context, num_hidden=hidden, 
                           menuno=0, rule=keys, elapsed=time.time()-t0)

@bp.route('/obsolete/persons/ref=<string:refname>')
@bp.route('/obsolete/persons/ref=<string:refname>/<opt>')
@login_required
@roles_accepted('guest', 'research', 'audit', 'admin')
def obsolete_show_persons_by_refname(refname, opt=""):
    """ List persons by refname for menu(0). Called from /list/refnames
    """
    logger.warning("#TODO: fix material selevtion or remove action show_persons_by_refname")

    u_context = UserContext(user_session, current_user, request)
    keys = ('refname', refname)
    ref = ('ref' in opt)
    order = 0
    args = {'ref': ref, 'order': order}
    if current_user.is_authenticated:
        args['user'] = current_user.username
    print(f'Obsolete! {request.method}: keys={keys}, args={args}')
    persons = read_persons_with_events(keys, args=args)
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

@bp.route('/obsolete/persons_all/')
@login_required
@roles_accepted('guest', 'research', 'audit', 'admin')
def obsolete_show_persons_all():
    """ List all persons for menu(12).

        Both my own and other persons depending on sum of url attributes div + div2
        or session variables.

        The position in persons list is defined by –
           1. by attribute fw, if defined (the forward arrow or from seach field)
           2. by session next_person[1], if defined (the page last visited)
              #TODO: next_person[0] is not in use, yet (backward arrow)
           3. otherwise "" (beginning)
    """
    print(f"--- {request}")
    print(f"--- {user_session}")
    # Set filter by owner and the data selections
    u_context = UserContext(user_session, current_user, request)
    # Which range of data is shown
    u_context.set_scope_from_request(request, 'person_scope')
    # How many objects are shown?
    u_context.count = int(request.args.get('c', 100))
    u_context.privacy_limit = shareds.PRIVACY_LIMIT
    print(f'{request.method}: keys=-, args=-')

    t0 = time.time()
    reader = PersonReader(dbreader, u_context)

    results = reader.get_person_list()
    status = results.get('status')
    if status != Status.OK:
        flash(f'{_("No persons found")}: {results.get("statustext")}','error')

    elapsed = time.time() - t0
    found = results.get('items',[])
    hide = results['num_hidden']
    hidden = f" hide={hide}" if hide > 0 else ""
    stk_logger(u_context, f"-> bp.scene.routes.show_persons_all"
                    f" n={len(found)}{hidden} e={elapsed:.3f}")
#     print(f"Got {len(found)} persons"
#           f" with {len(found)-results.hide} hidden"
#           f" and status {status}"
#           f" in {elapsed:.3f}s")
    return render_template("/scene/persons_list.html", persons=found,
                           num_hidden=hide, user_context=u_context,
                           menuno=12, elapsed=elapsed)


@bp.route('/obsolete/person/<int:uid>')
#     @login_required
@roles_accepted('member', 'gedcom', 'research', 'audit', 'admin')
def obsolete_show_person_v2(uid=None):
    """ One Person with all connected nodes - version 3 with apoc
    """
    return 'Obsolete: show_person_v2<br><a href="javascript:history.back()">Go Back</a>'
#     t0 = time.time()
#     if current_user.is_authenticated:
#         user=current_user.username
#     else:
#         user=None
#     # v2 Person page data
#     person, objs, marks = get_a_person_for_display_apoc(uid, user)
#     stk_logger(u_context, "-> bp.scene.routes.show_v2")
#     if not person:
#         return redirect(url_for('virhesivu', code=2, text="Ei oikeutta katsoa tätä henkilöä"))
#     #print (f"Current language {current_user.language}")
#     from bp.scene.models.media import get_thumbname
#     for i in person.media_ref:
#         print(get_thumbname(objs[i].uuid))
#     return render_template("/scene/person_v2.html", person=person, obj=objs, 
#                            marks=marks, menuno=12, elapsed=time.time()-t0)


@bp.route('/scene/person', methods=['GET'])
#     @login_required
@roles_accepted('guest','research', 'audit', 'admin')
def show_person(uid=None):
    """ One Person with all connected nodes - NEW version 3.

        Arguments:
        - uuid=     persons uuid
        - debug=1   optinal for javascript tests
    """
    t0 = time.time()
    uid = request.args.get('uuid', uid)
    dbg = request.args.get('debug', None)
    u_context = UserContext(user_session, current_user, request)

    reader = PersonReader(dbreader, u_context)
    args = {}

    result = reader.get_person_data(uid, args)
    # result {'person', 'objs', 'jscode', 'root'}
    status = result.get('status')
    if status != Status.OK:
        flash(f'{_("Person not found")}: {result.get("statustext","error")}', 'error')
    person = result.get('person')
    objs = result.get('objs',[])
    jscode = result.get('jscode','')
    root = result.get('root')

    stk_logger(u_context, f"-> bp.scene.routes.show_person n={len(objs)}")

    #for ref in person.media_ref: print(f'media ref {ref}')
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

        Derived from bp.tools.routes.show_baptism_data()
    """
    u_context = UserContext(user_session, current_user, request)
    reader = EventReader(dbreader, u_context) 

    results = reader.get_event_data(uuid)

    status = results.get('status')
    if status != Status.OK:
        flash(f'{_("Event not found")}: {results.get("statustext")}','error')
    event = results.get('event', None)
    members = results.get('members', [])

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
        reader = EventReader(dbreader, u_context) 
    
        results = reader.get_event_data(uuid, args)
    
        status = results.get('status')
        if status != Status.OK:
            flash(f'{_("Event not found")}: {results.get("statustext")}','error')
        if status == Status.NOT_FOUND:
            return jsonify({"event":None, "members":[],
                            "statusText":_('No event found'),
                            "status":status})
        elif status != Status.OK:
            return jsonify({"event":None, "members":[],
                            "statusText":_('No event found'),
                            "status":status})
        # Event
        event = results.get('event', None)
        event.type_lang = jinja_filters.translate(event.type, 'evt').title()
        # Event members
        members = results.get('members', [])
        for m in members:
            if m.label == "Person":
                m.href = '/scene/person?uuid=' + m.uuid
                m.names[0].type_lang = jinja_filters.translate(m.names[0].type, 'nt')
            elif m.label == "Family":
                m.href = '/scene/family?uuid=' + m.uuid
            m.role_lang = jinja_filters.translate(m.role, 'role') if m.role  else  ''
        # Actually there is one place and one pl.uppers
        places = results.get('places', [])
        for pl in places:
            pl.href = '/scene/location/uuid=' + pl.uuid
            pl.type_lang = jinja_filters.translate(pl.type, 'lt').title()
            for up in pl.uppers:
                up.href = '/scene/location/uuid=' + up.uuid
                up.type_lang = jinja_filters.translate(up.type, 'lt_in').title()
        # Event notes
        notes = results.get('notes', [])
        # Medias
        medias = results.get('medias', [])
        for m in medias:
            m.href = '/scene/media?uuid=' + m.uuid

        #TODO: The auditor may edit, not user self as here
        if u_context.user and u_context.context == u_context.choices.OWN:
            allow_edit = True
        else:
            allow_edit = False

        res_dict = {"event": event, 'members': members, 
                    'notes':notes, 'places':places, 'medias':medias,
                    'statusText': f'Löytyi {len(members)} tapahtuman osallista',
                    'allow_edit': allow_edit,
                    'translations':{'myself': _('Self') }
                    }
        response = json.dumps(res_dict, cls=StkEncoder)
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
    count = request.args.get('c', 100, type=int)
    t0 = time.time()
        
    # 'families' has Family objects
    families = Family_combo.get_families(o_context=u_context, opt=opt, limit=count)

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
def show_family_page(uid=None):
    """ One Family.
    """
    uid = request.args.get('uuid', uid)
    if not uid:
        return redirect(url_for('virhesivu', code=1, text="Missing Family key"))
    t0 = time.time()

    try:
        u_context = UserContext(user_session, current_user, request)
        reader = FamilyReader(dbreader, u_context) 
    
        results = reader.get_family_data(uid)
        #family = Family_combo.get_family_data(uid, u_context)
    except KeyError as e:
        return redirect(url_for('virhesivu', code=1, text=str(e)))

    stk_logger(u_context, "-> bp.scene.routes.show_family_page")
    if results['status']:
        return redirect(url_for('virhesivu', code=1, text=results['statustext']))
    return render_template("/scene/family.html",  menuno=3, family=results['item'],
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
        reader = FamilyReader(dbreader, u_context) 

        results = reader.get_person_families(uuid)

        if results.get('status') == Status.NOT_FOUND:
            return jsonify({"member":uuid, "records":[],
                            "statusText":_('No families'),
                            "status":Status.NOT_FOUND})        

        items = results['items']
        res_dict = {'records': items, 
                    "member": uuid, 
                    'statusText': f'Löytyi {len(items)} perhettä',
                    'translations':{'family': _('Family'), 
                                    'children': _('Children')}
                    }
        response = json.dumps(res_dict, cls=StkEncoder)

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

    reader = PlaceReader(dbreader, u_context) 

    # The list has Place objects, which include also the lists of
    # nearest upper and lower Places as place[i].upper[] and place[i].lower[]

    results = reader.get_list()

    elapsed = time.time() - t0
    stk_logger(u_context, f"-> bp.scene.routes.show_places n={len(results['items'])} e={elapsed:.3f}")
    return render_template("/scene/places.html", places=results['items'], 
                           menuno=4, user_context=u_context, elapsed=elapsed)


@bp.route('/scene/location/uuid=<locid>')
@login_required
@roles_accepted('guest', 'research', 'audit', 'admin')
def show_place(locid):
    """ Home page for a Place, shows events and place hierarchy.
    """
    t0 = time.time()
    try:
        u_context = UserContext(user_session, current_user, request)
        reader = PlaceReader(dbreader, u_context) 
    
        results = reader.get_with_events(locid)

        if results['status'] == Status.NOT_FOUND:
            return redirect(url_for('virhesivu', code=1, text=f'Ei löytynyt yhtään'))
        if results['status'] != Status.OK:
            return redirect(url_for('virhesivu', code=1, text=f'Virhetilanne'))

    except KeyError as e:
        traceback.print_exc()
        return redirect(url_for('virhesivu', code=1, text=str(e)))

    stk_logger(u_context, f"-> bp.scene.routes.show_place n={len(results['events'])}")
    return render_template("/scene/place_events.html", 
                           place=results['place'], 
                           pl_hierarchy=results['hierarchy'],
                           events=results['events'],
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

    reader = SourceReader(dbreader, u_context) 
    if series:
        u_context.series = series
    try:
        results = reader.get_source_list()
        if results['status'] == Status.NOT_FOUND:
            return redirect(url_for('virhesivu', code=1, text=f'Ei löytynyt yhtään'))
        if results['status'] != Status.OK:
            return redirect(url_for('virhesivu', code=1, text=f'Virhetilanne'))
    except KeyError as e:
        return redirect(url_for('virhesivu', code=1, text=str(e)))
    series = u_context.series if u_context.series else "all"
    stk_logger(u_context, f"-> bp.scene.routes.show_sources/{series} n={len(results['items'])}")
    return render_template("/scene/sources.html", sources=results['items'], 
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
        reader = SourceReader(dbreader, u_context) 
    
        results = reader.get_source_with_references(uuid, u_context)
        
        if results['status'] == Status.NOT_FOUND:
            msg = results.get('statustext', _('No objects found'))
            return redirect(url_for('virhesivu', code=1, text=msg))
        if results['status'] != Status.OK:
            msg = results.get('statustext', _('Error'))
            return redirect(url_for('virhesivu', code=1, text=msg))

    except KeyError as e:
        return redirect(url_for('virhesivu', code=1, text=str(e)))
    stk_logger(u_context, f"-> bp.scene.routes.show_source_page n={len(results['citations'])}")
#     for c in results.citations:
#         for i in c.citators:
#             if i.id[0] == "F":  print(f'{c} – family {i} {i.clearname}')
#             else:               print(f'{c} – person {i} {i.sortname}')
    return render_template("/scene/source_events.html", source=results['item'],
                           citations=results['citations'], user_context=u_context)

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
    try:
        medias = Media.read_my_media_list(u_context, 20)

    except KeyError as e:
        return redirect(url_for('virhesivu', code=1, text=str(e)))
    stk_logger(u_context, f"-> bp.scene.media.show_medias fw n={len(medias)}")
    return render_template("/scene/medias.html", medias=medias, 
                           user_context=u_context, elapsed=time.time()-t0)

@bp.route('/scene/media', methods=['GET'])
@login_required
@roles_accepted('guest', 'research', 'audit', 'admin')
def show_media(uid=None):
    """ 
        One Media
    """
    uid = request.args.get('uuid', uid)
    u_context = UserContext(user_session, current_user, request)
    if not uid:
        return redirect(url_for('virhesivu', code=1, text="Missing Media key"))
    
    try:
        medium = Media.get_one(uid)
        fullname, mimetype = media.get_fullname(medium.uuid)
        if mimetype == "application/pdf":
            size = 0
        else:
            size = media.get_image_size(fullname)
    except KeyError as e:
        return redirect(url_for('virhesivu', code=1, text=str(e)))

    stk_logger(u_context, f"-> bp.scene.routes.show_media n={len(medium.ref)}")
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
        
