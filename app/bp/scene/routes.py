'''
Created on 12.8.2018

@author: jm
'''
import logging 
#import os
from flask import send_file
from bp.scene.models import media
logger = logging.getLogger('stkserver')
import time

from flask import render_template, request, redirect, url_for, flash, session as user_session
from flask_security import current_user, login_required, roles_accepted
#from flask_babelex import _

from . import bp
from bp.scene.scene_reader import get_person_full_data
from bp.scene.scene_reader import get_a_person_for_display_apoc
from models.gen.person_combo import Person_combo
from models.gen.family_combo import Family_combo
from models.gen.place_combo import Place_combo
from models.gen.source import Source

from models.datareader import read_persons_with_events
from models.datareader import get_person_data_by_id # -- vanhempi versio ---
from models.datareader import get_event_participants
from models.datareader import get_place_with_events
from models.datareader import get_source_with_events
from models.owner import OwnerFilter

# Narrative start page
@bp.route('/scene',  methods=['GET', 'POST'])
def scene():
    """ Home page for scene narrative pages ('kertova') for anonymous. """    
    print(f"--- {request}")
    print(f"--- {user_session}")
    my_filter = OwnerFilter(user_session, current_user, request)
    my_filter.set_scope_from_request(request, 'person_scope')
    logger.info(f"-> bp.scene.routes.scene '{my_filter.scope[0]}'")
    return render_template('/start/index_scene.html')


# ------------------------- Menu 1: Person search ------------------------------

@bp.route('/scene/persons', methods=['POST', 'GET'])
def show_person_list(selection=None):
    """ Show list of selected Persons for menu(0). """
    t0 = time.time()
    if request.method == 'POST':
        try:
            # Selection from search form
            name = request.form['name']
            rule = request.form['rule']
            keys = (rule, name)
            logger.info(f"-> bp.scene.routes.show_person_list POST {keys}")
            persons = read_persons_with_events(keys)
            return render_template("/scene/persons.html", persons=persons, menuno=0,
                                   name=name, rule=keys, elapsed=time.time()-t0)
        except Exception as e:
            logger.info("iError {} in show_person_list".format(e))
            flash("Valitse haettava nimi ja tyyppi", category='warning')
    else:
        # the code below is executed if the request method
        # was GET (no search name given) or the credentials were invalid
        persons = []
        if selection:
            # Use selection filter
            keys = selection.split('=')
        else:
            keys = ('surname',)
        persons = read_persons_with_events(keys)
        logger.info(f"-> bp.scene.routes.show_person_list GET {keys}")

    return render_template("/scene/persons.html", persons=persons,
                           menuno=0, rule=keys, elapsed=time.time()-t0)

