# Flask routes program for Stk application tools blueprint
# @ Sss 2016
# JMä 3.1.2019

#import urllib

import logging 
logger = logging.getLogger('stkserver')
import time

from flask import render_template, request, redirect, url_for, flash #, jsonify
from flask_security import roles_accepted, login_required #, current_user ,roles_required
from flask_babelex import _

#import shareds
from models.gen.person_name import Name
from models import datareader          # Tietojen haku kannasta (tai työtiedostosta)
from .models import dataupdater         # Tietojen päivitysmetodit: joinpersons

from . import bp

@bp.route('/tables')
@login_required
@roles_accepted('audit', 'admin')
def datatables():
    """ Home page for table format tools """
    return render_template("/tools/tables.html")


""" ---------------- Other listings (Table format) ----------------------------
"""

@bp.route('/listall/<string:subj>')
@login_required
@roles_accepted('audit', 'admin')
def show_table_data(subj):
    """ Person etc listings
        tietokannan henkiloiden tai käyttäjien näyttäminen ruudulla 
    """
    t0 = time.time()
    if request.args:
        args=request.args
    else:
        args={}
    logger.info(f"-> bp.tools.routes.show_table_data theme={subj}")

    if subj == "persons":
        persons = datareader.read_persons_with_events(args=args)
        return render_template("/tools/table_persons.html", persons=persons, 
                               elapsed=time.time()-t0)
    elif subj == "surnames":
        surnames = Name.get_surnames()
        return render_template("/tools/table_surnames.html", surnames=surnames, elapsed=time.time()-t0)
    elif subj == 'events_wo_cites':
        headings, titles, lists = datareader.read_events_wo_cites()
        return render_template("/tools/table_of_data.html",
               headings=headings, titles=titles, lists=lists, elapsed=time.time()-t0)
    elif subj == 'events_wo_place':
        headings, titles, lists = datareader.read_events_wo_place()
        return render_template("/tools/table_of_data.html",
               headings=headings, titles=titles, lists=lists, elapsed=time.time()-t0)
    elif subj == 'families':
        families = datareader.read_families()
        return render_template("/tools/table_families.html", 
        families=families, elapsed=time.time()-t0)
    elif subj == 'notes':
        titles, objs = datareader.get_note_list()
        return render_template("/tools/table_of_objects.html",
                               headings=(_('Note List'), _('Note Items')),
                               titles=titles, objs=objs, elapsed=time.time()-t0)
    elif subj == 'media':
        media = datareader.read_medias()
        return render_template("/tools/table_media.html",
                               media=media, elapsed=time.time()-t0)
    elif subj == 'people_wo_birth':
        headings, titles, lists = datareader.read_people_wo_birth()
        return render_template("/tools/table_of_data.html",
               headings=headings, titles=titles, lists=lists, elapsed=time.time()-t0)
    elif subj == 'old_people_top':
        headings, titles, lists = datareader.read_old_people_top()
        return render_template("/tools/table_of_data.html",
               headings=headings, titles=titles, lists=lists, elapsed=time.time()-t0)
    elif subj == 'repositories':
        titles, obj = datareader.get_repositories()
#         for r in obj:
#             r.type = jinja_filters.translate(r.type, 'rept', 'fi')
        return render_template("/tools/table_of_objects.html",
                               headings=(_('Repositories'), _('Repository data')),
                               titles=titles, objs=obj, elapsed=time.time()-t0)
    elif subj == 'same_birthday':
        ids = datareader.read_same_eventday('Birth')
        return render_template("/tools/ng_same_person.html", subj=subj, ids=ids, elapsed=time.time()-t0)
    elif subj == 'same_deathday':
        ids = datareader.read_same_eventday('Death')
        return render_template("/tools/ng_same_person.html", subj=subj, ids=ids, elapsed=time.time()-t0)
    elif subj == 'same_name':
        ids = datareader.read_same_name()
        return render_template("/tools/ng_same_name.html", ids=ids, elapsed=time.time()-t0)
    elif subj == 'sources':
        sources = datareader.read_sources()
        return render_template("/tools/table_sources.html", sources=sources, elapsed=time.time()-t0)
    elif subj == 'sources_wo_cites':
        headings, titles, lists = datareader.read_sources_wo_cites()
        return render_template("/tools/table_of_data.html", headings=headings,
                               titles=titles, lists=lists, elapsed=time.time()-t0)
    elif subj == 'sources_wo_repository':
        headings, titles, lists = datareader.read_sources_wo_repository()
        return render_template("/tools/table_of_data.html",
               headings=headings, titles=titles, lists=lists, elapsed=time.time()-t0)
    elif subj == 'places':
        headings, titles, lists = datareader.read_places()
        return render_template("/tools/table_of_data.html", headings=headings,
                               titles=titles, lists=lists, elapsed=time.time()-t0)
    else:
        return redirect(url_for('virhesivu', code=1, text= \
            _('Material type') + " '" + subj + "' "+ _('processing still missing')))


