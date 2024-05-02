from flask import Flask
from flask.logging import create_logger
from flask_cors import CORS
from flask_caching import Cache
from flask_migrate import Migrate

import os
import sys
from dotenv import load_dotenv

import utils.schema as schema

app = Flask(__name__)
logger = create_logger(app)

cache = Cache(app, config={'CACHE_TYPE': 'simple'})

# where script is executed
script_directory = os.path.dirname(sys.executable if getattr(sys, 'frozen', False) else __file__)

load_dotenv()

DB_USERNAME = os.getenv('DB_USERNAME')
DB_PASSWORD = os.getenv('DB_PASSWORD')
DB_HOST = os.getenv('DB_HOST')
DB_NAME = os.getenv('DB_NAME')

print('DB_HOST: ', DB_HOST)

connection_string = f'mysql://{DB_USERNAME}:{DB_PASSWORD}@{DB_HOST}/{DB_NAME}'
app.config['SQLALCHEMY_DATABASE_URI'] = connection_string
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {'pool_recycle' : 280}


print("Initializing app...")
schema.db.init_app(app)
migrate = Migrate(app, schema.db)

# Wrap db.create_all() in an app context
print("Connecting to DB...")

with app.app_context():
    schema.db.create_all()

CORS(app)