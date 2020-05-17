'''
Created on 12.8.2018

@author: jm
'''
import logging 
import io
#import os
import shareds
import os
logger = logging.getLogger('stkserver')
import time
from datetime import datetime

from flask import send_file, Response, jsonify
from flask import render_template, request, redirect, url_for, flash, session as user_session
from flask_security import current_user, login_required, roles_accepted
#from flask_babelex import _

from ui.user_context import UserContext
from bl.place import PlaceReader
from bl.source import SourceReader
from bl.family import FamilyReader

from . import bp
from bp.scene.scene_reader import get_person_full_data
from bp.scene.models import media
from models.gen.family_combo import Family_combo
#from models.gen.source import Source
from models.gen.media import Media

from models.datareader import read_persons_with_events
#from models.datareader import get_person_data_by_id # -- vanhempi versio ---
from models.datareader import get_event_participants
#from models.datareader import get_place_with_events
#from models.datareader import get_source_with_events

from pe.neo4j.read_driver import Neo4jReadDriver
from pe.db_reader import DBreader

# Narrative start page

@bp.route('/scene',  methods=['GET', 'POST'])
def scene():
    """ Home page for scene narrative pages ('kertova') for anonymous. """    
    print(f"--- {request}")
    print(f"--- {user_session}")
    u_context = UserContext(user_session, current_user, request)
    u_context.set_scope_from_request(request, 'person_scope')
    logger.info(f"-> bp.scene.routes.scene '{u_context.scope[0]}'")
    return render_template('/start/index_scene.html')


# ------------------------- Menu 1: Person search ------------------------------

@bp.route('/scene/persons', methods=['POST', 'GET'])
def show_person_list(selection=None):
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
            logger.error("iError {} in show_person_list".format(e))
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
            theme='-'
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
    #print(f'--> bp.scene.routes.show_person_list shows {len(persons_out)}/{len(persons)} persons')
    logger.info("-> bp.scene.routes.show_person_list"
                f" {u_context.owner_or_common()} {request.method} {theme} n={len(persons_out)}/{len(persons)}")

    return render_template("/scene/persons.html", persons=persons_out,
                           user_context=u_context, num_hidden=hidden, 
                           menuno=0, rule=keys, elapsed=time.time()-t0)

@bp.route('/scene/persons/ref=<string:refname>')
@bp.route('/scene/persons/ref=<string:refname>/<opt>')
@login_required
def show_persons_by_refname(refname, opt=""):
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
    persons = read_persons_with_events(keys, args=args)
    logger.info("-> bp.scene.routes.show_persons_by_refname")
    return render_template("/scene/persons.html", persons=persons, menuno=1, 
                           user_context=u_context, order=order, rule=keys)

@bp.route('/scene/persons/all/<string:opt>')
@bp.route('/scene/persons/all/')
#     @login_required
def show_all_persons_list(opt=''):
    """ List all persons for menu(1)    OLD MODEL WITHOUT User selection

        Linked from admin/refnames only

        The string opt may include keys 'ref', 'sn', 'pn' in arbitary order
        with no delimiters. You may write 'refsn', 'ref:sn' 'sn-ref' etc.

        TODO Should have restriction by owner's UserProfile 
    """
    logger.warning("#TODO: fix material selevtion or remove action show_all_persons_list")

    t0 = time.time()
    u_context = UserContext(user_session, current_user, request)
    keys = ('all',)
    ref = ('ref' in opt)
    if 'fn' in opt: order = 1   # firstname
    elif 'pn' in opt: order = 2 # firstname
    else: order = 0             # surname
    args = {'ref': ref, 'order': order}
    if current_user.is_authenticated:
        args['user'] = current_user.username
    persons = read_persons_with_events(keys, args=args) #user=user, take_refnames=ref, order=order)
    logger.info("-> bp.scene.routes.show_all_persons_list")
    return render_template("/scene/persons.html", persons=persons, menuno=1, 
                           user_context=u_context, order=order,
                           rule=keys, elapsed=time.time()-t0)



# -------------------------- Menu 12 Persons by user ---------------------------

@bp.route('/scene/persons_all/')
@login_required
@roles_accepted('guest', 'research', 'audit', 'admin')
def show_persons_all():
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

    t0 = time.time()
    dbdriver = Neo4jReadDriver(shareds.driver)
    db = DBreader(dbdriver, u_context)
    results = db.get_person_list()
    elapsed = time.time() - t0

    hidden = f" hide={results.num_hidden}" if results.num_hidden > 0 else ""
    logger.info("-> bp.scene.routes.show_persons_all"
                f" kind={u_context.owner_or_common()}"
                f" got={len(results.items)}{hidden}"
                f" e={elapsed:.4f}")
    print(f"Got {len(results.items)} persons"
          f" with {results.num_hidden} hidden"
          f" and {results.error} errors"
          f" in {elapsed:.4f}s")
    return render_template("/scene/persons_list.html", persons=results.items,
                           num_hidden=results.num_hidden,
                           user_context=u_context,
                           menuno=12, elapsed=elapsed)


