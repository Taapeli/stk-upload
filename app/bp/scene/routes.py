'''
Created on 12.8.2018

@author: jm
'''
import logging 
import io
#import os
from flask import send_file, Response
from bp.scene.models import media
import shareds
logger = logging.getLogger('stkserver')
import time
from datetime import datetime

from flask import render_template, request, redirect, url_for, flash, session as user_session
from flask_security import current_user, login_required, roles_accepted
#from flask_babelex import _

from ui.user_context import UserContext
from bl.place import PlaceBl

from . import bp
from bp.scene.scene_reader import get_person_full_data
#from bp.scene.scene_reader import get_a_person_for_display_apoc
#from models.gen.person_combo import Person_combo
from models.gen.family_combo import Family_combo
#from models.gen.place_combo import Place_combo
from models.gen.source import Source
from models.gen.media import Media

from models.datareader import read_persons_with_events
#from models.datareader import get_person_data_by_id # -- vanhempi versio ---
from models.datareader import get_event_participants
from models.datareader import get_place_with_events
from models.datareader import get_source_with_events

from pe.neo4j.reader import Neo4jDriver
from pe.db_reader import DBreader

LAST_YEAR_ALLOWED=datetime.now().year - 50

# Narrative start page

@bp.route('/scene',  methods=['GET', 'POST'])
def scene():
    """ Home page for scene narrative pages ('kertova') for anonymous. """    
    print(f"--- {request}")
    print(f"--- {user_session}")
    my_context = UserContext(user_session, current_user, request)
    my_context.set_scope_from_request(request, 'person_scope')
    logger.info(f"-> bp.scene.routes.scene '{my_context.scope[0]}'")
    return render_template('/start/index_scene.html')


# ------------------------- Menu 1: Person search ------------------------------

@bp.route('/scene/persons', methods=['POST', 'GET'])
def show_person_list(selection=None):
    """ Show list of selected Persons for menu(0). """
    t0 = time.time()
    my_context = UserContext(user_session, current_user, request)
    my_context.set_scope_from_request(request, 'person_scope')
    if request.method == 'POST':
        try:
            # Selection from search form
            name = request.form['name']
            rule = request.form['rule']
            keys = (rule, name)
            logger.info(f"-> bp.scene.routes.show_person_list POST {keys}")
            persons = read_persons_with_events(keys)
            if my_context.use_common():  
                persons2 = [p for p in persons if not p.too_new]
            else:
                persons2 = persons
            return render_template("/scene/persons.html", persons=persons2, menuno=0,
                                   num_hidden=len(persons)-len(persons2), 
                                   name=name, rule=keys, 
                                   last_year_allowed=LAST_YEAR_ALLOWED, 
                                   elapsed=time.time()-t0)
        except Exception as e:
            logger.info("iError {} in show_person_list".format(e))
            flash("Valitse haettava nimi ja tyyppi", category='warning')
    else:
        # the code below is executed if the request method
        # was GET (no search name given) or the credentials were invalid
        persons = []
        if selection:
            # Use selection context
            keys = selection.split('=')
        else:
            keys = ('surname',)
        persons = read_persons_with_events(keys)
        logger.info(f"-> bp.scene.routes.show_person_list GET {keys}")

    if my_context.use_common():  
        persons2 = [p for p in persons if not p.too_new]
    else:
        persons2 = persons
    return render_template("/scene/persons.html", persons=persons2,
                           num_hidden=len(persons)-len(persons2), 
                           menuno=0, rule=keys, elapsed=time.time()-t0)

@bp.route('/scene/persons/ref=<string:refname>')
@bp.route('/scene/persons/ref=<string:refname>/<opt>')
@login_required
def show_persons_by_refname(refname, opt=""):
    """ List persons by refname for menu(0).
    """
    keys = ('refname', refname)
    ref = ('ref' in opt)
    order = 0
    args = {'ref': ref, 'order': order}
    if current_user.is_authenticated:
        args['user'] = current_user.username
    persons = read_persons_with_events(keys, args=args)
    logger.info("-> bp.scene.routes.show_persons_by_refname")
    return render_template("/scene/persons.html", persons=persons, menuno=1, 
                           order=order, rule=keys)

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
    t0 = time.time()
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
                           order=order,rule=keys, elapsed=time.time()-t0)



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
    u_context.privacy_limit = LAST_YEAR_ALLOWED

    logger.info("-> bp.scene.routes.show_persons_all: "
               f"{u_context.owner_str()} forward from '{u_context.scope[0]}'")
    t0 = time.time()

    dbdriver = Neo4jDriver(shareds.driver)
    db = DBreader(dbdriver, u_context) 
    
    results = db.person_list()
