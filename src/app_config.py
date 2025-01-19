from flask import Flask, request, has_request_context
from flask_cors import CORS
from flask_caching import Cache

import logging
from flask.logging import create_logger

from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy import create_engine

from os import getenv
from subprocess import run, CalledProcessError
from dotenv import load_dotenv
from pathlib import Path

import time

from models import Base


project_root_path = Path(__file__).parents[1].absolute()
load_dotenv(f'{project_root_path}/.env.development')

DB_USERNAME = getenv('DB_USERNAME')
DB_PASSWORD = getenv('DB_PASSWORD')
DB_HOST = getenv('DB_HOST')
DB_PORT = getenv('DB_PORT')
DB_NAME = getenv('DB_NAME')
DEBUG = bool(int(getenv('DEBUG') or 0))


# Custom logging filter to include method and request path
class RequestFilter(logging.Filter):
    def filter(self, record):
        if has_request_context():
            client_ip = request.remote_addr or 'unknown'
            record.request_info = f'[{request.method} {request.path} from {client_ip}]'
        else:
            record.request_info = ''
        return True


def create_flask_app():
    """Initializes flask app"""
    flask_app: Flask = Flask(__name__)

    cache = Cache(flask_app, config={'CACHE_TYPE': 'simple'})
    CORS(flask_app)

    return flask_app


def create_flask_logger(flask_app: Flask):
    """Initializes logger"""
    formatter = logging.Formatter(
        "[%(asctime)s] - %(levelname)s - %(request_info)s - %(message)s"
    )

    file_handler = logging.FileHandler('log.log')
    file_handler.setFormatter(formatter)
    file_handler.addFilter(RequestFilter())

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    console_handler.addFilter(RequestFilter())

    flask_logger = logging.getLogger('werkzeug')
    flask_logger.handlers.clear()
    flask_logger.addHandler(file_handler)
    flask_logger.addHandler(console_handler)

    if DEBUG:
        flask_logger.setLevel(logging.DEBUG)

    @flask_app.before_request
    def start_timer():
        request.start_time = time.time()

    @flask_app.after_request
    def log_request(response):
        if hasattr(request, 'start_time'):
            duration = time.time() - request.start_time
            flask_logger.info(
                "Request took %s seconds", duration
            )
        return response

    return flask_logger


def init_database_and_migrate(flask_app: Flask, flask_logger: logging.Logger):
    """Initializes Database and db_session"""

    if (None in [DB_USERNAME, DB_PASSWORD, DB_HOST, DB_PORT, DB_NAME]):
        flask_logger.error(".env.development file is missing")

    connection_string = f'mysql+mysqldb://{DB_USERNAME}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}'
    flask_logger.info("Using connection_string: %s", connection_string)

    flask_app.config['SQLALCHEMY_DATABASE_URI'] = connection_string
    flask_app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {'pool_recycle': 280}

    engine = create_engine(flask_app.config['SQLALCHEMY_DATABASE_URI'])

    flask_logger.info("Init database...")
    Base.metadata.create_all(bind=engine)

    flask_logger.info("Running migration scripts...")
    alembic_command = ["alembic", "-c",
                       "src/migrations/alembic.ini", "upgrade", "head"]
    try:
        run(alembic_command, check=True)
        flask_logger.info("Alembic migration applied successfully!")
    except CalledProcessError as e:
        flask_logger.info("Error while applying Alembic migration: %s", e)

    flask_db_session = scoped_session(sessionmaker(
        autocommit=False, autoflush=False, bind=engine
    ))

    return flask_db_session


def set_up_shutdown_session(flask_app: Flask):
    @flask_app.teardown_appcontext
    def shutdown_session(exception=None):
        """Closes database session"""
        db_session.remove()


app = create_flask_app()
logger = create_flask_logger(app)

db_session = init_database_and_migrate(app, logger)
set_up_shutdown_session(app)
