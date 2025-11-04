import logging
from contextlib import contextmanager
from typing import Optional, Iterator
from sqlalchemy import Engine, create_engine, text
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import sessionmaker, Session

from .envconfig import EnvConfig

DEFAULT_CONN_OPTIONS = {
    'pool_size': 5,
    'max_overflow': 10,
    'pool_timeout': 30,
    'pool_recycle': 3600,
    'echo': False
}

logger = logging.getLogger(__name__)

class DatabaseEngine:

    def __init__(self,):
        conn_str: str = EnvConfig.get_str('PLANIFY_DB_DSN')
        self._engine: Optional[Engine] = None
        self._session_factory: Optional[sessionmaker] = None

        self._init_engine(conn_str)


    def _init_engine(self, conn_str: str) -> None:
        try:
            self._engine = create_engine(conn_str, **DEFAULT_CONN_OPTIONS)

            self._test_connection()

            self._session_factory = sessionmaker(
                bind=self._engine,
                autocommit=False,
                autoflush=False,
                expire_on_commit=False
            )
            logger.debug('Database engine initialize successfully')
        except Exception as e:
            logger.error(f'Failed to initialize database engine: {e}')
            raise

    def _test_connection(self) -> None:
        if not self._engine:
            raise RuntimeError('Engine not initialized')

        try:
            with self._engine.connect() as conn:
                conn.execute(text('SELECT 1'))
            logger.debug('Database connection passed')
        except OperationalError as e:
            logger.error(f'Database connection failed: {e}')
            raise

    @property
    def engine(self) -> Engine:
        if not self._engine:
            raise RuntimeError('Database engine not initialized')
        return self._engine

    @contextmanager
    def session(self) -> Iterator[Session]:
        """
         Context manager для работы с сессией базы данных.

         Usage:
             with db_engine.session() as session:
                 user = session.query(User).first()
         """
        if not self._session_factory:
            raise RuntimeError("Session factory not initialized")

        session = self._session_factory()
        try:
            yield session
            session.commit()
            logger.debug("Session committed successfully")
        except Exception as e:
            session.rollback()
            logger.error(f"Session rollback due to error: {e}")
            raise
        finally:
            session.close()

    def dispose(self) -> None:
        """Закрыть все соединения и очистить ресурсы."""
        if self._engine:
            self._engine.dispose()

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.dispose()