@bp.route('/list/refnames', defaults={'reftype': None})
def list_refnames(reftype):
    """ Table of reference names """
    names = datareader.read_refnames()
    logger.info(f"-> bp.tools.routes.list_refnames n={len(names)}")
    print(names[0])
    return render_template("/tools/table_refnames.html", names=names)


# Ei käytössä?
# @bp.route('/lista/people_by_surname/', defaults={'surname': ""})
# def list_people_by_surname(surname):
#     """ Table of Persons with identical surname
#         henkilöiden, joilla on sama sukunimi näyttäminen ruudulla 
#     """
#     people = datareader.get_people_by_surname(surname)
#     return render_template("/tools/table_people_by_surname.html",
#                            surname=surname, people=people)


    #  linkki oli sukunimiluettelosta
@bp.route('/lista/person_data/<string:uniq_id>')
def show_person_data(uniq_id):
    """ Table of a Person selected by id(Person)
        linkki oli sukunimiluettelosta
    """
    person, events, photos, sources, families = datareader.get_person_data_by_id(uniq_id)
    logger.info(f"-> bp.tools.routes.show_person_data")
    logger.debug("Got {} persons, {} events, {} photos, {} sources, {} families".\
                 format(len(person), len(events), len(photos), len(sources), len(families)))
    return render_template("/tools/obsolete_table_person_by_id.html",
                       person=person, events=events, photos=photos, sources=sources)


@bp.route('/compare/<string:cond>')
def compare_person_page(cond):
    """ Vertailu - henkilön tietojen näyttäminen ruudulla
        cond = 'uniq_id=key1,key2'    the keys are db keys id(Person)
    """
    key, value = cond.split('=')
    uniq_id_1, uniq_id_2 = value.split(',')
    logger.info(f"-> bp.tools.routes.compare_person_page {cond}")
    try:
        if key == 'uniq_id':
            person, events, photos, sources, families = \
                datareader.get_person_data_by_id(int(uniq_id_1))
            person2, events2, photos2, sources2, families2 = \
                datareader.get_person_data_by_id(int(uniq_id_2))
            for f in families:
                print (_('{} in Family {}/{}').format(f.role, f.uniq_id, f.id))
                if f.mother:
                    print(_(' Mother: {}/{} p. {}').format(f.mother.uniq_id, f.mother.id, f.mother.birth_date))
                if f.father:
                    print(_(' Father: {}/{} p. {}').format(f.father.uniq_id, f.father.id, f.father.birth_date))
                if f.children:
                    for c in f.children:
                        print(_(' Child ({}): {}/{} * {}').format(c.sex_str(), c.uniq_id, c.id, c.birth_date))
        else:
            raise(KeyError(_('Wrong Search key')))
    except KeyError as e:
        return redirect(url_for('virhesivu', code=1, text=str(e)))
    return render_template("/tools/ng_compare.html", person=person, events=events, 
                           photos=photos, sources=sources,  families=families,
                           person2=person2, events2=events2, 
                           photos2=photos2, sources2=sources2, families2=families2)


