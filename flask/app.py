from app_config import app

import endpoints

if __name__ == '__main__':
    # flask --app app/app.py run --host 0.0.0.0 --port 8081 --debug
    app.run(host='0.0.0.0', port=8080)