@bp.route('/scene/person/<int:uid>')
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
#     logger.info("-> bp.scene.routes.show_v2")
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
@roles_accepted('member', 'gedcom', 'research', 'audit', 'admin', 'guest')
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

    # v3 Person page
    person, objs, jscode = get_person_full_data(uid, u_context.user, u_context.use_common())
    if not person:
        return redirect(url_for('virhesivu', code=2, text="Ei oikeutta katsoa tätä henkilöä"))
    logger.info(f"-> bp.scene.routes.show_person {u_context.owner_or_common()} obj={len(objs)}")

    #for ref in person.media_ref: print(f'media ref {ref}')
    last_year_allowed = datetime.now().year - shareds.PRIVACY_LIMIT
    return render_template("/scene/person.html", person=person, obj=objs, 
                           jscode=jscode, menuno=12, debug=dbg, root=person.root,
                           last_year_allowed=last_year_allowed, elapsed=time.time()-t0,
                           user_context=u_context)


@bp.route('/scene/person/uuid=<pid>')
@bp.route('/scene/person=<int:pid>')
#     @login_required
def obsolete_show_person_v1(pid):
    """ Full homepage for a Person in database (v1 versio).

        The pid may be 1) an uuid or 2) an uniq_id
    """
    return 'Obsolete: show_person_v1<br><a href="javascript:history.back()">Go Back</a>'
#     t0 = time.time()
#     try:
#         person, events, photos, citations, families = get_person_data_by_id(pid)
#         for f in families:
#             print ("{} in Family {} / {}".format(f.role, f.uniq_id, f.id))
#             if f.mother:
#                 print("  Mother: {} / {} s. {}".\
#                       format(f.mother.uniq_id, f.mother.id, f.mother.birth_date))
#             if f.father:
#                 print("  Father:  {} / {} s. {}".\
#                       format(f.father.uniq_id, f.father.id, f.father.birth_date))
#             for c in f.children:
#                 print("    Child ({}): {} / {} s. {}".\
#                       format(c.sex_str(), c.uniq_id, c.id, c.birth_date))
#     except KeyError as e:
#         return redirect(url_for('virhesivu', code=2, text=str(e)))
#     logger.info("-> bp.scene.routes.show_person_v1")
#     return render_template("/scene/person_v1.html", person=person, events=events, 
#                            photos=photos, citations=citations, families=families, 
#                            elapsed=time.time()-t0)


@bp.route('/scene/event/<int:uniq_id>')
def show_event(uniq_id):
    """ Table of a (baptism) Event persons.

        Kastetapahtuman tietojen näyttäminen ruudulla
        
        Derived from bp.tools.routes.show_baptism_data()
    """
    event, persons = get_event_participants(uniq_id)
    logger.info(f"-> bp.scene.routes.show_event n={len(persons)}")
    return render_template("/scene/event.html",
                           event=event, persons=persons)


# ------------------------------ Menu 3: Families --------------------------------

@bp.route('/scene/families')
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
    count = request.args.get('c', 100, type=int)
    t0 = time.time()
        
    # 'families' has Family objects
    families = Family_combo.get_families(o_context=u_context, opt=opt, limit=count)

    logger.info("-> bp.scene.routes.show_families "
                f"{u_context.owner_or_common()} by={opt} n={len(families)}")
    return render_template("/scene/families.html", families=families, 
                           user_context=u_context, elapsed=time.time()-t0)

# @bp.route('/scene/family=<int:fid>')
# def show_family_page(fid):
#     """ Home page for a Family.    OBSOLETE: use show_family
#         fid = id(Family)
#     """

@bp.route('/scene/family', methods=['GET'])
def show_family_page(uid=None):
    """ One Family.
    """
    uid = request.args.get('uuid', uid)
    if not uid:
        return redirect(url_for('virhesivu', code=1, text="Missing Family key"))
    t0 = time.time()

    try:
        u_context = UserContext(user_session, current_user, request)
        dbdriver = Neo4jReadDriver(shareds.driver)
        reader = FamilyReader(dbdriver, u_context) 
    
        results = reader.get_family_data(uid)
        #family = Family_combo.get_family_data(uid, u_context)
    except KeyError as e:
        return redirect(url_for('virhesivu', code=1, text=str(e)))

    logger.info("-> bp.scene.routes.show_family_page")
    if results['status']:
        return redirect(url_for('virhesivu', code=1, text=results['statustext']))
    return render_template("/scene/family.html",  menuno=3, family=results['item'],
                           user_context=u_context, elapsed=time.time()-t0)


