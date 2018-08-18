from flask import Flask
import shareds
# Create app
app = Flask(__name__, instance_relative_config=True)
shareds.app = app
print('Application instance path: ' + shareds.app.instance_path)

from bp.gedcom import bp as gedcom_bp
app.register_blueprint(gedcom_bp)

from bp.scene import bp as scene_bp
app.register_blueprint(scene_bp)

from bp.gramps import bp as gramps_bp
app.register_blueprint(gramps_bp)

from bp.admin import bp as admin_bp
app.register_blueprint(admin_bp)

app.config.from_object('config')
app.config.from_pyfile('config.py')
import setups