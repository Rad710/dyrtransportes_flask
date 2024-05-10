import os
import subprocess
from dotenv import load_dotenv

from flask import Flask, send_file
from flask_migrate import Migrate

app = Flask(__name__)

load_dotenv()

DB_USERNAME = os.getenv('DB_USERNAME')
DB_PASSWORD = os.getenv('DB_PASSWORD')
DB_HOST = os.getenv('DB_HOST')
DB_NAME = os.getenv('DB_NAME')


connection_string = f'mysql://{DB_USERNAME}:{DB_PASSWORD}@{DB_HOST}/{DB_NAME}'
app.config['SQLALCHEMY_DATABASE_URI'] = connection_string
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {'pool_recycle' : 280}


print("\nInitializing app...")
from models.database import db_session
from models.database import engine


print("Init database...")
import models.schema

models.schema.Base.metadata.create_all(bind=engine)
# migrate = Migrate(app, db)

# Wrap db.create_all() in an app context
print("\nConnecting to DB...")

# Define endpoints
from api.cobranzas import app, logger
from api.dinatran import app
from api.exportar import app
from api.importar import app
from api.keywords import app
from api.liquidacion_gastos import app
from api.liquidacion_viajes import app
from api.liquidacion import app
from api.planillas import app
from api.route import app
from api.statistics import app


@app.route('/')
def index():
    return "Hello, World!"


# Route to return a copy of the database file
@app.route('/database_backup', methods=['GET'])
def database_backup():
    try:
        dump_file = 'dump_filename.sql'

        # Use mysqldump to create a SQL dump of your MySQL database
        subprocess.run(["mysqldump", "-u", DB_USERNAME, "-h", DB_HOST, "--set-gtid-purged=OFF", "--no-tablespaces", DB_NAME, "--result-file=" + dump_file])
        # Open the dump file for reading and send it as an attachment
        return send_file(f'../{dump_file}', as_attachment=True)

    except Exception as e:
        error_message = f'Error al crear backup {str(e)}'
        logger.warning(error_message)
        return error_message, 500
    

@app.teardown_appcontext
def shutdown_session(exception=None):
    db_session.remove()

print('\nFlask API starting...\n\n')

if __name__ == '__main__':
    # flask --app app/app.py run --host 0.0.0.0 --port 8081 --debug
    app.run(host='0.0.0.0', port=8085)
