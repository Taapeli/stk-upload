'''
Created on 12.8.2018

@author: jm
'''
import logging 
logger = logging.getLogger('stkserver')

from flask import render_template, request, redirect, url_for, flash
from flask_security import current_user

from . import bp
from models.datareader import read_persons_with_events
from models.datareader import get_person_data_by_id
from models.datareader import get_place_with_events
from models.datareader import get_source_with_events
from models.gen.place import Place
from models.gen.source_citation import Source


@bp.route('/narrative/persons', methods=['POST', 'GET'])
def show_person_list(selection=None):
    """ Show list of selected Persons """
    if request.method == 'POST':
        try:
            # Selection from search form
            name = request.form['name']
            rule = request.form['rule']
            keys = (rule, name)
            persons = read_persons_with_events(keys)
            return render_template("/narrative/persons.html", persons=persons, menuno=0,
                                   name=name, rule=rule)
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
        keys = ('all',)
    persons = [] #datareader.read_persons_with_events(keys)
    return render_template("/narrative/persons.html", persons=persons, menuno=0)


@bp.route('/narrative/persons/restricted')
def show_persons_restricted(selection=None):
    """ Show list of selected Persons, limited information 
        for non-logged users from login_user.html """
    if not current_user.is_authenticated:
        # Tässä aseta sisäänkirjautumattoman käyttäjän rajoittavat parametrit.
        # Vaihtoehtoisesti kutsu toista metodia.
        keys = ('all',)
    persons = read_persons_with_events(keys)
    return render_template("/narrative/persons.html", persons=persons, menuno=1)


@bp.route('/narrative/persons/all/<string:opt>')
@bp.route('/narrative/persons/all/')
#     @login_required
def show_all_persons_list(selection=None, opt=''):
    """ TODO Should have restriction by owner's UserProfile """
    keys = ('all',)
    if current_user.is_authenticated:
        user=current_user.username
    else:
        user=None
    ref = (opt == 'ref')
    persons = read_persons_with_events(keys, user=user, take_refnames=ref)
    return render_template("/narrative/persons.html", persons=persons, menuno=1)


@bp.route('/narrative/person=<string:uniq_id>')
#     @login_required
def show_person_page(uniq_id):
    """ Full homepage for a Person in database
    """

    try:
        person, events, photos, sources, families = \
            get_person_data_by_id(uniq_id)
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
    return render_template("/narrative/person.html", person=person, events=events, 
                           photos=photos, sources=sources, families=families)


@bp.route('/narrative/locations')
def show_locations():
    """ List of Places
    """
    try:
        # 'locations' has Place objects, which include also the lists of
        # nearest upper and lower Places as place[i].upper[] and place[i].lower[]
        locations = Place.get_place_names()
    except KeyError as e:
        return redirect(url_for('virhesivu', code=1, text=str(e)))
#     for p in locations:
#         print ("# {} ".format(p))
    return render_template("/narrative/locations.html", locations=locations)


@bp.route('/narrative/location=<locid>')
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
#     for u in place.urls:
#         print ("# {} ".format(u))
    return render_template("/narrative/place_events.html", locid=locid, place=place, 
                           events=events, locations=place_list)

@bp.route('/narrative/sources')
def show_sources():
    """ Lähdeluettelon näyttäminen ruudulla
    """
    try:
        sources = Source.get_source_list()
    except KeyError as e:
        return redirect(url_for('virhesivu', code=1, text=str(e)))
    return render_template("/narrative/sources.html", sources=sources)


@bp.route('/narrative/source=<sourceid>')
def show_source_page(sourceid):
    """ Home page for a Source with events
    """
    try:
        stitle, events = get_source_with_events(sourceid)
    except KeyError as e:
        return redirect(url_for('virhesivu', code=1, text=str(e)))
    return render_template("/narrative/source_events.html",
                           stitle=stitle, events=events)

