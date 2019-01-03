# coding=UTF-8
# Flask routes program for Stk application
# @ Sss 2016
# JMä 29.12.2015

import urllib

import logging 
logger = logging.getLogger('stkserver')
import time

from flask import render_template, request, redirect, url_for, flash, g
from flask_security import login_required, roles_accepted, current_user # ,roles_required
from flask_babelex import _

import shareds
from models.gen.person_name import Name
# from models import dbutil
# from models import loadfile          # Datan lataus käyttäjältä
from models import datareader          # Tietojen haku kannasta (tai työtiedostosta)
from models import dataupdater         # Tietojen päivitysmetodit


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


@shareds.app.route('/tables')
#     @roles_accepted('member', 'admin')
@roles_accepted('member', 'admin')
def datatables():
    """ Home page for table format tools """
    return render_template("/tools/tables.html")

# Admin start page
@shareds.app.route('/admin',  methods=['GET', 'POST'])
@login_required
@roles_accepted('admin', 'master')
def admin():
    """ Home page for administrator """    
    return render_template('/admin/admin.html')

# Narrative start page
@shareds.app.route('/scene',  methods=['GET', 'POST'])
def scene():
    """ Home page for scene narrative pages ('kertova') """    
    return render_template('/scene/persons.html')


# """ ---------------- Other listings (Table format) ----------------------------
# """
# All moved to bp.tools.routes
# 
# @shareds.app.route('/lista/<string:subj>')
# def show_table_data(subj):
# 
# @shareds.app.route('/list/refnames', defaults={'reftype': None})
# def list_refnames(reftype):
# 
# @shareds.app.route('/lista/people_by_surname/', defaults={'surname': ""})
# def list_people_by_surname(surname):
# 
#     #  linkki oli sukunimiluettelosta
# @shareds.app.route('/lista/person_data/<string:uniq_id>')
# def show_person_data(uniq_id):
# 
# @shareds.app.route('/compare/<string:cond>')
# def compare_person_page(cond):
#
# @shareds.app.route('/compare2/<string:ehto>')
# def compare_person_page2(cond):
#
# @shareds.app.route('/lista/baptism_data/<int:uniq_id>')
# def show_baptism_data(uniq_id):
# 
# @shareds.app.route('/lista/family_data/<string:uniq_id>')
# def show_family_data(uniq_id):
# 
# @shareds.app.route('/pick/<string:cond>')
# def pick_selection(cond):
#     """ Table of objects selected by the argument """

""" -------------------------- Yleinen virhesivu ------------------------------
"""

#TODO Pitäisi korvata jollain ilmoituskentällä ...
@app.route('/virhe_lataus/<int:code>/<text>')
def virhesivu(code, text=''):
    """ Virhesivu näytetään """
    logging.debug('Virhesivu ' + str(code) )
    return render_template("virhe_lataus.html", code=code, text=text)



# """ ------------------------ Obsolete operations? ------------------------------
# """
# 
# 
# @shareds.app.route('/lista/person_data/<string:uniq_id>')
# def show_person_data_dbl(uniq_id):
#     """ Table of Person data
#         Henkilön tietojen näyttäminen ruudulla 
#         Linkki oli sukunimiluettelosta
#     """
#     person, events, photos, sources, families = \
#         datareader.get_person_data_by_id(uniq_id)
#     logger.debug("Got {} persons, {} events, {} photos, {} sources, {} families".\
#                  format(len(person), len(events), len(photos), len(sources), len(families)))
#     return render_template("table_person_by_id.html",
#                        person=person, events=events, photos=photos, sources=sources)
# 
# 
# @shareds.app.route('/compare/<string:cond>')
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
#                         print(_(' Child ({}): {}/{} * {}').format(c.gender, c.uniq_id, c.id, c.birth_date))
#         else:
#             raise(KeyError(_('Wrong Search key')))
#     except KeyError as e:
#         return redirect(url_for('virhesivu', code=1, text=str(e)))
#     return render_template("compare3.html",
#         person=person, events=events, photos=photos, sources=sources, families=families)
# 
# 
# @shareds.app.route('/compare2/<string:cond>')
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
#                         print(_("    Child ({}): {} / {} *{}").format(c.gender, c.uniq_id, c.id, c.birth_date))
#         else:
#             raise(KeyError(_('Wrong Search key')))
#     except KeyError as e:
#         return redirect(url_for('virhesivu', code=1, text=str(e)))
#     return render_template("compare2.html", person=person, events=events, 
#                            photos=photos, sources=sources, families=families)
# 
# 
# @shareds.app.route('/lista/family_data/<string:uniq_id>')
# def show_family_data_dbl(uniq_id):
#     """ henkilön perheen tietojen näyttäminen ruudulla """
#     person, families = datareader.get_families_data_by_id(uniq_id)
#     return render_template("table_families_by_id.html",
#                            person=person, families=families)
# 
# 
# @shareds.app.route('/yhdista', methods=['POST'])
# def nimien_yhdistely():
#     """ Nimien listaus tietokannasta ehtolauseella
#         oid=arvo        näyttää nimetyn henkilön
#         names=arvo      näyttää henkilöt, joiden nimi alkaa arvolla
#     """
#     names = request.form['names']
#     logging.debug('Poimitaan ' + names )
#     return redirect(url_for('pick_selection', ehto='names='+names))
# 
# 
# @shareds.app.route('/samahenkilo', methods=['POST'])
# def henkiloiden_yhdistely():
#     """ Yhdistetään base-henkilöön join-henkilöt tapahtumineen,
#         minkä jälkeen näytetään muuttunut henkilölista
#     """
#     names = request.form['names']
#     print (dir(request.form))
#     base_id = request.form['base']
#     join_ids = request.form.getlist('join')
#     #TODO lisättävä valitut ref.nimet, jahka niitä tulee
#     dataupdater.joinpersons(base_id, join_ids)
#     flash('Yhdistettiin (muka) ' + str(base_id) + " + " + str(join_ids) )
#     return redirect(url_for('pick_selection', ehto='names='+names))
################################################################################
    
# i18n: https://blog.miguelgrinberg.com/post/the-flask-mega-tutorial-part-xiv-i18n-and-l10n-legacy
from flask_babelex import Babel
from flask_babelex import _

babel = Babel(app)

@babel.localeselector
def get_locale():
    try:
        g.locale = current_user.language 
        return current_user.language
    except:
        pass
    return "fi"
    #return "en"
    #return request.accept_languages.best_match(LANGUAGES)

@shareds.app.route('/help')
@login_required
def app_help():
    url = request.args.get("url")
    path = urllib.parse.urlparse(url)
    return "Help for {}".format(path.path)

# ------------------------------ Filters ---------------------------------------
from templates import jinja_filters
