#!/usr/bin/python
# coding=UTF-8
# Taapeli harjoitustyö @ Sss 2016
# JMä 29.12.2015

import logging
logger = logging.getLogger('stkserver')
#import builtins
from flask import render_template, request, redirect, url_for, flash
from flask_security import login_required, roles_required, current_user
#from datetime import datetime
import shareds
import templates.jinja_filters
#===============================================================================
app = shareds.app
with app.app_context():
    # within this block, current_app points to app.
    import models.dbutil
    import models.loadfile          # Datan lataus käyttäjältä
    import models.datareader        # Tietojen haku kannasta (tai työtiedostosta)
    import models.dataupdater       # Tietojen päivitysmetodit
    import models.cvs_refnames      # Referenssinimien luonti
    import models.gen
    #import models.gen.user          # Käyttäjien tiedot

    """ Application route definitions
    """

    @app.route('/', methods=['GET', 'POST'])
    @login_required
    def home():
        """ Kirjautuneen käyttäjän kotisivu """
        role_names = [role.name for role in current_user.roles]
        logger.info(current_user.username + ' / ' + current_user.email + \
                    ' logged in, roles ' + str(role_names))
        return render_template('/mainindex.html')


    @app.route('/tables')
#     @roles_accepted('member', 'admin')
    @roles_required('admin')
    def datatables():
        """ Teknisten datataulukoiden käsittelysivu """
        return render_template("tables.html")


    @app.route('/refnames')
    @roles_required('admin')
    def refnames():
        """ Referenssiaineistojen käsittelysivu """
        return render_template("reference.html")



""" ----------------------------- Kertova-sivut --------------------------------
"""

@app.route('/person/list/', methods=['POST', 'GET'])
def show_person_list(selection=None):
    """ Valittujen tietokannan henkiloiden tai käyttäjien näyttäminen ruudulla """
    if request.method == 'POST':
        try:
            # Selection from search form
            name = request.form['name']
            rule = request.form['rule']
            keys = (rule, name)
            persons = models.datareader.lue_henkilot_k(keys)
            return render_template("k_persons.html", persons=persons, menuno=0)
        except Exception:
            flash("Ei oikeita hakukenttiä", category='warning')

    # the code below is executed if the request method
    # was GET or the credentials were invalid
    persons = []
    if selection:
        # Use selection filter
        keys = selection.split('=')
    else:
        keys = ('all',)
    persons = [] #models.datareader.lue_henkilot_k(keys)
    return render_template("k_persons.html", persons=persons, menuno=0)


@app.route('/person/list/restricted')
def show_persons_restricted(selection=None):
    """ tietokannan henkiloiden tai käyttäjien näyttäminen ruudulla mainostarkoituksessa"""
    if not current_user.is_authenticated:
        # Tässä aseta sisäänkirjautumattoman käyttäjän rajoittavat parametrit. Vaihtoehtoisesti kutsu toistra metodia.
                keys = ('all',)
    persons = models.datareader.lue_henkilot_k(keys)
    return render_template("k_persons.html", persons=persons, menuno=1)


@app.route('/person/list_all')
#     @login_required
def show_all_persons_list(selection=None):
    """ tietokannan henkiloiden tai käyttäjien näyttäminen ruudulla """
    keys = ('all',)
    persons = models.datareader.lue_henkilot_k(keys)
    return render_template("k_persons.html", persons=persons, menuno=1)


@app.route('/person/<string:ehto>')
#     @login_required
def show_person_page(ehto):
    """ Kertova - henkilön tietojen näyttäminen ruudulla
        uniq_id=arvo    näyttää henkilön tietokanta-avaimen mukaan
    """
    key, value = ehto.split('=')
    try:
        if key == 'uniq_id':
            person, events, photos, sources, families = \
                models.datareader.get_person_data_by_id(value)
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
    return render_template("k_person.html",
        person=person, events=events, photos=photos, sources=sources, families=families)


@app.route('/events/loc=<locid>')
def show_location_page(locid):
    """ Paikan tietojen näyttäminen ruudulla: hierarkia ja tapahtumat
    """
    try:
        # List 'locatils' has Place objects with 'parent' field pointing to
        # upper place in hierarcy. Events
        place, place_list, events = models.datareader.get_place_with_events(locid)
    except KeyError as e:
        return redirect(url_for('virhesivu', code=1, text=str(e)))
