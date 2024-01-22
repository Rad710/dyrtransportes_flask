from flask import Flask
from flask_cors import CORS
from flask_caching import Cache

import os
import sys
from dotenv import load_dotenv

from utils.schema import db

app = Flask(__name__)
cache = Cache(app, config={'CACHE_TYPE': 'simple'})

# where script is executed
script_directory = os.path.dirname(sys.executable if getattr(sys, 'frozen', False) else __file__)

load_dotenv()

# DB_USERNAME = 'rad710'
# DB_PASSWORD = 'hola12345'
# DB_HOST = 'rad710.mysql.pythonanywhere-services.com'
# DB_NAME = 'rad710$dyrtransportes'

DB_USERNAME = os.getenv('DB_USERNAME')
DB_PASSWORD = os.getenv('DB_PASSWORD')
DB_HOST = os.getenv('DB_HOST')
DB_NAME = os.getenv('DB_NAME')

print('DB_HOST: ', DB_HOST)

# connection string: mysql://user:pword@host/db
connection_string = f'mysql://{DB_USERNAME}:{DB_PASSWORD}@{DB_HOST}/{DB_NAME}'
app.config['SQLALCHEMY_DATABASE_URI'] = connection_string
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {'pool_recycle' : 280}

db.init_app(app)

# Wrap db.create_all() in an app context
with app.app_context():
    db.create_all()

CORS(app)