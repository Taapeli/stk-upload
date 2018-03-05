# coding=UTF-8
# Flask main program for Stk application
# @ Sss 2016
# JMä 29.12.2015

import logging
logger = logging.getLogger('stkserver')

from flask import render_template, request, redirect, url_for, flash
from flask_security import login_required, roles_accepted, roles_required, current_user
import shareds
import models.gen   
from models import loadfile            # Datan lataus käyttäjältä
from models import datareader          # Tietojen haku kannasta (tai työtiedostosta)
from models import dataupdater         # Tietojen päivitysmetodit
from models import gramps_loader       # Loading a gramps xml file
from models import cvs_refnames        # Referenssinimien luonti
from forms import ListEmailsForm
from templates import jinja_filters


app = shareds.app
if not app:
    raise RuntimeError("Start this application in '..' from 'run.py' or 'runssl.py'")


""" Application route definitions
"""

@shareds.app.route('/', methods=['GET', 'POST'])
@login_required
def home():
    """ Home page for logged in user """
    role_names = [role.name for role in current_user.roles]
    logger.info(current_user.username + ' / ' + current_user.email + \
                ' logged in, roles ' + str(role_names))
    return render_template('/mainindex.html')


@app.route('/admin',  methods=['GET', 'POST'])
@login_required
@roles_required('admin')
def admin():
    """ Home page for administrator """    
    return render_template('/adminindex.html')


@app.route('/list_emails',  methods=['GET', 'POST'])
#    @login_required
#    @roles_required('admin')
def list_emails():
    form = ListEmailsForm()
    if request.method == 'GET':
        lista = shareds.user_datastore.get_emails()
        return render_template("/security/list_emails.html", emails=lista, form=form)
    elif request.method == 'POST':
        shareds.user_datastore.email_register(form.allowed_email.data, form.default_role.data)
        lista = shareds.user_datastore.get_emails()
        return render_template("/security/list_emails.html", emails=lista, form=form)


@app.route('/list_users', methods=['GET'])
# @login_required
def list_users():
# Käytetään neo4juserdatastorea
    lista = shareds.user_datastore.get_users()
    return render_template("security/list_users.html", users=lista)  


@app.route('/tables')
#     @roles_accepted('member', 'admin')
@roles_accepted('member', 'admin')
def datatables():
    """ Technical table format listings """
    return render_template("tables.html")


@app.route('/refnames')
@roles_required('admin')
def refnames():
    """ Operations for reference names """
    return render_template("reference.html")


""" --------------------- Narrative Kertova-sivut ------------------------------
    Modules k_* uses the Kertova layout 
    (derived from the Gramps Narrative report)
"""