@bp.route('/scene/persons/ref=<string:refname>')
@bp.route('/scene/persons/ref=<string:refname>/<opt>')
@login_required
def show_persons_by_refname(refname, opt=""):
    """ List persons by refname.
    """
    keys = ('refname', refname)
    if current_user.is_authenticated:
        user=current_user.username
    else:
        user=None
    ref = ('ref' in opt)
    order = 0
    persons = read_persons_with_events(keys, user=user, take_refnames=ref, order=order)
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
    if current_user.is_authenticated:
        user=current_user.username
    else:
        user=None
    ref = ('ref' in opt)
    if 'fn' in opt: order = 1   # firstname
    elif 'pn' in opt: order = 2 # firstname
    else: order = 0             # surname
    persons = read_persons_with_events(keys, user=user, take_refnames=ref, order=order)
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

        The position in persons list is defined by -
           1. by attribute fw, if defined (the forward arrow or from seach field)
           2. by session next_person[1], if defined (the page last visited)
              #TODO: next_person[0] is not in use, yet (backward arrow)
           3. otherwise "" (beginning)
    """
    print(f"--- {request}")
    print(f"--- {user_session}")
    # Set filter by owner and the data selection
    my_filter = OwnerFilter(user_session, current_user, request)
    # Which range of data is shown
    my_filter.set_scope_from_request(request, 'person_scope')
    # About how mamy items to read
    count = int(request.args.get('c', 100))

    logger.info(f"-> bp.scene.routes.show_persons_all: forward from '{my_filter.scope[0]}'")
    t0 = time.time()
    persons = Person_combo.read_my_persons_list(o_filter=my_filter, limit=count)

    return render_template("/scene/persons_list.html", persons=persons, menuno=12, 
                           owner_filter=my_filter, elapsed=time.time()-t0)


@bp.route('/scene/person/<int:uid>')
#     @login_required
@roles_accepted('member', 'gedcom', 'research', 'audit', 'admin')
def show_person_v2(uid=None):
    """ One Person with all connected nodes - version 3 with apoc
    """
    t0 = time.time()
    if current_user.is_authenticated:
        user=current_user.username
    else:
        user=None
    # v2 Person page data
    person, objs, marks = get_a_person_for_display_apoc(uid, user)
    logger.info("-> bp.scene.routes.show_v2")
    if not person:
        return redirect(url_for('virhesivu', code=2, text="Ei oikeutta katsoa tätä henkilöä"))
    #print (f"Current language {current_user.language}")
    from bp.scene.models.media import get_thumbname
    for i in person.media_ref:
        print(get_thumbname(objs[i].uuid))
    return render_template("/scene/person_v2.html", person=person, obj=objs, 
                           marks=marks, menuno=12, elapsed=time.time()-t0)


@bp.route('/scene/person', methods=['GET'])
#     @login_required
@roles_accepted('member', 'gedcom', 'research', 'audit', 'admin', 'guest')
def     show_person_v3(uid=None):
    """ One Person with all connected nodes - NEW version 3.

        Arguments:
        - uuid=     persons uuid
        - debug=1   optinal for javascript tests
    """
    t0 = time.time()
    uid = request.args.get('uuid', uid)
    if not uid:
        return redirect(url_for('virhesivu', code=1, text="Missing Person key"))

    dbg = request.args.get('debug', None)
    print(dbg)
    if current_user.is_authenticated:
        user=current_user.username
    else:
        user=None
    logger.info("-> bp.scene.routes.show_person_v3")
    
    # v3 Person page
    person, objs, jscode = get_person_full_data(uid, user)
    if not person:
        return redirect(url_for('virhesivu', code=2, text="Ei oikeutta katsoa tätä henkilöä"))

    return render_template("/scene/person.html", person=person, obj=objs, 
                           jscode=jscode, menuno=12, debug=dbg, elapsed=time.time()-t0)


@bp.route('/scene/person/uuid=<pid>')
@bp.route('/scene/person=<int:pid>')
#     @login_required
def show_person_v1(pid):
    """ Full homepage for a Person in database (v1 versio).

        The pid may be 1) an uuid or 2) an uniq_id
    """
    t0 = time.time()
    try:
        person, events, photos, citations, families = get_person_data_by_id(pid)
        for f in families:
            print ("{} in Family {} / {}".format(f.role, f.uniq_id, f.id))
            if f.mother:
                print("  Mother: {} / {} s. {}".\
                      format(f.mother.uniq_id, f.mother.id, f.mother.birth_date))
            if f.father:
                print("  Father:  {} / {} s. {}".\
                      format(f.father.uniq_id, f.father.id, f.father.birth_date))
            for c in f.children:
                print("    Child ({}): {} / {} s. {}".\
                      format(c.sex_str(), c.uniq_id, c.id, c.birth_date))
    except KeyError as e:
        return redirect(url_for('virhesivu', code=2, text=str(e)))
    logger.info("-> bp.scene.routes.show_person_v1")
    return render_template("/scene/person_v1.html", person=person, events=events, 
                           photos=photos, citations=citations, families=families, 
                           elapsed=time.time()-t0)


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
    # Set filter by owner and the data selection
    my_filter = OwnerFilter(user_session, current_user, request)
    # Which range of data is shown
    my_filter.set_scope_from_request(request, 'person_scope')
    opt = request.args.get('o', 'father', type=str)
    count = request.args.get('c', 100, type=int)
    t0 = time.time()
        
    # 'families' has Family objects
    families = Family_combo.get_families(o_filter=my_filter, opt=opt, limit=count)

    logger.info("-> bp.scene.routes.show_families")
    return render_template("/scene/families.html", families=families, 
                           owner_filter=my_filter, elapsed=time.time()-t0)

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

@bp.route('/pop/family=<int:fid>')
def show_family_popup(fid):
    """ Small Family pop-up. EXPERIMENTAL
    """
    #TODO Create a pop-up window; Gen only fewer pieces of data
    family = Family_combo.get_family_data(fid)
    return render_template("/scene/family_pop.html", family=family)

# ------------------------------ Menu 4: Places --------------------------------

@bp.route('/scene/locations')
def show_places():
    """ List of Places for menu(4)
    """
    t0 = time.time()
    print(f"--- {request}")
    print(f"--- {user_session}")
    # Set filter by owner and the data selection
    my_filter = OwnerFilter(user_session, current_user, request)
    # Which range of data is shown
    my_filter.set_scope_from_request(request, 'person_scope')
    count = request.args.get('c', 100, type=int)
    try:
        # 'locations' has Place objects, which include also the lists of
        # nearest upper and lower Places as place[i].upper[] and place[i].lower[]
#        locations = Place_combo.get_place_hierarchy()
        locations = Place_combo.get_my_place_hierarchy(o_filter=my_filter, limit=count)
    except KeyError as e:
        return redirect(url_for('virhesivu', code=1, text=str(e)))
#     for p in locations:
#         print ("# {} ".format(p))
    logger.info(f"-> bp.scene.routes.show_places: forward from '{my_filter.scope[0]}'")
    return render_template("/scene/places.html", locations=locations, 
                           owner_filter=my_filter, elapsed=time.time()-t0)


@bp.route('/scene/location/uuid=<locid>')
@bp.route('/scene/location=<int:locid>')
def show_place_page(locid):
    """ Home page for a Place, shows events and place hierarchy
        locid = id(Place)
    """
    try:
        # List 'place_list' has Place objects with 'parent' field pointing to
        # upper place in hierarcy. Events
        place, place_list, events = get_place_with_events(locid)
    except KeyError as e:
        import traceback
        traceback.print_exc()
        return redirect(url_for('virhesivu', code=1, text=str(e)))
#     for p in place_list:
#         print ("# {} ".format(p))
#     for u in place.notes:
#         print ("# {} ".format(u))
    logger.info("-> bp.scene.routes.show_place_page")
    return render_template("/scene/place_events.html", locid=locid, place=place, 
                           events=events, locations=place_list)

# ------------------------------ Menu 5: Sources --------------------------------

@bp.route('/scene/sources')
@bp.route('/scene/sources/<theme>')
def show_sources(theme=None):
    """ Lähdeluettelon näyttäminen ruudulla for menu(5)
    
        Todo: Examples?
            /scene/sources --> birth; shorter list?
            /scene/sources/all    <-- now no theme
            /scene/sources/birth
            /scene/sources/wedding?year1=1800%year2=1850 <-- todo

    """
    if theme:
        # Todo: Possible year filter? Needs pre-calculated varibles?
        year1 = request.args.get('year1', None)
        year2 = request.args.get('year2', None)
        filt = (theme, year1, year2)
    else:
        filt=None
    try:
        sources, title = Source.get_source_list(filt)
    except KeyError as e:
        return redirect(url_for('virhesivu', code=1, text=str(e)))
    logger.info("-> bp.scene.routes.show_sources")
    return render_template("/scene/sources.html", sources=sources, title=title)


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

# ------------------------------ Media --------------------------------

@bp.route('/scene/media/<fname>')
def fetch_media(fname):
    """ Fetch media file, assumes jpg, fix later...
    """
    uuid = request.args.get("id")
    fullname, mimetype = media.get_fullname(uuid)
    logger.info("-> bp.scene.routes.fetch_media")
    return send_file(fullname, mimetype=mimetype)        

@bp.route('/scene/thumbnail')
def fetch_thumbnail():
    """ Fetch thumbnail
    """
    uuid = request.args.get("id")
    thumbname = media.get_thumbname(uuid)
    print(thumbname)
    mimetype='image/jpg'
    logger.info("-> bp.scene.routes.fetch_thumbnail")
    return send_file(thumbname, mimetype=mimetype)
