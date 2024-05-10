"""
    Define app logger, handlers, cache, CORS
"""

import logging

import flask.logging
from flask_cors import CORS
from flask_caching import Cache

from app.app import app



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

