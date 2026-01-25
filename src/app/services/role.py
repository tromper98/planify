import logging
from sqlalchemy import select

from src.app.models import Role, User, Client
from src.infrastructure.postgres.databaseengine import DatabaseEngine

logger = logging.getLogger(__name__)


class RoleService:
    def __init__(self, engine: DatabaseEngine):
        self._engine = engine

    def get_user_role_by_tg_id(self, tg_id: int) -> Role:
        with self._engine.session() as session:
            stmt = select(User).where(User.tg_user_id == tg_id)
            user = session.scalars(stmt).one_or_none()

            if user:
                return Role.ADMIN

            stmt = select(Client).where(Client.tg_client_id == tg_id)
            client = session.scalars(stmt).one_or_none()

            if client:
                return Role.CLIENT

            return Role.GUEST
