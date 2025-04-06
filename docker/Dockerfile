## docker build -t dyrtransportes-flask:1.10.0 -f docker/Dockerfile .

# or ${REGISTRY}/dyrtransportes/dyrtransportes-flask:1.10.0

FROM python:3.13.2-slim-bookworm

EXPOSE 8080

WORKDIR /app

RUN adduser --disabled-password --gecos '' uwsgiuser && chown -R uwsgiuser:uwsgiuser /app

COPY requirements-common.txt .
COPY requirements-prod.txt .

RUN apt-get -y update && apt-get -y upgrade && \
    apt-get -y install pkg-config && \
    apt-get -y install gcc python3-dev && \
    apt-get -y install default-libmysqlclient-dev && \
    rm -rf /var/lib/apt/lists/* && \
    pip install -r requirements-common.txt --no-cache-dir && \
    pip install -r requirements-prod.txt --no-cache-dir

COPY wsgi.py .
COPY src src/

USER uwsgiuser

CMD ["uwsgi", "--http", "0.0.0.0:8080", "--wsgi-file", "wsgi.py"]