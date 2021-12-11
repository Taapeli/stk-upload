# coding=UTF-8

#   Isotammi Genealogical Service for combining multiple researchers' results.
#   Created in co-operation with the Genealogical Society of Finland.
#
#   Copyright (C) 2016-2021  Juha Mäkeläinen, Jorma Haapasalo, Kari Kujansuu,
#                            Timo Nallikari, Pekka Valta
#
#   This program is free software: you can redistribute it and/or modify
#   it under the terms of the GNU General Public License as published by
#   the Free Software Foundation, either version 2 of the License, or
#   (at your option) any later version.
#
#   This program is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU General Public License for more details.
#
#   You should have received a copy of the GNU General Public License
#   along with this program.  If not, see <http://www.gnu.org/licenses/>.

"""
    Flask routes program for Stk application
    @ Sss 2016
    JMä 29.12.2015 - 4.1.2019
"""

# Blacked 2021-05-18 / JMä
import logging
import urllib
from operator import itemgetter

logger = logging.getLogger("stkserver")

from flask import render_template, request, redirect, url_for# , session
from flask_security import login_required, logout_user, current_user
from flask_babelex import get_locale
from werkzeug.exceptions import HTTPException

import shareds
from bl.person import PersonReader
from ui.context import UserContext

app = shareds.app
if not app:
    raise RuntimeError("Start this application in '..' from 'run.py' or 'runssl.py'")

@app.before_request
def before_request():
    """Set user variable for log message filtering"""
    for filt in logger.filters:
        if current_user.is_authenticated:
            filt.user = current_user.username
        else:
            filt.user = "<anon>"
        # print (f'routes.before_request current_user for {logger.name}: {filt.user}')

@app.errorhandler(HTTPException)
def handle_bad_request(e):
    return render_template(
        "unexpected_error.html",
        text=e.get_description(),
    ), e.code

@app.route("/")
def entry():
    """Home page needing authentication.

    1. a guest user (from login page or home button) or anonymous user (home)
    2. authenticated user

    When not authenticated, should show a login page first!
    """
    if current_user.has_role("guest"):
        #        print("Authenticated guest user at entry")
        logger.info(f"-> routes.entry/guest")
        logout_user()

    if current_user.is_authenticated and current_user.has_role("to_be_approved"):
        # Home page for logged in user
        logger.info(f"-> routes.entry/join")
        return redirect(url_for("join"))

    if current_user.is_authenticated:
        # Home page for logged in user
        logger.info(f"-> routes.entry/user")
        return redirect(url_for("start_logged"))

    logger.info(f"-> routes.entry/-")
    lang = get_locale().language
    demo_site = f"{app.config['DEMO_URL']}"
    logger.debug(
        f"-> routes.entry auth={current_user.is_authenticated} demo={demo_site}"
    )

    surnamestats = []
    is_demo = shareds.app.config.get("DEMO", False)
    if is_demo:
        # Get surname cloud data
        u_context = UserContext()
        u_context.user = None

        with PersonReader("read", u_context) as service:
            print(f"#> routes.entry: datastore = {service}")

            minfont = 6
            maxfont = 20
            # maxnames = 40
            surnamestats = service.get_surname_list(40)
            print(f"#start_logged DEMO: show {len(surnamestats)} surnames")
            for i, stat in enumerate(surnamestats):
                stat["order"] = i
                stat["fontsize"] = maxfont - i * (maxfont - minfont) / len(surnamestats)
            surnamestats.sort(key=itemgetter("surname"))

    # If not logged in, a login page is shown here first
    return render_template(
        "/index_demo.html", demo_site=demo_site, lang=lang, surnamestats=surnamestats
    )


""" -------------------------- Yleinen virhesivu ------------------------------
"""

# TODO Pitäisi korvata jollain ilmoituskentällä ...
@app.route("/virhe_lataus/<int:code>/<text>")
def virhesivu(code, text=""):
    """ Virhesivu näytetään """
    logger.debug(f"-> routes.virhesivu {code} {text}")
    return render_template("virhe_lataus.html", code=code, text=text)


"""
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
    """


@app.route("/help")
@login_required
def app_help():
    url = request.args.get("url")
    path = urllib.parse.urlparse(url)
    return "Help for {}".format(path.path)


# ------------------------------ Filters ---------------------------------------
from ui import jinja_filters
