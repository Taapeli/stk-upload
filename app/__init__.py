from flask import Flask, session, request
from flask_babelex import Babel
from flask_security import current_user
import shareds

import logging
import os

# Create app
app = Flask(__name__, instance_relative_config=True)
shareds.app = app
print('Application instance path: ' + shareds.app.instance_path)


shareds.app.config.from_object('config')
shareds.app.config.from_pyfile('config.py')

class ContextFilter(logging.Filter):
    """
    This is a filter which injects contextual information into the log.
    """

    def __init__(self):
        self.user = "<Nobody>" # choice(ContextFilter.USERS)

    def filter(self, record):
        if hasattr(self,'user'):
            record.user = self.user
        else:
            record.user = '-'
            print("# setups.ContextFilter.filter: 'user' not defined")
        return True

def setup_logging():
    def need(key):
        if key in shareds.app.config:
            return shareds.app.config[key]
        print("Config param '{}' not found, exiting".format(key))
        exit(1)

    # Mapping of config file strings to constants known by Formatter class
    loglevels = { "NOTSET": logging.NOTSET,
                  "DEBUG": logging.DEBUG,
                  "INFO": logging.INFO,
                  "WARNING": logging.WARNING,
                  "ERROR": logging.ERROR,
                  "CRITICAL": logging.CRITICAL, }

    logdir = need('STK_LOGDIR')
    logfile = need('STK_LOGFILE')
    loglevel = need('STK_LOGLEVEL')

    # Name of out application level logger:
    loggername = 'stkserver'

    # Format of our application level log messages,
    # used for log parsing in app/bp/stat/models/logreader.py
    logformat = '%(asctime)s %(name)s %(levelname)s %(user)s %(message)s'

    if loglevel in loglevels:
        loglevel = loglevels[loglevel]
    else:
        print("Unknown loglevel '{}', using default level WARNING".format(loglevel))
        loglevel = logging.WARNING

    try:
        if not os.path.isdir(logdir):
            os.makedirs(logdir)
    except Exception as e:
        print("Can't create logging directory: {}: {}".format(logdir, e))
        exit(1)

    formatter = logging.Formatter(logformat)
    logger = logging.getLogger(loggername)

    fh = logging.FileHandler(logdir + '/' + logfile)
    fh.setLevel(loglevel)       # use same logging level for handler ...
    fh.setFormatter(formatter)

    logger.setLevel(loglevel)   # ... and logger
    logger.addFilter(ContextFilter())
    logger.addHandler(fh)
    logger.info("Starting")
    print('Käynnistys: {} logging {} file {}'.format(app, logger, fh.stream.name))
    return

setup_logging()

shareds.babel = Babel(shareds.app)
#-----------------------------------------------------------------------------
#  KEEP THIS AS THE FIRST REGISTERING BECAUSE OF FLASK TEMPLATE HANDLIND LOGIC
from bp.stk_security import bp as stk_security_bp
shareds.app.register_blueprint(stk_security_bp)
#-----------------------------------------------------------------------------

from bp.start import bp as start_bp
shareds.app.register_blueprint(start_bp)

from bp.gedcom import bp as gedcom_bp
shareds.app.register_blueprint(gedcom_bp)

from bp.scene import bp as scene_bp
shareds.app.register_blueprint(scene_bp)

from bp.tools import bp as tools_bp
shareds.app.register_blueprint(tools_bp)

from bp.gramps import bp as gramps_bp
shareds.app.register_blueprint(gramps_bp)

from bp.admin import bp as admin_bp
shareds.app.register_blueprint(admin_bp)

from bp.audit import bp as audit_bp
shareds.app.register_blueprint(audit_bp)

from bp.dupsearch import bp as dupsearch_bp
shareds.app.register_blueprint(dupsearch_bp)

from bp.api import bp as api_bp
shareds.app.register_blueprint(api_bp)

from bp.dbeditor import bp as dbeditor_bp
shareds.app.register_blueprint(dbeditor_bp)

from bp.refname_editor import bp as refname_editor_bp
shareds.app.register_blueprint(refname_editor_bp)

from bp.stat import bp as stat_bp
shareds.app.register_blueprint(stat_bp)

@shareds.babel.localeselector
def get_locale():
    reqlang = request.args.get('lang')
    if reqlang:
        session['lang'] = reqlang
    else:
        reqlang = session.get('lang')
        if not reqlang:
            if current_user.is_authenticated: 
                reqlang = current_user.language
                session['lang'] = reqlang
    return reqlang

from flask_login import user_logged_in, user_logged_out
from models import syslog

def log_user_logged_in(sender, user, **extra):
    syslog.log(type="user logged in")
    session['lang'] = current_user.language

def log_user_logged_out(sender, user, **extra):
    syslog.log(type="user logged out")

syslog.syslog_init()
syslog.log(type="application initialized")

user_logged_in.connect(log_user_logged_in,shareds.app)
user_logged_out.connect(log_user_logged_out,shareds.app)

import setups
