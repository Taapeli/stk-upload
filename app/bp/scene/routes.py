'''
Created on 12.8.2018

@author: jm
'''
import logging 
from models.gen.person_combo import Person_combo
logger = logging.getLogger('stkserver')
import time

from flask import render_template, request, redirect, url_for, flash
from flask_security import current_user, login_required

from . import bp
from bp.scene.data_reader import get_a_person_for_display_apoc # get_a_person_for_display, get_person_for_display, get_person_data_by_id
from models.datareader import read_persons_with_events
from models.datareader import get_person_data_by_id # -- vanhempi versio ---
from models.datareader import get_place_with_events
from models.datareader import get_source_with_events
#from models.gen.family import Family_for_template
from models.gen.place import Place
from models.gen.source import Source
#from models.gen.citation import Citation


@bp.route('/scene/persons/restricted')
def show_persons_restricted(selection=None):
    """ Show list of selected Persons, limited information 
        for non-logged users from login_user.html """
    if not current_user.is_authenticated:
        # Tässä aseta sisäänkirjautumattoman käyttäjän rajoittavat parametrit.
        # Vaihtoehtoisesti kutsu toista metodia.
        keys = ('all',)
    persons = read_persons_with_events(keys)
    return render_template("/scene/persons.html", persons=persons, 
                           menuno=1, rule=keys)

# ------------------------- Menu 0: Person search ------------------------------

@bp.route('/scene/persons', methods=['POST', 'GET'])
def show_person_list(selection=None):
    """ Show list of selected Persons for menu(0) """
    t0 = time.time()
    if request.method == 'POST':
        try:
            # Selection from search form
            name = request.form['name']
            rule = request.form['rule']
            keys = (rule, name)
            persons = read_persons_with_events(keys)
            return render_template("/scene/persons.html", persons=persons, menuno=0,
                                   name=name, rule=keys, elapsed=time.time()-t0)
        except Exception as e:
            logger.debug("Error {} in show_person_list".format(e))
            flash("Valitse haettava nimi ja tyyppi", category='warning')

    # the code below is executed if the request method
    # was GET or the credentials were invalid
    persons = []
    if selection:
        # Use selection filter
        keys = selection.split('=')
    else:
        keys = ('surname',)
    persons = [] #datareader.read_persons_with_events(keys)
    return render_template("/scene/persons.html", persons=persons,
                           menuno=0, rule=keys, elapsed=time.time()-t0)

@bp.route('/scene/persons/ref=<string:refname>')
@bp.route('/scene/persons/ref=<string:refname>/<opt>')
@login_required
def show_persons_by_refname(refname, opt=""):
    """ List persons by refname
    """
    keys = ('refname', refname)
    if current_user.is_authenticated:
        user=current_user.username
    else:
        user=None
    ref = ('ref' in opt)
    order = 0
    persons = read_persons_with_events(keys, user=user, take_refnames=ref, order=order)
    return render_template("/scene/persons.html", persons=persons, menuno=1, 
                           order=order, rule=keys)

# ------------------------------ Menu 1 Persons --------------------------------

@bp.route('/scene/persons_own/<string:start>')
@bp.route('/scene/persons_own/')
@login_required
def show_my_persons(start=''):
    """ List all persons for menu(11)
        Restriction by owner's UserProfile 
    """
    t0 = time.time()
    keys = ('all',)
    if current_user.is_authenticated:
        user=current_user.username
    else:
        user=None
    persons = Person_combo.read_my_persons_list(user, start, 100)
    return render_template("/scene/list_persons.html", persons=persons, menuno=11, 
                           rule=keys, elapsed=time.time()-t0)

@bp.route('/scene/persons_all/')
#     @login_required
def show_my_persons_all(opt=''):
    """ List all persons for menu(12)
        Both owners and other persons 
    """
    t0 = time.time()
    keys = ('all',)
    if current_user.is_authenticated:
        user=current_user.username
    else:
        user=None
#     if 'fn' in opt: order = 1   # firstname
#     elif 'pn' in opt: order = 2 # firstname
#     else: order = 0             # surname
    persons = read_persons_with_events(keys, user=user)
    return render_template("/scene/list_persons.html", persons=persons, menuno=12, 
                           rule=keys, elapsed=time.time()-t0)

