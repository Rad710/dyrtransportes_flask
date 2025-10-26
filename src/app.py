import tempfile
import os
import subprocess
from datetime import datetime


from flask import send_from_directory
from flask import send_file
from flask import request

from app_config import app
from app_config import DEBUG
from app_config import DB_USERNAME
from app_config import DB_HOST
from app_config import DB_NAME
from app_config import DB_PASSWORD
from app_config import RequestWithUser

from decorators.token_required import token_required

from api import *


request: RequestWithUser


@app.route("/api/hello-world", methods=["GET"])
def hello_world():
    return "Hello, World!"


@app.route("/api/protected/hello-world", methods=["GET"])
@token_required
def protected_hello_world():
    return "Protected Hello, World!"


@app.route("/api/protected/database-backup", methods=["GET"])
@token_required
def database_backup():
    if request.current_user.user_id != "dyrtransportes":
        logger.error("Backup invalid user: %s")
        return jsonify({"message": "Error al crear backup: usuario no autorizado"}), 500

    try:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_filename = f"database_backup_{timestamp}.sql"

        # Create a temporary directory that will be automatically cleaned up
        temp_dir = tempfile.mkdtemp()
        dump_file = os.path.join(temp_dir, "temp_dump.sql")

        # Use mysqldump to create a SQL dump of your MySQL database
        result = None
        if DEBUG:
            result = subprocess.run(
                [
                    "mysqldump",
                    "-u",
                    DB_USERNAME,
                    f"-p{DB_PASSWORD}",
                    "-h",
                    DB_HOST,
                    "--set-gtid-purged=OFF",
                    "--no-tablespaces",
                    DB_NAME,
                    "--result-file=" + dump_file,
                ],
                capture_output=True,
                text=True,
                check=False,  # Explicitly set check to False since we handle errors manually
            )
        else:
            result = subprocess.run(
                [
                    "mysqldump",
                    "-u",
                    DB_USERNAME,
                    "-h",
                    DB_HOST,
                    "--set-gtid-purged=OFF",
                    "--no-tablespaces",
                    DB_NAME,
                    "--result-file=" + dump_file,
                ],
                capture_output=True,
                text=True,
                check=False,  # Explicitly set check to False since we handle errors manually
            )

        # Check if the process executed successfully
        if result is None or result.returncode != 0:
            logger.error("mysqldump failed: %s", result.stderr)
            return jsonify({"message": f"Error creating backup: {result.stderr}"}), 500

        # Check if file exists before sending
        if not os.path.exists(dump_file):
            logger.error("Dump file was not created")
            return jsonify({"message": "Backup file was not created"}), 500

        # Send the file with the timestamped filename
        return send_file(
            dump_file,
            as_attachment=True,
            download_name=backup_filename,
            mimetype="application/sql",
        )

    except Exception as e:
        logger.error("Backup error: %s", e)
        return jsonify({"message": "Error creating backup"}), 500


## TODO: remove these two endpoints when using nginx
# Serve static assets directly
@app.route("/assets/<path:path>")
def serve_assets(path: str):
    return send_from_directory("static/assets", path)


# Catch-all route to serve index.html for any non-API routes
@app.route("/", defaults={"path": ""})
@app.route("/<path:path>")
def serve_react(path: str):
    # If path starts with /api/, let Flask continue to the next route handler
    if path.startswith("api/"):
        return app.dispatch_request()

    # Otherwise serve the index.html file for client-side routing
    return send_from_directory("static", "index.html")


@app.teardown_appcontext
def shutdown_session(exception=None):
    """Closes database session"""
    db_session.remove()


## TODO: import endpoint

## TODO: create driver payroll when creating new driver

## TODO: create driver payroll when changing status to paid

## TODO: add blueprint for apis


if __name__ == "__main__":
    # flask --app app/app.py run --host 0.0.0.0 --port 8081 --debug
    app.run(host="0.0.0.0", debug=bool(DEBUG), port=8080)
