import pytest

from sqlalchemy import text
from src.infrastructure.databaseengine import DatabaseEngine

from tests.integration.common.fixture import clean_database

def test_db_connection(clean_database):
    engine: DatabaseEngine = DatabaseEngine()

    with engine.session() as session:
        result = session.execute(text('SELECT 1 as test_value'))
        row = result.fetchone()

        assert row is not None
        assert row.test_value == 1