#         limit=count, start=None, include=["events"])
    print(f'Got {len(results.items)} persons with {results.num_hidden} hidden and {results.error} errors')
    return render_template("/scene/persons_list.html", persons=results.items,
                           num_hidden=results.num_hidden, 
                           user_context=u_context,
                           menuno=12, elapsed=time.time()-t0)


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
def     show_person(uid=None):
    """ One Person with all connected nodes - NEW version 3.

        Arguments:
        - uuid=     persons uuid
        - debug=1   optinal for javascript tests
    """
    t0 = time.time()
    uid = request.args.get('uuid', uid)
#     if not uid:
#         return redirect(url_for('virhesivu', code=1, text="Missing Person key"))

    dbg = request.args.get('debug', None)
    if current_user.is_authenticated:
        user=current_user.username
        ofilter = user_session.get('user_context',0)
        use_common = (ofilter == 1)
    else:
        user=None
    logger.info("-> bp.scene.routes.show_person")
    
    # v3 Person page
    person, objs, jscode = get_person_full_data(uid, user, use_common)
    if not person:
        return redirect(url_for('virhesivu', code=2, text="Ei oikeutta katsoa tätä henkilöä"))

    return render_template("/scene/person.html", person=person, obj=objs, 
                           jscode=jscode, menuno=12, debug=dbg, root=person.root,
                           last_year_allowed=LAST_YEAR_ALLOWED, elapsed=time.time()-t0)


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
    logger.info("-> bp.scene.routes.show_event")
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
    my_context = UserContext(user_session, current_user, request)
    # Which range of data is shown
    my_context.set_scope_from_request(request, 'person_scope')
    opt = request.args.get('o', 'father', type=str)
    count = request.args.get('c', 100, type=int)
    t0 = time.time()
        
    # 'families' has Family objects
    families = Family_combo.get_families(o_context=my_context, opt=opt, limit=count)

    logger.info("-> bp.scene.routes.show_families")
    return render_template("/scene/families.html", families=families, 
                           user_context=my_context, elapsed=time.time()-t0)

@bp.route('/scene/family=<int:fid>')
def show_family_page(fid):
    """ Home page for a Family.    OBSOLETE: use show_family

        fid = id(Family)
    """
    try:
        family = Family_combo.get_family_data(fid)
    except KeyError as e:
        return redirect(url_for('virhesivu', code=1, text=str(e)))

    logger.info("-> bp.scene.routes.show_family_page")
    return render_template("/scene/family.html", family=family, menuno=3)


@bp.route('/scene/family', methods=['GET'])
def show_family(uid=None):
    """ One Family.
    
    """
    
    uid = request.args.get('uuid', uid)
    if not uid:
        return redirect(url_for('virhesivu', code=1, text="Missing Family key"))
    
    try:
        family = Family_combo.get_family_data(uid)
    except KeyError as e:
        return redirect(url_for('virhesivu', code=1, text=str(e)))

    logger.info("-> bp.scene.routes.show_family")
    return render_template("/scene/family.html", family=family, menuno=3)

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


    dbdriver = Neo4jDriver(shareds.driver)
    db = DBreader(dbdriver, u_context) 

    # The list has Place objects, which include also the lists of
    # nearest upper and lower Places as place[i].upper[] and place[i].lower[]

    results = db.place_list()

#     for p in result.items:
#         print ("# {} ".format(p))
    logger.info(f"-> bp.scene.routes.show_places: forward from '{u_context.scope[0]}'")
    return render_template("/scene/places.html", places=results.items, menuno=4,
                           user_context=u_context, elapsed=time.time()-t0)


@bp.route('/scene/location/uuid=<locid>')
#@bp.route('/scene/location=<int:locid>')
def show_place_page(locid):
    """ Home page for a Place, shows events and place hierarchy.
    """
    try:
        # List 'place_list' has Place objects with 'parent' field pointing to
        # upper place in hierarcy. Events
        my_context = UserContext(user_session, current_user, request)
        my_context.set_scope_from_request(request, 'person_scope')
        #if my_context.use_common():
        #    events = [e for e in events if not e.person.too_new]
        place, place_list, events = get_place_with_events(locid)

    except KeyError as e:
        import traceback
        traceback.print_exc()
        return redirect(url_for('virhesivu', code=1, text=str(e)))
