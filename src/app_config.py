from flask import Flask
from flask_cors import CORS
from flask_caching import Cache

from logging import Logger, FileHandler, Formatter, StreamHandler
from flask.logging import create_logger

from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy import create_engine

from os import getenv
from subprocess import run, CalledProcessError
from dotenv import load_dotenv
from pathlib import Path

from models import Base


project_root_path = Path(__file__).parents[1].absolute()
load_dotenv(f'{project_root_path}/.env.development')

DB_USERNAME = getenv('DB_USERNAME')
DB_PASSWORD = getenv('DB_PASSWORD')
DB_HOST = getenv('DB_HOST')
DB_PORT = getenv('DB_PORT')
DB_NAME = getenv('DB_NAME')
DEBUG = bool(int(getenv('DEBUG') or 0))


def create_flask_app():
    """Initializes flask app"""
    flask_app: Flask = Flask(__name__)

    cache = Cache(flask_app, config={'CACHE_TYPE': 'simple'})
    CORS(flask_app)

    return flask_app


def create_flask_logger(flask_app: Flask):
    """Initializes logger"""
    file_handler = FileHandler('log.log')
    formatter = Formatter(
        "[%(asctime)s] - %(name)s - %(levelname)s - %(message)s")
    file_handler.setFormatter(formatter)

    console_handler = StreamHandler()
    console_handler.setFormatter(formatter)

    flask_logger = create_logger(flask_app)

    flask_logger.handlers.clear()
    flask_logger.addHandler(file_handler)
    flask_logger.addHandler(console_handler)

    return flask_logger


def init_database_and_migrate(flask_app: Flask, flask_logger: Logger):
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


app = create_flask_app()
logger = create_flask_logger(app)
db_session = init_database_and_migrate(app, logger)