# @bp.route('/compare2/<string:ehto>')
# def compare_person_page2(cond):
#     """ Vertailu - henkilön tietojen näyttäminen ruudulla
#         uniq_id=arvo    näyttää henkilön tietokanta-avaimen mukaan
#     """
#     key, value = cond.split('=')
#     try:
#         if key == 'uniq_id':
#             person, events, photos, sources, families = \
#                 datareader.get_person_data_by_id(value)
#             for f in families:
#                 print (_('{} in Family {}/{}').format(f.role, f.uniq_id, f.id))
#                 if f.mother:
#                     print(_(' Mother: {}/{} p. {}').format(f.mother.uniq_id, f.mother.id, f.mother.birth_date))
#                 if f.father:
#                     print(_(' Father: {}/{} p. {}').format(f.father.uniq_id, f.father.id, f.father.birth_date))
#                 if f.children:
#                     for c in f.children:
#                         print(_(' Child ({}): {}/{} * {}').format(c.sex, c.uniq_id, c.id, c.birth_date))
#         else:
#             raise(KeyError(_('Wrong Search key')))
#     except KeyError as e:
#         return redirect(url_for('virhesivu', code=1, text=str(e)))
#     return render_template("compare2.html",
#         person=person, events=events, photos=photos, sources=sources, families=families)


@bp.route('/lista/baptism_data/<int:uniq_id>')
def show_baptism_data(uniq_id):
    """ Table of a baptism Event selected by id(Event)
        kastetapahtuman tietojen näyttäminen ruudulla 
    """
    event, persons = datareader.get_baptism_data(uniq_id)
    logger.info(f"-> bp.tools.routes.show_baptism_data")
    return render_template("/tools/table_baptism_data.html",
                           event=event, persons=persons)


@bp.route('/lista/family_data/<string:uniq_id>')
def show_family_data(uniq_id):
    """ Table of families of a Person
        henkilön perheen tietojen näyttäminen ruudulla 
    """
    return "bp.tools.routes.show_family_data poistettu 17.5.2020"
#     person, families = datareader.get_families_data_by_id(uniq_id)
#     return render_template("/tools/obsolete_table_families_by_id.html",
#                            person=person, families=families)


@bp.route('/pick/<string:cond>')
def pick_selection(cond):
    """ Table of objects selected by the argument
    """
    key, value = cond.split('=')
    logger.info(f"-> bp.tools.routes.pick_selection theme={key}")
    try:
        if key == 'name':               # A prototype for later development
            value=value.title()
            persons = datareader.read_persons_with_events(keys=('surname',value))
            return render_template("/tools/join_persons.html",
                                   persons=persons, pattern=value)
        elif key == 'cite_sour_repo':   # from obsolete_table_person_by_id.html Ei käytössä
            return "bp.tools.routes.pick_selection/cite_sour_repo poistettu 17.5.2020"
#             events = datareader.read_cite_sour_repo(uniq_id=value)
#             return render_template("/tools/cite_sour_repo.html",
#                                    events=events)
#         elif key == 'repo_uniq_id':     # from cite_sourc_repo.html, 
#                                         # ng_table_repositories.html,
#                                         # table_repositories.html
#             repositories = datareader.read_repositories(uniq_id=value)
#             return render_template("repo_sources.html",
#                                    repositories=repositories)
        elif key == 'source_uniq_id':   # from cite_sourc_repo.html, table_sources.html
            sources = datareader.read_sources(uniq_id=int(value))
            return render_template("/tools/source_citations.html",
                                   sources=sources)
        elif key == 'uniq_id':          # from table_persons2.html
            persons = datareader.read_persons_with_events(keys=("uniq_id",value))
            return render_template("/tools/person2.html", persons=persons)
        else:
            raise(KeyError(_('Only the OID can retrieve')))
    except KeyError as e:
        return redirect(url_for('virhesivu', code=1, text=str(e)))


""" -------------------------- Yleinen virhesivu ------------------------------
"""

#TODO Pitäisi korvata jollain ilmoituskentällä ...
@bp.route('/virhe_lataus/<int:code>/<text>')
def virhesivu(code, text=''):
    """ Virhesivu näytetään """
    logging.debug('Virhesivu ' + str(code) )
    return render_template("/tools/virhe_lataus.html", code=code, text=text)



""" ------------------------ Obsolete operations? ------------------------------
"""