#     for p in place_list:
#         print ("# {} ".format(p))
#     for u in place.urls:
#         print ("# {} ".format(u))
    return render_template("k_place_events.html",
                       locid=locid, place=place, events=events, locations=place_list)


@app.route('/lista/k_sources')
def show_sources():
    """ Lähdeluettelon näyttäminen ruudulla
    """
    try:
        sources = models.gen.source_citation.Source.get_source_list()
    except KeyError as e:
        return redirect(url_for('virhesivu', code=1, text=str(e)))
    return render_template("k_sources.html", sources=sources)


@app.route('/events/source=<sourceid>')
def show_source_page(sourceid):
    """ Lähteen tietojen näyttäminen ruudulla: tapahtumat
    """
    try:
        stitle, events = models.datareader.get_source_with_events(sourceid)
    except KeyError as e:
        return redirect(url_for('virhesivu', code=1, text=str(e)))
    return render_template("k_source_events.html",
                           stitle=stitle, events=events)


""" ------ Listaukset (kertova- tai taulukko-muodossa) -------------------------
"""

@app.route('/lista/<string:subj>')
def nayta_henkilot(subj):
    """ tietokannan henkiloiden tai käyttäjien näyttäminen ruudulla """
    if subj == "k_persons":
        # Kertova-tyyliin
        persons = models.datareader.lue_henkilot_k()
        return render_template("k_persons.html", persons=persons, menuno=0)
#     if subj == "henkilot":
#         dburi = models.dbutil.get_server_location()
#         persons = models.datareader.lue_henkilot()
#         return render_template("table_persons.html", persons=persons, uri=dburi)
    elif subj == "henkilot2":
        persons = models.datareader.lue_henkilot_k()
        return render_template("table_persons2.html", persons=persons)
    elif subj == "surnames":
        surnames = models.gen.person.Name.get_surnames()
        return render_template("table_surnames.html", surnames=surnames)
    elif subj == 'events_wo_cites':
        headings, titles, lists = models.datareader.read_events_wo_cites()
        return render_template("table_of_data.html",
               headings=headings, titles=titles, lists=lists)
    elif subj == 'events_wo_place':
        headings, titles, lists = models.datareader.read_events_wo_place()
        return render_template("table_of_data.html",
               headings=headings, titles=titles, lists=lists)
    elif subj == 'notes':
        titles, lists = models.datareader.get_notes()
        return render_template("table_of_data.html",
                               headings=("Huomautusluettelo", "Note-kohteet"),
                               titles=titles, lists=lists)
    elif subj == 'media':
        media = models.datareader.read_medias()
        return render_template("table_media.html",
                               media=media)
    elif subj == 'people_wo_birth':
        headings, titles, lists = models.datareader.read_people_wo_birth()
        return render_template("table_of_data.html",
               headings=headings, titles=titles, lists=lists)
    elif subj == 'old_people_top':
        headings, titles, lists = models.datareader.read_old_people_top()
        return render_template("table_of_data.html",
               headings=headings, titles=titles, lists=lists)
    elif subj == 'repositories':
        repositories = models.datareader.read_repositories()
        for r in repositories:
            r.type = templates.jinja_filters.translate(r.type, 'rept', 'fi')
        return render_template("ng_table_repositories.html",
                               repositories=repositories)
    elif subj == 'sources':
        sources = models.datareader.read_sources()
        return render_template("table_sources.html",
                               sources=sources)
    elif subj == 'sources_wo_cites':
        headings, titles, lists = models.datareader.read_sources_wo_cites()
        return render_template("table_of_data.html",
               headings=headings, titles=titles, lists=lists)
    elif subj == 'sources_wo_repository':
        headings, titles, lists = models.datareader.read_sources_wo_repository()
        return render_template("table_of_data.html",
               headings=headings, titles=titles, lists=lists)
    elif subj == 'places':
        headings, titles, lists = models.datareader.read_places()
        return render_template("table_of_data.html",
               headings=headings, titles=titles, lists=lists)
    elif subj == "users":
        # Käytetään neo4juserdatastorea
        lista = shareds.user_datastore.get_users()
        return render_template("table_users.html", users=lista)
    else:
        return redirect(url_for('virhesivu', code=1, text= \
            "Aineistotyypin '" + subj + "' käsittely puuttuu vielä"))


