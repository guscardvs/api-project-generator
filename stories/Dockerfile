FROM python:3.9-slim

COPY . /var/www/app

WORKDIR /var/www/app

RUN python3.9 -m pip install -U pip poetry

RUN poetry install --no-dev

EXPOSE 8000

ENTRYPOINT poetry run circusd ./circus.ini --log-level info

