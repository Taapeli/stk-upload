from flask import Flask, session, request
from flask_babelex import Babel
from flask_security import current_user
import logging

import shareds
# Create app
app = Flask(__name__, instance_relative_config=True)
shareds.app = app
print('Application instance path: ' + shareds.app.instance_path)


shareds.app.config.from_object('config')
shareds.app.config.from_pyfile('config.py')

_level = shareds.app.config.get('STK_LOG_LEVEL')
if _level:
    print (f"stkserver log level set to {_level}")
    logging.getLogger('stkserver').setLevel(_level)

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

import logging
syslog.syslog_init()
syslog.log(type="application initialized")
user_logged_in.connect(log_user_logged_in,shareds.app)
user_logged_out.connect(log_user_logged_out,shareds.app)
 
import setups