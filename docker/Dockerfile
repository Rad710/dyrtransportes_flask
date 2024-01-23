FROM python:3.10.13

EXPOSE 8081

# RUN apt-get -y update && apt-get -y upgrade
# RUN apt-get -y install pkg-config \
#     && apt-get -y install gcc python3-dev

# RUN apt-get install libmysqlclient-dev

WORKDIR /app

COPY requirements.txt .
COPY docker/wait-for-it.sh wait-for-it.sh
COPY docker/entrypoint.sh entrypoint.sh

RUN pip install -r requirements.txt

COPY . .

RUN pip install -r requirements.txt --upgrade

ENV FLASK_APP=flask_app.py

CMD ["./wait-for-it.sh", "-t", "0", "dyrtransportes-mysql-dev:3306", "--", "./entrypoint.sh"]