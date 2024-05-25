import os
from dotenv import load_dotenv

from flask import Flask
import logging
from flask_cors import CORS
from flask_caching import Cache
import flask.logging
from pathlib import Path

app : Flask = Flask(__name__)

project_root_path = Path(__file__).parent.absolute()
load_dotenv(f'{project_root_path}/.env')

DB_USERNAME = os.getenv('DB_USERNAME')
DB_PASSWORD = os.getenv('DB_PASSWORD')
DB_HOST = os.getenv('DB_HOST')
DB_PORT = os.getenv('DB_PORT')
DB_NAME = os.getenv('DB_NAME')

DEBUG = bool(int(os.getenv('DEBUG') or 0))

connection_string = f'mysql://{DB_USERNAME}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}'
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

from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

engine = create_engine(app.config['SQLALCHEMY_DATABASE_URI'])

db_session = scoped_session(sessionmaker(autocommit=False,
                                         autoflush=False,
                                         bind=engine))


print("Init database...")
from models import Base
Base.metadata.create_all(bind=engine)
# migrate = Migrate(app, db)

# Wrap db.create_all() in an app context
print("\nConnecting to DB...")

@app.teardown_appcontext
def shutdown_session(exception=None):
    db_session.remove()
