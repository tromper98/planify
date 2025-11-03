import pytest

import os
from sqlalchemy import Engine, create_engine, text

def test_db_connection():
    dsn = os.getenv('PLANIFY_DB_DSN')
    engine: Engine = create_engine(dsn)

    with engine.connect() as conn:
        result = conn.execute(text('SELECT 1 as test_value'))
        row = result.fetchone()

        assert row is not None
        assert row.test_value == 1