@app.route('/lista/k_locations')
def show_locations():
    """ Paikkaluettelon näyttäminen ruudulla
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


@app.route('/list/refnames', defaults={'reftype': None})
@app.route('/list/refnames/<string:reftype>')
def list_refnames(reftype):
    """ show reference names on the screen """
    if reftype and reftype != "":
        names = models.datareader.read_typed_refnames(reftype)  # TODO: Not tested method
        return render_template("table_refnames_1.html", names=names, reftype=reftype)
    else:
        names = models.datareader.read_refnames()
        return render_template("table_refnames.html", names=names)


@app.route('/lista/people_by_surname/', defaults={'surname': ""})
@app.route('/lista/people_by_surname/<string:surname>')
def list_people_by_surname(surname):
    """ henkilöiden, joilla on sama sukunimi näyttäminen ruudulla """
    people = models.datareader.get_people_by_surname(surname)
    return render_template("table_people_by_surname.html",
                           surname=surname, people=people)


    #  linkki oli sukunimiluettelosta
@app.route('/lista/person_data/<string:uniq_id>')
def show_person_data(uniq_id):
    """ henkilön tietojen näyttäminen ruudulla """
    person, events, photos, sources, families = models.datareader.get_person_data_by_id(uniq_id)
    logger.debug("Got {} persons, {} events, {} photos, {} sources, {} families".\
                 format(len(person), len(events), len(photos), len(sources), len(families)))
    return render_template("table_person_by_id.html",
                       person=person, events=events, photos=photos, sources=sources)


@app.route('/compare/<string:ehto>')
def compare_person_page(ehto):
    """ Vertailu - henkilön tietojen näyttäminen ruudulla
        uniq_id=arvo    näyttää henkilön tietokanta-avaimen mukaan
    """
    key, value = ehto.split('=')
    try:
        if key == 'uniq_id':
            person, events, photos, sources, families = \
                models.datareader.get_person_data_by_id(value)
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


@app.route('/compare2/<string:ehto>')
def compare_person_page2(ehto):
    """ Vertailu - henkilön tietojen näyttäminen ruudulla
        uniq_id=arvo    näyttää henkilön tietokanta-avaimen mukaan
    """
    key, value = ehto.split('=')
    try:
        if key == 'uniq_id':
            person, events, photos, sources, families = \
                models.datareader.get_person_data_by_id(value)
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
    """ kastetapahtuman tietojen näyttäminen ruudulla """
    event, persons = models.datareader.get_baptism_data(uniq_id)
    return render_template("table_baptism_data.html",
                           event=event, persons=persons)



@app.route('/lista/family_data/<string:uniq_id>')
def show_family_data(uniq_id):
    """ henkilön perheen tietojen näyttäminen ruudulla """
    person, families = models.datareader.get_families_data_by_id(uniq_id)
    return render_template("table_families_by_id.html",
                           person=person, families=families)


@app.route('/poimi/<string:ehto>')
def nayta_ehdolla(ehto):
    """ Nimien listaus tietokannasta ehtolauseella
        oid=arvo        näyttää nimetyn henkilön
        name=arvo    näyttää henkilöt, joiden nimi alkaa arvolla
    """
    key, value = ehto.split('=')
    try:
#         if key == 'oid':
#             persons = models.datareader.lue_henkilot(oid=value)
#             return render_template("person.html", persons=persons)
        if key == 'name':
            value=value.title()
            persons = models.datareader.lue_henkilot_k(keys=['surname',value])
            return render_template("join_persons.html",
                                   persons=persons, pattern=value)
        elif key == 'cite_sour_repo':
            events = models.datareader.read_cite_sour_repo(uniq_id=value)
            return render_template("cite_sour_repo.html",
                                   events=events)
        elif key == 'repo_uniq_id':
            repositories = models.datareader.read_repositories(uniq_id=value)
            return render_template("repo_sources.html",
                                   repositories=repositories)
        elif key == 'source_uniq_id':
            sources = models.datareader.read_sources(uniq_id=value)
            return render_template("source_citations.html",
                                   sources=sources)
        elif key == 'uniq_id':
            persons = models.datareader.lue_henkilot_k(("uniq_id",value))
            return render_template("person2.html", persons=persons)
        else:
            raise(KeyError("Vain oid:llä voi hakea"))
    except KeyError as e:
        return redirect(url_for('virhesivu', code=1, text=str(e)))



""" -------------------------- Tietojen talletus ------------------------------
"""

@app.route('/lataa', methods=['POST'])
def lataa():
    """ Load a cvs file to temp directory for processing in the server
    """
    try:
        infile = request.files['filenm']
        material = request.form['material']
        logging.debug("Got a {} file '{}'".format(material, infile.filename))

        models.loadfile.upload_file(infile)

    except Exception as e:
        return redirect(url_for('virhesivu', code=1, text=str(e)))

    return redirect(url_for('save_loaded', filename=infile.filename, subj=material))


@app.route('/talleta/<string:subj>/<string:filename>')
def save_loaded(filename, subj):
    """ Saving loaded reference data to the database """
    pathname = models.loadfile.fullname(filename)
    dburi = models.dbutil.get_server_location()
    try:
#         if subj == 'henkilot':  # Käräjille osallistuneiden tiedot
#             status = models.datareader.datastorer(pathname)
        if subj == 'refnames': # Referenssinimet
            # Stores Refname objects
            status = models.cvs_refnames.load_refnames(pathname)
        elif subj == 'xml_file': # gramps backup xml file to Neo4j db
            status = models.datareader.xml_to_neo4j(pathname, current_user.username)
#         elif subj == 'karajat': # TODO: Tekemättä
#             status = "Käräjätietojen lukua ei ole vielä tehty"
        else:
            return redirect(url_for('virhesivu', code=1, text= \
                "Data type '" + subj + "' is still missing"))
    except KeyError as e:
        return render_template("virhe_lataus.html", code=1, \
               text="Missing proper column title: " + str(e))
    return render_template("talletettu.html", text=status, uri=dburi)


#  linkki oli sukunimiluettelosta
@app.route('/lista/person_data/<string:uniq_id>')
def show_person_data_dbl(uniq_id):
    """ henkilön tietojen näyttäminen ruudulla """
    #models.dbutil.connect_db()
    person, events, photos, sources, families = models.datareader.get_person_data_by_id(uniq_id)
    logger.debug("Got {} persons, {} events, {} photos, {} sources, {} families".\
                 format(len(person), len(events), len(photos), len(sources), len(families)))
    return render_template("table_person_by_id.html",
                       person=person, events=events, photos=photos, sources=sources)


@app.route('/compare/<string:ehto>')
def compare_person_page_dbl(ehto):
    """ Vertailu - henkilön tietojen näyttäminen ruudulla
        uniq_id=arvo    näyttää henkilön tietokanta-avaimen mukaan
    """
    key, value = ehto.split('=')
    try:
        if key == 'uniq_id':
            person, events, photos, sources, families = \
                models.datareader.get_person_data_by_id(value)
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


@app.route('/compare2/<string:ehto>')
def compare_person_page2_dbl(ehto):
    """ Vertailu - henkilön tietojen näyttäminen ruudulla
        uniq_id=arvo    näyttää henkilön tietokanta-avaimen mukaan
    """
    #models.dbutil.connect_db()
    key, value = ehto.split('=')
    try:
        if key == 'uniq_id':
            person, events, photos, sources, families = \
                models.datareader.get_person_data_by_id(value)
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
    #models.dbutil.connect_db()
    person, families = models.datareader.get_families_data_by_id(uniq_id)
    return render_template("table_families_by_id.html",
                           person=person, families=families)


@app.route('/poimi/<string:ehto>')
def nayta_ehdolla_dbl(ehto):
    """ Nimien listaus tietokannasta ehtolauseella
        oid=arvo        näyttää nimetyn henkilön
        names=arvo      näyttää henkilöt, joiden nimi alkaa arvolla
    """

    @app.route('/tyhjenna/kaikki/kannasta')
    def tyhjenna():
        """ tietokannan tyhjentäminen mitään kyselemättä """
        #models.dbutil.connect_db()
        msg = models.dbutil.alusta_kanta()
        return render_template("talletettu.html", text=msg)


@app.route('/aseta/confidence')
def aseta_confidence():
    """ tietojen laatuarvion asettaminen henkilöille """
    dburi = models.dbutil.get_server_location()
    message = models.datareader.set_confidence_value()
    return render_template("talletettu.html", text=message, uri=dburi)


@app.route('/aseta/estimated_dates')
def aseta_estimated_dates():
    """ syntymä- ja kuolinaikojen arvioiden asettaminen henkilöille """
    dburi = models.dbutil.get_server_location()
    message = models.datareader.set_estimated_dates()
    return render_template("talletettu.html", text=message, uri=dburi)


@app.route('/set/refnames')
def set_refnames():
    """ Setting reference names for all persons """
    dburi = models.dbutil.get_server_location()
    message = models.datareader.set_refnames()
    return render_template("talletettu.html", text=message, uri=dburi)


@app.route('/yhdista', methods=['POST'])
def nimien_yhdistely():
    """ Nimien listaus tietokannasta ehtolauseella
        oid=arvo        näyttää nimetyn henkilön
        names=arvo      näyttää henkilöt, joiden nimi alkaa arvolla
    """
    names = request.form['names']
    logging.debug('Poimitaan ' + names )
    return redirect(url_for('nayta_ehdolla', ehto='names='+names))


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
    models.dataupdater.joinpersons(base_id, join_ids)
    flash('Yhdistettiin (muka) ' + str(base_id) + " + " + str(join_ids) )
    return redirect(url_for('nayta_ehdolla', ehto='names='+names))

#  Käyttäjän lisääminen tapahtuu Flask-securityn metodeilla

# @app.route('/newuser', methods=['POST'])
# def new_user():
#     """ Lisää tai päivittää käyttäjätiedon


