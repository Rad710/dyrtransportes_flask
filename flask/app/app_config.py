"""
    Define app loger, cache, CORS and DEBUG mode
"""

import os

import flask.logging
from flask_cors import CORS
from flask_caching import Cache

from app.app import app


DEBUG = os.getenv('DEBUG')

logger = flask.logging.create_logger(app)

cache = Cache(app, config={'CACHE_TYPE': 'simple'})

CORS(app)


if DEBUG:
    app.debug = True
    print(f'\n\nDEBUG={DEBUG}')
    print('In debug mode...\n')

