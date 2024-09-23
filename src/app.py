import logging

from app_config import app
from app_config import logger
from app_config import db_session
from app_config import DEBUG

import api


@app.teardown_appcontext
def shutdown_session(exception=None):
    """Closes database session"""
    db_session.remove()


if DEBUG:
    logger.setLevel(logging.DEBUG)

if __name__ == '__main__':
    # flask --app app/app.py run --host 0.0.0.0 --port 8081 --debug
    app.run(host='0.0.0.0', debug=False, port=8080)
