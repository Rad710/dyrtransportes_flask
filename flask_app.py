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

# poner base de datos en mismo directorio que el script
DATABASE_PATH = os.path.join(script_directory, "pagina_web.db")

app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{DATABASE_PATH}'

db.init_app(app)

# Wrap db.create_all() in an app context
with app.app_context():
    db.create_all()


CORS(app)