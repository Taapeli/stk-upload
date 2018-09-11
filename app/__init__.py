from flask import Flask
import shareds
# Create app
shareds.app = Flask(__name__, instance_relative_config=True)
app = shareds.app 
print('Application instance path: ' + shareds.app.instance_path)

from bp.gedcom import bp as gedcom_bp
shareds.app.register_blueprint(gedcom_bp)

from bp.scene import bp as scene_bp
shareds.app.register_blueprint(scene_bp)

from bp.gramps import bp as gramps_bp
shareds.app.register_blueprint(gramps_bp)

from bp.admin import bp as admin_bp
shareds.app.register_blueprint(admin_bp)

from bp.stk_security import bp as security_bp
shareds.app.register_blueprint(security_bp)

shareds.app.config.from_object('config')
shareds.app.config.from_pyfile('config.py')
import setups