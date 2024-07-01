from app_config import app
from app_config import logger
from app_config import DEBUG

import logging

import api

if DEBUG:
    logger.setLevel(logging.DEBUG)

if __name__ == '__main__':
    # flask --app app/app.py run --host 0.0.0.0 --port 8081 --debug
    app.run(host='0.0.0.0', debug=False, port=8080)