#     for p in place_list:        print (f"# {p} ")
#     for e in events:            print (f"# {e} {e.description}")
#     for u in place.notes:       print (f"# {u} ")
    logger.info("-> bp.scene.routes.show_place_page")
    return render_template("/scene/place_events.html", place=place, 
                           events=events, pl_hierarchy=place_list)

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
    my_context = UserContext(user_session, current_user, request)
#Todo: show by page
#     # Which range of data is shown
#     my_context.set_scope_from_request(request, 'source_scope')
#     # How many objects are shown?
#     count = int(request.args.get('c', 100))

    if series:
        my_context.series = series
    try:
        sources, title = Source.get_source_list(my_context)
    except KeyError as e:
        return redirect(url_for('virhesivu', code=1, text=str(e)))
    logger.info("-> bp.scene.routes.show_sources")
    return render_template("/scene/sources.html", sources=sources, title=title,
                           user_context=my_context)


@bp.route('/scene/source=<int:sourceid>')
def show_source_page(sourceid):
    """ Home page for a Source with referring Event and Person data
    """
    try:
        source, citations = get_source_with_events(sourceid)
    except KeyError as e:
        return redirect(url_for('virhesivu', code=1, text=str(e)))
    logger.info("-> bp.scene.routes.show_source_page")
    return render_template("/scene/source_events.html",
                           source=source, citations=citations)

# ------------------------------ Menu 6: Media --------------------------------

@bp.route('/scene/medias')
def show_medias():
    """ List of Medias for menu(5)
    """
    t0 = time.time()
    print(f"--- {request}")
    print(f"--- {user_session}")
    # Set context by owner and the data selections
    my_context = UserContext(user_session, current_user, request)
    # Which range of data is shown
    my_context.set_scope_from_request(request, 'media_scope')
    try:
        medias = Media.read_my_media_list(my_context, 20)

    except KeyError as e:
        return redirect(url_for('virhesivu', code=1, text=str(e)))
    logger.info(f"-> bp.scene.media.show_medias: forward from '{my_context.scope[0]}'")
    return render_template("/scene/medias.html", medias=medias, 
                           user_context=my_context, elapsed=time.time()-t0)

@bp.route('/scene/media', methods=['GET'])
def show_media(uid=None):
    """ 
        One Media
    """
    uid = request.args.get('uuid', uid)
    if not uid:
        return redirect(url_for('virhesivu', code=1, text="Missing Media key"))
    
    try:
        mediaobj = Media.get_one(uid)
        fullname, _mimetype = media.get_fullname(mediaobj.uuid)
        size = media.get_image_size(fullname)
    except KeyError as e:
        return redirect(url_for('virhesivu', code=1, text=str(e)))

    logger.info("-> bp.scene.routes.show_media")
    return render_template("/scene/media.html", media=mediaobj, size=size, menuno=6)


@bp.route('/scene/media/<fname>')
def fetch_media(fname):
    """ Fetch media file, full size of cropped. 
    
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
    if crop:
        # crop dimensions are diescribed as % of width and height
        image = media.get_cropped_image(fullname, crop, show_thumb)
        logger.info("-> bp.scene.routes.fetch_media cropped png")
        # Create a png image in memery and display it
        buffer = io.BytesIO()
        image.save(buffer, format="PNG")
        return Response(buffer.getvalue(), mimetype='image/png')
    else:
        logger.info("-> bp.scene.routes.fetch_media")
        return send_file(fullname, mimetype=mimetype)        

@bp.route('/scene/thumbnail')
def fetch_thumbnail():
    """ Fetch thumbnail
    """
    uuid = request.args.get("id")
    thumbname = media.get_thumbname(uuid)
    #print(thumbname)
    mimetype='image/jpg'
    logger.info("-> bp.scene.routes.fetch_thumbnail")
    try:
        ret = send_file(thumbname, mimetype=mimetype)
        return ret
    except FileNotFoundError:
        # Show default image
        ret = send_file(url_for('static', filename='noone.jpg'), mimetype=mimetype)
        logger.warning(f"-> bp.scene.routes.fetch_thumbnail: missing {thumbname}")
        return ret
        
