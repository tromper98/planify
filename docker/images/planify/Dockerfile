FROM python:3.13.7-alpine3.21

WORKDIR /app

COPY pyproject.toml poetry.lock README.md alembic.ini  ./

RUN pip install --no-cache-dir poetry && \
    poetry install --no-root

COPY src ./src

RUN poetry install