@app.route('/virhe_lataus/<int:code>/<text>')
def virhesivu(code, text=''):
    """ Virhesivu näytetään """
    logging.debug('Virhesivu ' + str(code) )
    return render_template("virhe_lataus.html", code=code, text=text)


# """ ----------------------------------------------------------------------------
#     Version 1 vanhoja harjoitussivuja ilman tietokantaa
# """
# 
# @app.route('/vanhat')
# def index_old():
#     """Vanhan aloitussivun piirtäminen"""
#     return render_template("index_1.html")
# 
# 
# @app.route('/lataa1a', methods=['POST'])
# def lataa1a():
#     """ Lataa tiedoston ja näyttää sen """
#     try:
#         infile = request.files['filenm']
#         logging.debug('Ladataan tiedosto ' + infile.filename)
#         models.loadfile.upload_file(infile)
#     except Exception as e:
#         return redirect(url_for('virhesivu', code=415, text=str(e)))
# 
#     return redirect(url_for('nayta1', filename=infile.filename, fmt='list'))
# 
# 
# @app.route('/lataa1b', methods=['POST'])
# def lataa1b():
#     """ Lataa tiedoston ja näyttää sen taulukkona """
#     infile = request.files['filenm']
#     try:
#         models.loadfile.upload_file(infile)
#     except Exception as e:
#         return redirect(url_for('virhesivu', code=1, text=str(e)))
# 
#     return redirect(url_for('nayta1', filename=infile.filename, fmt='table'))
# 
# 
# @app.route('/lista1/<string:fmt>/<string:filename>')
# def nayta1(filename, fmt):
#     """ tiedoston näyttäminen ruudulla """
#     try:
#         pathname = models.loadfile.fullname(filename)
#         with open(pathname, 'r', encoding='UTF-8') as f:
#             read_data = f.read()
#     except IOError as e:
#         return redirect(url_for('virhesivu', code=1, text=str(e)))
#     except UnicodeDecodeError as e:
#         return redirect(url_for('virhesivu', code=1, \
#                text="Tiedosto ei ole UTF-8. " + str(e)))
# 
#     # Vaihtoehto a:
#     if fmt == 'list':   # Tiedosto sellaisenaan
#         return render_template("lista1.html", name=pathname, data=read_data)
# 
#     # Vaihtoehto b: Luetaan tiedot taulukoksi
#     else:
#         try:
#             persons = models.datareader.henkilolista(pathname)
#             return render_template("table_persons.html", name=pathname, \
#                    persons=persons)
#         except Exception as e:
#             return redirect(url_for('virhesivu', code=1, text=str(e)))


""" ----------------------------- Käynnistys ------------------------------- """

if __name__ == '__main__':
    print("Käynnistys tehdään ohjelmalta /run.py tai /runssl.py")

