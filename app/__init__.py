from flask import Flask
import shareds
# Create app
app = Flask(__name__, instance_relative_config=True)
shareds.app = app
print('Application instance path: ' + shareds.app.instance_path)

from gedcom import bp as gedcom_bp
app.register_blueprint(gedcom_bp)

from narrative import bp as narrative_bp
app.register_blueprint(narrative_bp)

from admin import bp as admin_bp
app.register_blueprint(admin_bp)

app.config.from_object('config')
app.config.from_pyfile('config.py')
import setups