@bp.route('/scene/json/families', methods=['POST','GET'])
def json_get_person_families(uuid=None):
    """ Get all families for a Person as json array.

        The first element is childhood family or None, 
        the others are marriages in time order.
    """
    import json
    try:
        if not uuid:
            uuid = json.loads(request.data)['uuid']
            #uuid = request.args.get('uuid', None)
        #print(f'got uuid: {uuid}')
        if not uuid:
            return jsonify({"records":[], "statusText":"Missing Family key"})

        u_context = UserContext(user_session, current_user, request)
        dbdriver = Neo4jReadDriver(shareds.driver)
        reader = FamilyReader(dbdriver, u_context) 
    
        results = reader.get_person_families(uuid)
        #family = Family_combo.get_family_data(uuid, u_context)

        if results.get('status') != 0:
            return jsonify({"records":[], "statusText":results.get('status')})
        res = []
        for family in results['items']:
            if not family:   # Missing childhood family
                res.append(None)
                continue

            fdict = {
                "rel_type":family.rel_type,
                "dates": family.dates.to_list(),
                "id":family.id,
                "uuid":family.uuid
            }
            parents = []
            if family.father:
                parent = {
                    "role":"father",
                    "sortname":family.father.sortname,
                    "uuid":family.father.uuid
                }
                if family.father.event_birth:
                    parent['dates'] = family.father.event_birth.dates.to_list()
                parents.append(parent)
            if family.mother:
                parent = {
                    "role":"mother",
                    "sortname":family.mother.sortname,
                    "uuid":family.mother.uuid
                }
                if family.mother.event_birth:
                    parent['dates'] = family.mother.event_birth.dates.to_list()
                parents.append(parent)
            fdict['parents'] = parents
        
            children = []
            for ch in family.children:
                child = {"sex":ch.sex, "sortname":ch.sortname, "uuid":ch.uuid}
                if ch.event_birth:
                    child['dates'] = ch.event_birth.dates.to_list()
                children.append(child)
            fdict["children"] = children

            events = []
            for ev in family.events:
                events.append({"type":ev.type, "id":ev.id, "uuid":ev.uuid})
            fdict["events"] = events
            res.append(fdict)

    except KeyError as e:
        return jsonify({"records":[], "statusText":str(e)})


    logger.info(f"-> bp.scene.routes.show_person_families_json")
    response = {'records':res, 'statusText':f'Löytyi {len(res)} perhettä (TESTING)'}
    print(json.dumps(response))
    #response.headers['Access-Control-Allow-Origin'] = '*'
    return jsonify(response) 


# @bp.route('/pop/family=<int:fid>')
# def show_family_popup(fid):
#     """ Small Family pop-up. EXPERIMENTAL
#     """
#     #TODO Create a pop-up window; Gen only fewer pieces of data
#     family = Family_combo.get_family_data(fid)
#     return render_template("/scene/family_pop.html", family=family)

# ------------------------------ Menu 4: Places --------------------------------

@bp.route('/scene/locations')
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
    u_context.count = request.args.get('c', 100, type=int)

    dbdriver = Neo4jReadDriver(shareds.driver)
    reader = PlaceReader(dbdriver, u_context) 

    # The list has Place objects, which include also the lists of
    # nearest upper and lower Places as place[i].upper[] and place[i].lower[]

    results = reader.get_list()
    #results = db.get_place_list()

#     for p in result.items:
#         print ("# {} ".format(p))
    logger.info("-> bp.scene.routes.show_places "
               f"{u_context.owner_or_common()} n={len(results.items)}")
    return render_template("/scene/places.html", places=results.items, menuno=4,
                           user_context=u_context, elapsed=time.time()-t0)


@bp.route('/scene/location/uuid=<locid>')
def show_place(locid):
    """ Home page for a Place, shows events and place hierarchy.
    """
    try:
        u_context = UserContext(user_session, current_user, request)
        dbdriver = Neo4jReadDriver(shareds.driver)
        reader = PlaceReader(dbdriver, u_context) 
    
        results = reader.get_with_events(locid)

    except KeyError as e:
        import traceback
        traceback.print_exc()
        return redirect(url_for('virhesivu', code=1, text=str(e)))
