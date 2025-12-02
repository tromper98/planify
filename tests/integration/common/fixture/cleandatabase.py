import pytest
from sqlalchemy import text
from src.infrastructure.databaseengine import DatabaseEngine

@pytest.fixture
def clean_database():
    """Фикстура для ручной очистки базы данных."""
    engine = DatabaseEngine()

    def _cleaner():
        with engine.session() as session:
            # Получаем все пользовательские таблицы
            result = session.execute(text("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_type = 'BASE TABLE'
            """))

            tables = [row[0] for row in result]

            # Очищаем все таблицы
            for table in tables:
                if table not in ['spatial_ref_sys']:  # Исключаем системные
                    session.execute(text(f'TRUNCATE TABLE "{table}" CASCADE;'))

            session.commit()

    # Очищаем перед тестом
    _cleaner()
    yield
    # Очищаем после теста
    _cleaner()