@bp.route('/lista/person_data/<string:uniq_id>')
def show_person_data_dbl(uniq_id):
    """ Table of Person data
        Henkilön tietojen näyttäminen ruudulla 
        Linkki oli sukunimiluettelosta
    """
    person, events, photos, sources, families = \
        datareader.get_person_data_by_id(uniq_id)
    logger.info(f"-> bp.tools.routes.show_person_data_dbl")
    logger.debug("Got {} persons, {} events, {} photos, {} sources, {} families".\
                 format(len(person), len(events), len(photos), len(sources), len(families)))
    return render_template("/tools/obsolete_table_person_by_id.html",
                       person=person, events=events, photos=photos, sources=sources)


# @bp.route('/compare/<string:cond>')
# def compare_person_page_dbl(cond):
#     """ Vertailu - henkilön tietojen näyttäminen ruudulla
#         cond='uniq_id=value'    pick person by db key
#     """
#     key, value = cond.split('=')
#     try:
#         if key == 'uniq_id':
#             person, events, photos, sources, families = \
#                 datareader.get_person_data_by_id(value)
#             for f in families:
#                 print (_('{} in Family {}/{}').format(f.role, f.uniq_id, f.id))
#                 if f.mother:
#                     print(_(' Mother: {}/{} p. {}').format(f.mother.uniq_id, f.mother.id, f.mother.birth_date))
#                 if f.father:
#                     print(_(' Father: {}/{} p. {}').format(f.father.uniq_id, f.father.id, f.father.birth_date))
#                 if f.children:
#                     for c in f.children:
#                         print(_(' Child ({}): {}/{} * {}').format(c.sex_str(), c.uniq_id, c.id, c.birth_date))
#         else:
#             raise(KeyError(_('Wrong Search key')))
#     except KeyError as e:
#         return redirect(url_for('virhesivu', code=1, text=str(e)))
#     return render_template("/tools/compare3.html",
#         person=person, events=events, photos=photos, sources=sources, families=families)


# @bp.route('/compare2/<string:cond>')
# def compare_person_page2_dbl(cond):
#     """ Vertailu - henkilön tietojen näyttäminen ruudulla
#         uniq_id=arvo    näyttää henkilön tietokanta-avaimen mukaan
#     """
#     key, value = cond.split('=')
#     try:
#         if key == 'uniq_id':
#             person, events, photos, sources, families = \
#                 datareader.get_person_data_by_id(value)
#             for f in families:
#                 print (_("{} in the family {} / {}").format(f.role, f.uniq_id, f.id))
#                 if f.mother:
#                     print(_("  Mother: {} / {} s. {}").format(f.mother.uniq_id, f.mother.id, f.mother.birth_date))
#                 if f.father:
#                     print(_("  Father:  {} / {} s. {}").format(f.father.uniq_id, f.father.id, f.father.birth_date))
#                 if f.children:
#                     for c in f.children:
#                         print(_("    Child ({}): {} / {} *{}").format(c.sex_str(), c.uniq_id, c.id, c.birth_date))
#         else:
#             raise(KeyError(_('Wrong Search key')))
#     except KeyError as e:
#         return redirect(url_for('virhesivu', code=1, text=str(e)))
#     return render_template("/tools/compare2.html", person=person, events=events, 
#                            photos=photos, sources=sources, families=families)

@bp.route('/lista/family_data/<string:uniq_id>')
def show_family_data_dbl(uniq_id):
    """ henkilön perheen tietojen näyttäminen ruudulla """
    return "bp.tools.routes.show_family_data_dbl poistettu 17.5.2020"
#     person, families = datareader.get_families_data_by_id(uniq_id)
#     return render_template("/tools/obsolete_table_families_by_id.html",
#                            person=person, families=families)


@bp.route('/yhdista', methods=['POST'])
def nimien_yhdistely():
    """ Nimien listaus tietokannasta ehtolauseella
        oid=arvo        näyttää nimetyn henkilön
        names=arvo      näyttää henkilöt, joiden nimi alkaa arvolla
    """
    names = request.form['names']
    logging.debug('Poimitaan ' + names )
    return redirect(url_for('pick_selection', ehto='names='+names))


@bp.route('/samahenkilo', methods=['POST'])
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

