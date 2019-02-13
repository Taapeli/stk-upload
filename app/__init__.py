from flask import Flask, session, request
from flask_babelex import Babel
from flask_security import current_user
import shareds
# Create app
app = Flask(__name__, instance_relative_config=True)
shareds.app = app
print('Application instance path: ' + shareds.app.instance_path)


shareds.app.config.from_object('config')
shareds.app.config.from_pyfile('config.py')

shareds.babel = Babel(shareds.app)

from bp.start import bp as start_bp
shareds.app.register_blueprint(start_bp)

from bp.stk_security import bp as stk_security_bp
shareds.app.register_blueprint(stk_security_bp)

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
 
import setups