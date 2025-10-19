FROM python:3.14.0-alpine3.21

WORKDIR /app

COPY pyproject.toml poetry.lock README.md  ./

RUN pip install --no-cache-dir poetry

RUN poetry install --no-root

COPY src ./src

RUN poetry install
