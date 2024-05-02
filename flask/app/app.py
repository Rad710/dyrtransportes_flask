import os
from dotenv import load_dotenv

from flask import Flask
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
from models.schema import db

db.init_app(app)
migrate = Migrate(app, db)

# Wrap db.create_all() in an app context
print("\nConnecting to DB...")

from flask_migrate import upgrade
with app.app_context():
    db.create_all()

    print('\nMigrating db...')
    upgrade()


# Define endpoints
from app.routes import app

print('\nFlask API starting...\n\n')

if __name__ == '__main__':
    # flask --app app/app.py run --host 0.0.0.0 --port 8081 --debug
    app.run(host='0.0.0.0', port=8085)
