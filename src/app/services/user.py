import logging
from typing import Optional
from sqlalchemy import select

from src.app.models import User
from src.infrastructure.databaseengine import DatabaseEngine

logger = logging.getLogger(__name__)


class UserService:
    def __init__(self, engine: DatabaseEngine):
        self._engine = engine

    def add_user(self, user: User) -> None:
        try:
            with self._engine.session() as session:
                session.add(user)
                session.commit()
        except Exception as e:
            if hasattr(locals().get('session'), 'rollback'):
                session.rollback()
            logger.error(f"Failed to create Admin {repr(user)}. Error: {e}")
            raise

    def get_user_by_id(self, user_id: int) -> User:
        with self._engine.session() as session:
            stmt = select(User).where(User.user_id == user_id)
            user: Optional[User] = session.scalars(stmt).one_or_none()

            if user is None:
                raise ValueError(f"Admin with id {user_id} not found")

        return user
