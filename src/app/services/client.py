import logging
from typing import Optional
from sqlalchemy import select

from src.app.models import User, Appointment
from src.infrastructure.databaseengine import DatabaseEngine

logger = logging.getLogger(__name__)


class ClientService:
    def __init__(self, engine: DatabaseEngine):
        self._engine = engine

    def add_client(self, client: User):
        if client.is_admin():
            raise RuntimeError(f"Can't create Client with non client role")
        try:
            with self._engine.session() as session:
                session.add(client)
                session.commit()
        except Exception as e:
            if hasattr(locals().get('session'), 'rollback'):
                session.rollback()
            logger.error(f"Failed to add Client {repr(client)}. Error: {e}")
            raise

    def get_client_by_id(self, client_id: int) -> Optional[User]:
        with self._engine.session() as session:
            stmt = select(User).where(User.user_id == client_id, User.is_admin == 0)
            client: Optional[User] = session.scalars(stmt).one_or_none()

            if client is None:
                raise ValueError(f"Client with id {client_id} not found")
        return client

    def get_client_appointments(self, client_id: int) -> Optional[list[Appointment]]:
        with self._engine.session() as session:
            stmt = select(Appointment).where(
                Appointment.client_id == client_id
            ).order_by(Appointment.created_at)
            return list(session.scalars(stmt).all())
