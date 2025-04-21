import os
import logging
import time

from pathlib import Path
from subprocess import run
from subprocess import CalledProcessError

from dotenv import load_dotenv

from flask import Flask
from flask import request
from flask import Request
from flask import has_request_context

from flask_cors import CORS

from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session
from sqlalchemy.orm import sessionmaker

from models import *

project_root_path = Path(__file__).parents[1].absolute()
load_dotenv(f"{project_root_path}/.env")

DB_USERNAME = os.getenv("DB_USERNAME")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")
DB_NAME = os.getenv("DB_NAME")
API_KEY = os.getenv("API_KEY")
DEBUG = os.getenv("DEBUG")


# Custom logging filter to include method and request path
class RequestFilter(logging.Filter):
    def filter(self, record):
        if has_request_context():
            client_ip = request.remote_addr or "unknown"
            record.request_info = f"[{request.method} {request.path} from {client_ip}]"
        else:
            record.request_info = ""
        return True


class RequestWithUser(Request):
    current_user: User
    start_time: float


request: RequestWithUser


def create_flask_app():
    """Initializes flask app"""
    flask_app: Flask = Flask(__name__)
    flask_app.config["SECRET_KEY"] = API_KEY

    if DEBUG:
        CORS(flask_app, expose_headers=["Content-Disposition"])

    return flask_app


def create_flask_logger(flask_app: Flask):
    """Initializes logger with separate files for info and error logs"""
    formatter = logging.Formatter(
        "[%(asctime)s] - %(levelname)s - %(request_info)s - %(message)s"
    )

    # Create info log handler
    info_file_handler = logging.FileHandler("info.log")
    info_file_handler.setFormatter(formatter)
    info_file_handler.addFilter(RequestFilter())
    info_file_handler.setLevel(logging.INFO)

    # Create error log handler
    error_file_handler = logging.FileHandler("error.log")
    error_file_handler.setFormatter(formatter)
    error_file_handler.addFilter(RequestFilter())
    error_file_handler.setLevel(logging.ERROR)

    # Console handler for all logs
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    console_handler.addFilter(RequestFilter())

    flask_logger = logging.getLogger("werkzeug")
    flask_logger.handlers.clear()
    flask_logger.addHandler(info_file_handler)
    flask_logger.addHandler(error_file_handler)
    flask_logger.addHandler(console_handler)

    if DEBUG:
        flask_logger.setLevel(logging.DEBUG)
        # For SQLAlchemy, we'll add both handlers to capture all levels
        sqlalchemy_logger = logging.getLogger("sqlalchemy.engine")
        sqlalchemy_logger.setLevel(logging.INFO)
        sqlalchemy_logger.addHandler(info_file_handler)
        sqlalchemy_logger.addHandler(error_file_handler)
        sqlalchemy_logger.addHandler(logging.StreamHandler())

    @flask_app.before_request
    def start_timer():
        request.start_time = time.time()

    @flask_app.after_request
    def log_request(response):
        if hasattr(request, "start_time"):
            duration = time.time() - request.start_time
            flask_logger.info("request took %s seconds", duration)
        return response

    return flask_logger


def init_database_and_migrate():
    """Initializes Database and db_session"""

    if None in [DB_USERNAME, DB_PASSWORD, DB_HOST, DB_PORT, DB_NAME]:
        print(".env file is missing")

    connection_string = (
        f"mysql+mysqldb://{DB_USERNAME}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    )
    if DEBUG:
        print("using connection_string: %s", connection_string)

    engine = create_engine(
        url=connection_string,
        pool_size=10,  # Maximum number of connections to keep
        pool_recycle=3600,  # Recycle connections after 1 hour (in seconds)
        pool_pre_ping=True,  # Verify connections before using them
        max_overflow=20,  # Allow up to 20 connections beyond pool_size when needed
    )

    print("init database...")
    Base.metadata.create_all(bind=engine)

    # Get the absolute path to the alembic.ini file
    # This gets the directory of the current script file (__file__), not the working directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    alembic_ini_path = os.path.join(script_dir, "migrations", "alembic.ini")

    print(f"Using alembic.ini at: {alembic_ini_path}")

    print("running migration scripts...")
    alembic_command = ["alembic", "-c", alembic_ini_path, "upgrade", "head"]
    try:
        run(alembic_command, check=True)
        print("Alembic migration applied successfully!")
    except CalledProcessError as e:
        print("Error while applying Alembic migration: %s", e)
        # Print more detailed error information
        print(f"Command attempted: {' '.join(alembic_command)}")
        print(f"Working directory: {os.getcwd()}")
    except Exception as e:
        print("Error while applying Alembic migration: %s", e)

    return scoped_session(sessionmaker(autocommit=False, autoflush=False, bind=engine))


app = create_flask_app()
logger = create_flask_logger(app)
db_session = init_database_and_migrate()
