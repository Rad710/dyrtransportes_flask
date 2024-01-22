from flask import Flask
from flask_cors import CORS
from flask_caching import Cache

import os
import sys
import time
from dotenv import load_dotenv

from utils.schema import db

app = Flask(__name__)
cache = Cache(app, config={'CACHE_TYPE': 'simple'})

# where script is executed
script_directory = os.path.dirname(sys.executable if getattr(sys, 'frozen', False) else __file__)

load_dotenv()

DB_USERNAME = os.getenv('DB_USERNAME')
DB_PASSWORD = os.getenv('DB_PASSWORD')
DB_HOST = os.getenv('DB_HOST')
DB_NAME = os.getenv('DB_NAME')

print('DB_HOST: ', DB_HOST)

# connection string: mysql://user:pword@host/db
connection_string = f'mysql://{DB_USERNAME}:{DB_PASSWORD}@{DB_HOST}/{DB_NAME}'
app.config['SQLALCHEMY_DATABASE_URI'] = connection_string
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {'pool_recycle' : 280}


print("Initializing app...")
db.init_app(app)

# Wrap db.create_all() in an app context
print("Connecting to DB...")

with app.app_context():
    max_retries = 3
    retry_delay = 5
    for attempt in range(1, max_retries + 1):
        try:
            db.create_all()
            break
        except Exception as e:
            print(f"Error during database initialization (attempt {attempt}/{max_retries}): {e}")
            if attempt < max_retries:
                print(f"Retrying in {retry_delay} seconds...")
                time.sleep(retry_delay)
            else:
                # If max retries reached, raise the exception
                raise e

CORS(app)