from flask import Flask
from flask_cors import CORS
from flask_caching import Cache

import os
import sys

from utils.schema import db

app = Flask(__name__)
cache = Cache(app, config={'CACHE_TYPE': 'simple'})

# donde corre el script
script_directory = os.path.dirname(sys.executable if getattr(sys, 'frozen', False) else __file__)


user = 'rad710'
password = 'hola12345'
host = 'rad710.mysql.pythonanywhere-services.com'
db = 'rad710$dyrtransportes' # dbFlask was created as a PythonAnywhere MySQL database

# connection string: mysql://user:pword@host/db
app.config['SQLALCHEMY_DATABASE_URI'] = f'mysql://{user}:{password}@{host}/{db}'

db.init_app(app)

# Wrap db.create_all() in an app context
with app.app_context():
    db.create_all()


CORS(app)