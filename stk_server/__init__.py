from flask import Flask
import shareds
# Create app
app = Flask(__name__, instance_relative_config=True)
shareds.app = app
print('Application instance path: ' + shareds.app.instance_path)
app.config.from_object('config')
app.config.from_pyfile('config.py')
import setups