#     for p in hierarchy:         print (f"# {p} ")
#     for e in events:            print (f"# {e} {e.description}")
#     for u in place.notes:       print (f"# {u} ")
    logger.info(f"-> bp.scene.routes.show_place {u_context.owner_or_common()} n={len(results.events)}")
    return render_template("/scene/place_events.html", place=results.items, 
                           pl_hierarchy=results.hierarchy,
                           user_context=u_context, events=results.events)

# ------------------------------ Menu 5: Sources --------------------------------

@bp.route('/scene/sources')
@bp.route('/scene/sources/<series>')
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
    # Set context by owner and the data selections
    u_context = UserContext(user_session, current_user, request)
    # Which range of data is shown
    u_context.set_scope_from_request(request, 'source_scope')
    u_context.count = request.args.get('c', 100, type=int)

    dbdriver = Neo4jReadDriver(shareds.driver)
    reader = SourceReader(dbdriver, u_context) 
    if series:
        u_context.series = series
    try:
        results = reader.get_source_list()
    except KeyError as e:
        return redirect(url_for('virhesivu', code=1, text=str(e)))
    logger.info(f"-> bp.scene.routes.show_sources by={u_context.series} c={len(results.items)}")
    return render_template("/scene/sources.html", sources=results.items, 
                           user_context=u_context)


@bp.route('/scene/source', methods=['GET'])
#@bp.route('/scene/source=<string:sourceid>')
def show_source_page(sourceid=None):
    """ Home page for a Source with referring Event and Person data
    """
    uuid = request.args.get('uuid', sourceid)
    if not uuid:
        return redirect(url_for('virhesivu', code=1, text="Missing Source key"))
    u_context = UserContext(user_session, current_user, request)
    try:
        dbdriver = Neo4jReadDriver(shareds.driver)
        reader = SourceReader(dbdriver, u_context) 
    
        results = reader.get_source_with_references(uuid, u_context)
        #results = db.get_source_with_references(uuid, u_context)
        #source, citations = get_source_with_events(sourceid)
    except KeyError as e:
        return redirect(url_for('virhesivu', code=1, text=str(e)))
    logger.info(f"-> bp.scene.routes.show_source_page n={len(results.citations)}")
#     for c in results.citations:
#         for i in c.citators:
#             if i.id[0] == "F":  print(f'{c} – family {i} {i.clearname}')
#             else:               print(f'{c} – person {i} {i.sortname}')
    return render_template("/scene/source_events.html", source=results.items,
                           citations=results.citations, user_context=u_context)

# ------------------------------ Menu 6: Media --------------------------------

@bp.route('/scene/medias')
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
    logger.info(f"-> bp.scene.media.show_medias: {u_context.owner_or_common()} fw n={len(medias)}")
    return render_template("/scene/medias.html", medias=medias, 
                           user_context=u_context, elapsed=time.time()-t0)

@bp.route('/scene/media', methods=['GET'])
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
        fullname, _mimetype = media.get_fullname(medium.uuid)
        size = media.get_image_size(fullname)
    except KeyError as e:
        return redirect(url_for('virhesivu', code=1, text=str(e)))

    logger.info(f"-> bp.scene.routes.show_media n={len(medium.ref)}")
    return render_template("/scene/media.html", media=medium, size=size,
                           user_context=u_context, menuno=6)

# ----------- Access media file ---------------

@bp.route('/scene/media/<fname>')
def fetch_media(fname):
    """ Fetch media file to display full screen.
    
        Example:
        http://127.0.0.1:5000/scene/media/kuva2?id=63995268bd2348aeb6c70b5259f6743f&crop=0,21,100,91&full=1

        Arguments:
            id    uuid of Media
            crop  pixel coordinates as "left,upper,right,lower" %
            full  "1" = show full size, "0" thumbnail size (default)
    
        #TODO. Assumes jpg. Accept other file formats
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
        ret = send_file(os.path.join('static', 'noone.jpg'), mimetype=mimetype)
        logger.debug(f"-> bp.scene.routes.fetch_media none")
        return ret

@bp.route('/scene/thumbnail')
def fetch_thumbnail():
    """ Fetch thumbnail file to display
    """
    uuid = request.args.get("id")
    crop = request.args.get("crop")
    if crop == "None":
        crop = None
    logger.debug(f"-> bp.scene.routes.fetch_thumbnail ok")
    mimetype='image/jpg'
    thumbname = "(no file)"
    try:
        thumbname = media.get_thumbname(uuid, crop)
        #print(thumbname)
        ret = send_file(thumbname, mimetype=mimetype)
        return ret
    except FileNotFoundError:
        # Show default image
        ret = send_file(os.path.join('static', 'noone.jpg'), mimetype=mimetype)
        logger.debug(f"-> bp.scene.routes.fetch_thumbnail none")
        return ret
        
