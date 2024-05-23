import os
from dotenv import load_dotenv

from flask import Flask
import logging
from flask_cors import CORS
from flask_caching import Cache
import flask.logging

# from flask_migrate import Migrate

app : Flask = Flask(__name__)

load_dotenv()

DB_USERNAME = os.getenv('DB_USERNAME')
DB_PASSWORD = os.getenv('DB_PASSWORD')
DB_HOST = os.getenv('DB_HOST')
DB_NAME = os.getenv('DB_NAME')


connection_string = f'mysql://{DB_USERNAME}:{DB_PASSWORD}@{DB_HOST}/{DB_NAME}'
app.config['SQLALCHEMY_DATABASE_URI'] = connection_string
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {'pool_recycle' : 280}


file_handler = logging.FileHandler('log.log')
formatter = logging.Formatter("[%(asctime)s] - %(name)s - %(levelname)s - %(message)s")
file_handler.setFormatter(formatter)

console_handler = logging.StreamHandler()
console_handler.setFormatter(formatter)

logger = flask.logging.create_logger(app)

logger.handlers.clear()
logger.addHandler(file_handler)
logger.addHandler(console_handler)

cache = Cache(app, config={'CACHE_TYPE': 'simple'})

CORS(app)

print("\nInitializing app...")
from models.database import db_session
from models.database import engine


print("Init database...")
import models.models

models.models.Base.metadata.create_all(bind=engine)
# migrate = Migrate(app, db)

# Wrap db.create_all() in an app context
print("\nConnecting to DB...")

@app.teardown_appcontext
def shutdown_session(exception=None):
    db_session.remove()