@bp.route('/scene/persons/all/<string:opt>')
@bp.route('/scene/persons/all/')
#     @login_required
def show_all_persons_list(opt=''):
    """ List all persons for menu(1)    OLD MODEL WITHOUT User selection
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
    return render_template("/scene/persons.html", persons=persons, menuno=1, 
                           order=order,rule=keys, elapsed=time.time()-t0)


@bp.route('/scene/person/<int:uid>')
#     @login_required
# def show_a_person(uid):
#     """ One Person with connected Events, Families etc
#         Korvaamaan metodin show_person_page()
#     """
#     if not uid:
#         return redirect(url_for('virhesivu', code=1, text="Missing Person key"))
#     if current_user.is_authenticated:
#         user=current_user.username
#     else:
#         user=None
#     person, sources = get_a_person_for_display(uid, user)
#     return render_template("/scene/person_pg.html", 
#                            person=person, sources=sources, menuno=1)
@bp.route('/scene/person/a=<int:uid>')
#     @login_required
def show_a_person_w_apoc(uid):
    """ One Person with all connected nodes
        Korvaamaan metodin show_person_page()
    """
    t0 = time.time()
    if not uid:
        return redirect(url_for('virhesivu', code=1, text="Missing Person key"))

    if current_user.is_authenticated:
        user=current_user.username
    else:
        user=None
    
    person, objs, marks = get_a_person_for_display_apoc(uid, user)
    if person == None:
        return redirect(url_for('virhesivu', code=1, text="Henkilötietoja ei saatu"))
#     for m in marks:
#         print("Citation mark {}".format(m))
#     for e in person.events:
#         for ni in e.note_ref:
#             print("Event {} Note {}: {}".format(e.uniq_id, ni, objs[ni]))

    return render_template("/scene/person_pg.html", person=person, obj=objs, 
                           marks=marks, menuno=1, elapsed=time.time()-t0)


@bp.route('/scene/person=<int:uniq_id>')
#     @login_required
def show_person_page(uniq_id):
    """ Full homepage for a Person in database (vanhempi versio)
    """
    t0 = time.time()
    try:
        person, events, photos, citations, families = get_person_data_by_id(uniq_id)
        for f in families:
            print ("{} in Family {} / {}".format(f.role, f.uniq_id, f.id))
            if f.mother:
                print("  Mother: {} / {} s. {}".\
                      format(f.mother.uniq_id, f.mother.id, f.mother.birth_date))
            if f.father:
                print("  Father:  {} / {} s. {}".\
                      format(f.father.uniq_id, f.father.id, f.father.birth_date))
            if f.children:
                for c in f.children:
                    print("    Child ({}): {} / {} *{}".\
                          format(c.gender, c.uniq_id, c.id, c.birth_date))
    except KeyError as e:
        return redirect(url_for('virhesivu', code=1, text=str(e)))
    return render_template("/scene/person.html", person=person, events=events, 
                           photos=photos, citations=citations, families=families, 
                           elapsed=time.time()-t0)

# ------------------------------ Menu 4: Places --------------------------------

@bp.route('/scene/locations')
def show_locations():
    """ List of Places for menu(4)
    """
    t0 = time.time()
    try:
        # 'locations' has Place objects, which include also the lists of
        # nearest upper and lower Places as place[i].upper[] and place[i].lower[]
        locations = Place.get_place_hierarchy()
    except KeyError as e:
        return redirect(url_for('virhesivu', code=1, text=str(e)))
#     for p in locations:
#         print ("# {} ".format(p))
    return render_template("/scene/locations.html", locations=locations, 
                           elapsed=time.time()-t0)


@bp.route('/scene/location=<int:locid>')
def show_location_page(locid):
    """ Home page for a Place, shows events and place hierarchy
        locid = id(Place)
    """
    try:
        # List 'place_list' has Place objects with 'parent' field pointing to
        # upper place in hierarcy. Events
        place, place_list, events = get_place_with_events(locid)
    except KeyError as e:
        return redirect(url_for('virhesivu', code=1, text=str(e)))
#     for p in place_list:
#         print ("# {} ".format(p))
#     for u in place.notes:
#         print ("# {} ".format(u))
    return render_template("/scene/place_events.html", locid=locid, place=place, 
                           events=events, locations=place_list)

# ------------------------------ Menu 5: Sources --------------------------------

@bp.route('/scene/sources')
def show_sources():
    """ Lähdeluettelon näyttäminen ruudulla for menu(5)
    """
    try:
        sources = Source.get_source_list()
    except KeyError as e:
        return redirect(url_for('virhesivu', code=1, text=str(e)))
    return render_template("/scene/sources.html", sources=sources)


@bp.route('/scene/source=<int:sourceid>')
def show_source_page(sourceid):
    """ Home page for a Source with referring Event and Person data
    """
    try:
        stitle, citations = get_source_with_events(sourceid)
    except KeyError as e:
        return redirect(url_for('virhesivu', code=1, text=str(e)))
    return render_template("/scene/source_events.html",
                           stitle=stitle, citations=citations)