@app.route('/person/list/', methods=['POST', 'GET'])
def show_person_list(selection=None):
    """ Show list of selected Persons """
    if request.method == 'POST':
        try:
            # Selection from search form
            name = request.form['name']
            rule = request.form['rule']
            keys = (rule, name)
            persons = models.datareader.read_persons_with_events(keys)
            return render_template("k_persons.html", persons=persons, menuno=0,
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
    return render_template("k_persons.html", persons=persons, menuno=0)


@app.route('/person/list/restricted')
def show_persons_restricted(selection=None):
    """ Show list of selected Persons, limited information 
        for non-logged users """
    if not current_user.is_authenticated:
        # Tässä aseta sisäänkirjautumattoman käyttäjän rajoittavat parametrit.
        # Vaihtoehtoisesti kutsu toista metodia.
        keys = ('all',)
    persons = models.datareader.read_persons_with_events(keys)
    return render_template("k_persons.html", persons=persons, menuno=1)


@app.route('/person/list_all')
#     @login_required
def show_all_persons_list(selection=None):
    """ TODO Should have restriction by owner's UserProfile """
    keys = ('all',)
    if current_user.is_authenticated:
        user=current_user.username
    else:
        user=None
    persons = models.datareader.read_persons_with_events(keys, user=user)
    return render_template("k_persons.html", persons=persons, menuno=1)


@app.route('/person/<string:cond>')
#     @login_required
def show_person_page(cond):
    """ Full homepage for a Person in database
        cond = 'uniq_id=arvo'    selected by db key id(Person)
    """
    key, value = cond.split('=')
    try:
        if key == 'uniq_id':
            person, events, photos, sources, families = \
                datareader.get_person_data_by_id(value)
            for f in families:
                print ("{} in Family {} / {}".format(f.role, f.uniq_id, f.id))
                if f.mother:
                    print("  Mother: {} / {} s. {}".format(f.mother.uniq_id, f.mother.id, f.mother.birth_date))
                if f.father:
                    print("  Father:  {} / {} s. {}".format(f.father.uniq_id, f.father.id, f.father.birth_date))
                if f.children:
                    for c in f.children:
                        print("    Child ({}): {} / {} *{}".format(c.gender, c.uniq_id, c.id, c.birth_date))
        else:
            raise(KeyError("Väärä hakuavain"))
    except KeyError as e:
        return redirect(url_for('virhesivu', code=1, text=str(e)))
    return render_template("k_person.html", person=person, events=events, 
                           photos=photos, sources=sources, families=families)


@app.route('/events/loc=<locid>')
def show_location_page(locid):
    """ Home page for a location, including place hierarchy and events
        locid = id(Place)
    """
    try:
        # List 'place_list' has Place objects with 'parent' field pointing to
        # upper place in hierarcy. Events
        place, place_list, events = datareader.get_place_with_events(locid)
    except KeyError as e:
        return redirect(url_for('virhesivu', code=1, text=str(e)))
#     for p in place_list:
#         print ("# {} ".format(p))
#     for u in place.urls:
#         print ("# {} ".format(u))
    return render_template("k_place_events.html", locid=locid, place=place, 
                           events=events, locations=place_list)

@app.route('/events/source=<sourceid>')
def show_source_page(sourceid):
    """ Home page for a Source with events
    """
    try:
        stitle, events = datareader.get_source_with_events(sourceid)
    except KeyError as e:
        return redirect(url_for('virhesivu', code=1, text=str(e)))
    return render_template("k_source_events.html",
                           stitle=stitle, events=events)


""" ---------- Listings (Narrative or table format) ----------------------------
"""

@app.route('/lista/<string:subj>')
def nayta_henkilot(subj):
    """ Person listings
        tietokannan henkiloiden tai käyttäjien näyttäminen ruudulla 
    """
    if subj == "k_persons":
        # Kertova-tyyliin
        persons = datareader.read_persons_with_events()
        return render_template("k_persons.html", persons=persons, menuno=0)
#     if subj == "henkilot":
#         dburi = models.dbutil.get_server_location()
#         persons = datareader.lue_henkilot()
#         return render_template("table_persons.html", persons=persons, uri=dburi)
    elif subj == "henkilot2":
        persons = datareader.read_persons_with_events()
        return render_template("table_persons2.html", persons=persons)
    elif subj == "surnames":
        surnames = models.gen.person.Name.get_surnames()
        return render_template("table_surnames.html", surnames=surnames)
    elif subj == 'events_wo_cites':
        headings, titles, lists = datareader.read_events_wo_cites()
        return render_template("table_of_data.html",
               headings=headings, titles=titles, lists=lists)
    elif subj == 'events_wo_place':
        headings, titles, lists = datareader.read_events_wo_place()
        return render_template("table_of_data.html",
               headings=headings, titles=titles, lists=lists)
    elif subj == 'notes':
        titles, lists = datareader.get_notes()
        return render_template("table_of_data.html",
                               headings=("Huomautusluettelo", "Note-kohteet"),
                               titles=titles, lists=lists)
    elif subj == 'media':
        media = datareader.read_medias()
        return render_template("table_media.html",
                               media=media)
    elif subj == 'people_wo_birth':
        headings, titles, lists = datareader.read_people_wo_birth()
        return render_template("table_of_data.html",
               headings=headings, titles=titles, lists=lists)
    elif subj == 'old_people_top':
        headings, titles, lists = datareader.read_old_people_top()
        return render_template("table_of_data.html",
               headings=headings, titles=titles, lists=lists)
    elif subj == 'repositories':
        repositories = datareader.read_repositories()
        for r in repositories:
            r.type = jinja_filters.translate(r.type, 'rept', 'fi')
        return render_template("ng_table_repositories.html",
                               repositories=repositories)
    elif subj == 'same_birthday':
        ids = models.datareader.read_same_birthday()
        return render_template("ng_same_birthday.html", ids=ids)
    elif subj == 'same_deathday':
        ids = models.datareader.read_same_deathday()
        return render_template("ng_same_deathday.html", ids=ids)
    elif subj == 'same_name':
        ids = models.datareader.read_same_name()
        return render_template("ng_same_name.html", ids=ids)
    elif subj == 'sources':
        sources = datareader.read_sources()
        return render_template("table_sources.html", sources=sources)
    elif subj == 'sources_wo_cites':
        headings, titles, lists = datareader.read_sources_wo_cites()
        return render_template("table_of_data.html", headings=headings,
                               titles=titles, lists=lists)
    elif subj == 'sources_wo_repository':
        headings, titles, lists = datareader.read_sources_wo_repository()
        return render_template("table_of_data.html",
               headings=headings, titles=titles, lists=lists)
    elif subj == 'places':
        headings, titles, lists = datareader.read_places()
        return render_template("table_of_data.html", headings=headings,
                               titles=titles, lists=lists)
    else:
        return redirect(url_for('virhesivu', code=1, text= \
            "Aineistotyypin '" + subj + "' käsittely puuttuu vielä"))


@app.route('/lista/k_locations')
def show_locations():
    """ List of Places
    """
    try:
        # 'locations' has Place objects, which include also the lists of
        # nearest upper and lower Places as place[i].upper[] and place[i].lower[]
        locations = models.gen.place.Place.get_place_names()
    except KeyError as e:
        return redirect(url_for('virhesivu', code=1, text=str(e)))
#     for p in locations:
#         print ("# {} ".format(p))
    return render_template("k_locations.html", locations=locations)


@app.route('/lista/k_sources')
def show_sources():
    """ List of all Sources """
    try:
        sources = models.gen.source_citation.Source.get_source_list()
    except KeyError as e:
        return redirect(url_for('virhesivu', code=1, text=str(e)))
    return render_template("k_sources.html", sources=sources)


@app.route('/list/refnames', defaults={'reftype': None})
#@app.route('/list/refnames/<string:reftype>')
def list_refnames(reftype):
    """ Table of reference names """
#     if reftype and reftype != "":
#         names = datareader.read_typed_refnames(reftype)  # TODO: Not tested method
#         return render_template("table_refnames_1.html", names=names, reftype=reftype)
#     else:
    names = datareader.read_refnames()
    return render_template("table_refnames.html", names=names)


@app.route('/lista/people_by_surname/', defaults={'surname': ""})
@app.route('/lista/people_by_surname/<string:surname>')
def list_people_by_surname(surname):
    """ Table of Persons with identical surname
        henkilöiden, joilla on sama sukunimi näyttäminen ruudulla 
    """
    people = datareader.get_people_by_surname(surname)
    return render_template("table_people_by_surname.html",
                           surname=surname, people=people)


@app.route('/lista/person_data/<string:uniq_id>')
def show_person_data(uniq_id):
    """ Table of a Person selected by id(Person)
        linkki oli sukunimiluettelosta
    """
    person, events, photos, sources, families = datareader.get_person_data_by_id(uniq_id)
    logger.debug("Got {} persons, {} events, {} photos, {} sources, {} families".\
                 format(len(person), len(events), len(photos), len(sources), len(families)))
    return render_template("table_person_by_id.html",
                       person=person, events=events, photos=photos, sources=sources)


@app.route('/compare/<string:cond>')
def compare_person_page(cond): 
    """ Comparison of two Persons
        Vertailu - henkilön tietojen näyttäminen ruudulla 
        cond = 'uniq_id=key1,key2'    the keys are db keys id(Person)
    """
    key, value = cond.split('=')
    uniq_id_1, uniq_id_2 = value.split(',')
    try:
        if key == 'uniq_id':
            person, events, photos, sources, families = \
                datareader.get_person_data_by_id(uniq_id_1)
            person2, events2, photos2, sources2, families2 = \
                datareader.get_person_data_by_id(uniq_id_2)
            for f in families:
                print ("{} perheessä {} / {}".format(f.role, f.uniq_id, f.id))
                if f.mother:
                    print("  Äiti: {} / {} s. {}".format(f.mother.uniq_id, f.mother.id, f.mother.birth_date))
                if f.father:
                    print("  Isä:  {} / {} s. {}".format(f.father.uniq_id, f.father.id, f.father.birth_date))
                if f.children:
                    for c in f.children:
                        print("    Lapsi ({}): {} / {} *{}".format(c.gender, c.uniq_id, c.id, c.birth_date))
        else:
            raise(KeyError("Väärä hakuavain"))
    except KeyError as e:
        return redirect(url_for('virhesivu', code=1, text=str(e)))
    return render_template("ng_compare.html", person=person, events=events, 
                           photos=photos, sources=sources,  families=families,
                           person2=person2, events2=events2, 
                           photos2=photos2, sources2=sources2, families2=families2)


@app.route('/compare2/<string:cond>')
def compare_person_page2(cond):
    """ Vertailu - henkilön tietojen näyttäminen ruudulla
        uniq_id=arvo    näyttää henkilön tietokanta-avaimen mukaan
    """
    key, value = cond.split('=')
    try:
        if key == 'uniq_id':
            person, events, photos, sources, families = \
                datareader.get_person_data_by_id(value)
            for f in families:
                print ("{} perheessä {} / {}".format(f.role, f.uniq_id, f.id))
                if f.mother:
                    print("  Äiti: {} / {} s. {}".format(f.mother.uniq_id, f.mother.id, f.mother.birth_date))
                if f.father:
                    print("  Isä:  {} / {} s. {}".format(f.father.uniq_id, f.father.id, f.father.birth_date))
                if f.children:
                    for c in f.children:
                        print("    Lapsi ({}): {} / {} *{}".format(c.gender, c.uniq_id, c.id, c.birth_date))
        else:
            raise(KeyError("Väärä hakuavain"))
    except KeyError as e:
        return redirect(url_for('virhesivu', code=1, text=str(e)))
    return render_template("compare2.html",
        person=person, events=events, photos=photos, sources=sources, families=families)


@app.route('/lista/baptism_data/<string:uniq_id>')
def show_baptism_data(uniq_id):
    """ Table of a baptism Event selected by id(Event)
        kastetapahtuman tietojen näyttäminen ruudulla 
    """
    event, persons = datareader.get_baptism_data(uniq_id)
    return render_template("table_baptism_data.html",
                           event=event, persons=persons)


@app.route('/lista/family_data/<string:uniq_id>')
def show_family_data(uniq_id):
    """ Table of families of a Person
        henkilön perheen tietojen näyttäminen ruudulla 
    """
    person, families = datareader.get_families_data_by_id(uniq_id)
    return render_template("table_families_by_id.html",
                           person=person, families=families)


@app.route('/pick/<string:cond>')
def pick_selection(cond):
    """ Table of objects selected by the argument
    """
    key, value = cond.split('=')
    try:
#         if key == 'oid':              
#             # from table_persons.html as @app.route('/poimi/<string:cond>')
#             persons = models.datareader.lue_henkilot(oid=value)
#             return render_template("person.html", persons=persons)

        if key == 'name':               # A prototype for later development
            value=value.title()
            persons = datareader.read_persons_with_events(keys=['surname',value])
            return render_template("join_persons.html",
                                   persons=persons, pattern=value)
        elif key == 'cite_sour_repo':   # from table_person_by_id.html
            events = models.datareader.read_cite_sour_repo(uniq_id=value)
            return render_template("cite_sour_repo.html",
                                   events=events)
        elif key == 'repo_uniq_id':     # from cite_sourc_repo.html, 
                                        # ng_table_repositories.html,
                                        # table_repositories.html
            repositories = models.datareader.read_repositories(uniq_id=value)
            return render_template("repo_sources.html",
                                   repositories=repositories)
        elif key == 'source_uniq_id':   # from cite_sourc_repo.html, table_sources.html
            sources = models.datareader.read_sources(uniq_id=value)
            return render_template("source_citations.html",
                                   sources=sources)
        elif key == 'uniq_id':          # from table_persons2.html
            persons = models.datareader.read_persons_with_events(("uniq_id",value))
            return render_template("person2.html", persons=persons)
        else:
            raise(KeyError("Vain oid:llä voi hakea"))
    except KeyError as e:
        return redirect(url_for('virhesivu', code=1, text=str(e)))


""" -------------------------- Tietojen talletus ------------------------------
"""

@app.route('/upload', methods=['POST'])
def upload():
    """ Load a cvs file to temp directory for processing in the server
    """
    try:
        infile = request.files['filenm']
        material = request.form['material']
        logging.debug("Got a {} file '{}'".format(material, infile.filename))

        loadfile.upload_file(infile)
        if 'destroy' in request.form and request.form['destroy'] == 'all':
            logger.info("*** About deleting all previous Refnames ***")
            datareader.recreate_refnames()

    except Exception as e:
        return redirect(url_for('virhesivu', code=1, text=str(e)))

    return redirect(url_for('save_loaded', filename=infile.filename, subj=material))

@app.route('/save/<string:subj>/<string:filename>')
def save_loaded(filename, subj):
    """ Save loaded xml of cvs data to the database """
    pathname = models.loadfile.fullname(filename)
    dburi = models.dbutil.get_server_location()
    try:
        if subj == 'refnames':    # Stores Refname objects
            status = cvs_refnames.load_refnames(pathname)
        elif subj == 'xml_file':  # gramps backup xml file to Neo4j db
            status = gramps_loader.xml_to_neo4j(pathname, current_user.username)
        else:
            return redirect(url_for('virhesivu', code=1, text= \
                "Data type '" + subj + "' is still missing"))
    except KeyError as e:
        return render_template("virhe_lataus.html", code=1, \
               text="Missing proper column title: " + str(e))
    return render_template("talletettu.html", text=status, uri=dburi)

@app.route('/tyhjenna/kaikki/kannasta')
def tyhjenna():
    """ Clear database - with no confirmation! """
    msg = models.dbutil.alusta_kanta()
    return render_template("talletettu.html", text=msg)

@app.route('/aseta/confidence')
def aseta_confidence():
    """ tietojen laatuarvion asettaminen henkilöille """
    dburi = models.dbutil.get_server_location()
    message = dataupdater.set_confidence_value() 
    return render_template("talletettu.html", text=message, uri=dburi)

@app.route('/aseta/estimated_dates')
def aseta_estimated_dates():
    """ syntymä- ja kuolinaikojen arvioiden asettaminen henkilöille """
    dburi = models.dbutil.get_server_location()
    message = dataupdater.set_estimated_dates()
    return render_template("talletettu.html", text=message, uri=dburi)

@app.route('/set/refnames')
def set_person_refnames():
    """ Setting reference names for all persons """
    dburi = models.dbutil.get_server_location()
    message = dataupdater.set_person_refnames()
    return render_template("talletettu.html", text=message, uri=dburi)

@app.route('/virhe_lataus/<int:code>/<text>')
def virhesivu(code, text=''):
    """ Virhesivu näytetään """
    logging.debug('Virhesivu ' + str(code) )
    return render_template("virhe_lataus.html", code=code, text=text)



""" ------------------------ Obsolete operations? ------------------------------
"""


@app.route('/lista/person_data/<string:uniq_id>')
def show_person_data_dbl(uniq_id):
    """ Table of Person data
        Henkilön tietojen näyttäminen ruudulla 
        Linkki oli sukunimiluettelosta
    """
    person, events, photos, sources, families = \
        datareader.get_person_data_by_id(uniq_id)
    logger.debug("Got {} persons, {} events, {} photos, {} sources, {} families".\
                 format(len(person), len(events), len(photos), len(sources), len(families)))
    return render_template("table_person_by_id.html",
                       person=person, events=events, photos=photos, sources=sources)


@app.route('/compare/<string:cond>')
def compare_person_page_dbl(cond):
    """ Vertailu - henkilön tietojen näyttäminen ruudulla
        uniq_id=arvo    näyttää henkilön tietokanta-avaimen mukaan
    """
    key, value = cond.split('=')
    try:
        if key == 'uniq_id':
            person, events, photos, sources, families = \
                datareader.get_person_data_by_id(value)
            for f in families:
                print ("{} perheessä {} / {}".format(f.role, f.uniq_id, f.id))
                if f.mother:
                    print("  Äiti: {} / {} s. {}".format(f.mother.uniq_id, f.mother.id, f.mother.birth_date))
                if f.father:
                    print("  Isä:  {} / {} s. {}".format(f.father.uniq_id, f.father.id, f.father.birth_date))
                if f.children:
                    for c in f.children:
                        print("    Lapsi ({}): {} / {} *{}".format(c.gender, c.uniq_id, c.id, c.birth_date))
        else:
            raise(KeyError("Väärä hakuavain"))
    except KeyError as e:
        return redirect(url_for('virhesivu', code=1, text=str(e)))
    return render_template("compare3.html",
        person=person, events=events, photos=photos, sources=sources, families=families)


@app.route('/compare2/<string:cond>')
def compare_person_page2_dbl(cond):
    """ Vertailu - henkilön tietojen näyttäminen ruudulla
        uniq_id=arvo    näyttää henkilön tietokanta-avaimen mukaan
    """
    key, value = cond.split('=')
    try:
        if key == 'uniq_id':
            person, events, photos, sources, families = \
                datareader.get_person_data_by_id(value)
            for f in families:
                print ("{} in the family {} / {}".format(f.role, f.uniq_id, f.id))
                if f.mother:
                    print("  Mother: {} / {} s. {}".format(f.mother.uniq_id, f.mother.id, f.mother.birth_date))
                if f.father:
                    print("  Father:  {} / {} s. {}".format(f.father.uniq_id, f.father.id, f.father.birth_date))
                if f.children:
                    for c in f.children:
                        print("    Clild ({}): {} / {} *{}".format(c.gender, c.uniq_id, c.id, c.birth_date))
        else:
            raise(KeyError("Väärä hakuavain"))
    except KeyError as e:
        return redirect(url_for('virhesivu', code=1, text=str(e)))
    return render_template("compare2.html",
        person=person, events=events, photos=photos, sources=sources, families=families)


@app.route('/lista/family_data/<string:uniq_id>')
def show_family_data_dbl(uniq_id):
    """ henkilön perheen tietojen näyttäminen ruudulla """
    person, families = datareader.get_families_data_by_id(uniq_id)
    return render_template("table_families_by_id.html",
                           person=person, families=families)


@app.route('/yhdista', methods=['POST'])
def nimien_yhdistely():
    """ Nimien listaus tietokannasta ehtolauseella
        oid=arvo        näyttää nimetyn henkilön
        names=arvo      näyttää henkilöt, joiden nimi alkaa arvolla
    """
    names = request.form['names']
    logging.debug('Poimitaan ' + names )
    return redirect(url_for('pick_selection', ehto='names='+names))


@app.route('/samahenkilo', methods=['POST'])
def henkiloiden_yhdistely():
    """ Yhdistetään base-henkilöön join-henkilöt tapahtumineen,
        minkä jälkeen näytetään muuttunut henkilölista
    """
    names = request.form['names']
    print (dir(request.form))
    base_id = request.form['base']
    join_ids = request.form.getlist('join')
    #TODO lisättävä valitut ref.nimet, jahka niitä tulee
    dataupdater.joinpersons(base_id, join_ids)
    flash('Yhdistettiin (muka) ' + str(base_id) + " + " + str(join_ids) )
    return redirect(url_for('pick_selection', ehto='names='+names))