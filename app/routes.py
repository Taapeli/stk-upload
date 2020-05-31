# coding=UTF-8
# Flask routes program for Stk application
# @ Sss 2016
# JMä 29.12.2015 - 4.1.2019

import urllib

import logging 
logger = logging.getLogger('stkserver')

from flask import render_template, request, redirect, url_for #, g, flash
from flask_security import login_required, logout_user, current_user # ,roles_required
from flask_babelex import get_locale

import shareds

app = shareds.app
if not app:
    raise RuntimeError("Start this application in '..' from 'run.py' or 'runssl.py'")


@app.before_request
def before_request():
    ''' Set user variable for log message filtering
    '''
    for filt in logger.filters:
        if current_user.is_authenticated:
            filt.user = current_user.username
        else:
            filt.user = '<anon>'
        #print (f'routes.before_request current_user for {logger.name}: {filt.user}')


@app.route('/')
def entry():
    ''' Home page needing autentication.

        1. a guest user (from login page or home button) or anonymous user (home)
        2. authenticated user

        When not autenticated, should show a login page first!
    '''
    if current_user.has_role("guest"):
#        print("Authenticated guest user at entry") 
        logger.info(f'-> routes.entry/guest')
        logout_user()

    if current_user.is_authenticated:
        # Home page for logged in user
        logger.info(f'-> routes.entry/user')
        return redirect(url_for('start_logged'))

    logger.info(f'-> routes.entry/-')
    lang = get_locale().language
    demo_site = f"{app.config['DEMO_URL']}?lang={lang}"
    logger.debug(f'-> routes.entry auth={current_user.is_authenticated} demo={demo_site}')

    # If not logged in, a login page is shown here first
    return render_template('/index_entry.html', demo_site=demo_site)

""" -------------------------- Yleinen virhesivu ------------------------------
"""

#TODO Pitäisi korvata jollain ilmoituskentällä ...
@app.route('/virhe_lataus/<int:code>/<text>')
def virhesivu(code, text=''):
    """ Virhesivu näytetään """
    logger.debug(f'-> routes.virhesivu {code} {text}')
    return render_template("virhe_lataus.html", code=code, text=text)
'''
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
    #return request.accept_languages.best_match(get('LANGUAGES'))
    '''

@app.route('/help')
@login_required
def app_help():
    url = request.args.get("url")
    path = urllib.parse.urlparse(url)
    return "Help for {}".format(path.path)

# ------------------------------ Filters ---------------------------------------
from templates import jinja_filters
