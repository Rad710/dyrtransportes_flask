import api.statistics
import api.route
import api.planillas
import api.liquidacion
import api.liquidacion_viajes
import api.liquidacion_gastos
import api.driver
import api.importar
import api.exportar
import api.dinatran
import api.cobranzas
import api.product
from flask import send_file
import subprocess

from app_config import DB_USERNAME, DB_HOST, DB_NAME, db_session, app


@app.route('/')
def index():
    return "Hello, World!"


# Route to return a copy of the database file
@app.route('/database_backup', methods=['GET'])
def database_backup():
    try:
        dump_file = 'dump_filename.sql'

        # Use mysqldump to create a SQL dump of your MySQL database
        subprocess.run(["mysqldump", "-u", DB_USERNAME, "-h", DB_HOST, "--set-gtid-purged=OFF",
                       "--no-tablespaces", DB_NAME, "--result-file=" + dump_file])
        # Open the dump file for reading and send it as an attachment
        return send_file(f'../{dump_file}', as_attachment=True)

    except Exception as e:
        error_message = f'Error al crear backup {str(e)}'
        # logger.warning(error_message)
        return error_message, 500


@app.teardown_appcontext
def shutdown_session(exception=None):
    db_session.remove()


# Define endpoints
