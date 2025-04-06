D y R Transportes Web - Backendend with Flask and MySQL (ORM sqlalchemy).

Works as an API that allows requests to the database


Configuration:
```.env
# dev
DB_USERNAME=root
DB_PASSWORD=root
DB_HOST=127.0.0.1
DB_PORT=3306
DB_NAME=dyrtransportes
DEBUG=1

API_KEY=123456
```

Create a database. Ex:
``` bash
docker run -d --restart=always -v /home/rolando/Desktop/dyrtransportes-mysql:/var/lib/mysql -e MYSQL_ROOT_PASSWORD=root -e MYSQL_PASSWORD=root -e MYSQL_DATABASE=dyrtransportes --name=dyrtransportes-mysql-dev -p 3306:3306 mysql:8
```

Run app (use script/run_dev.sh):
```bash
mypy src/

alembic -c src/migrations/alembic.ini upgrade head

flask --app src/app.py run --host 0.0.0.0 --port 8080 --debug
```

