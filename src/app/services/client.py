import logging
from typing import Optional
from sqlalchemy import select

from src.app.models import Client, Appointment
from src.infrastructure.postgres.databaseengine import DatabaseEngine

logger = logging.getLogger(__name__)


class ClientService:
    def __init__(self, engine: DatabaseEngine):
        self._engine = engine

    def add_client(self, client: Client):
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

    def get_client_by_id(self, client_id: int) -> Optional[Client]:
        with self._engine.session() as session:
            stmt = select(Client).where(Client.client_id == client_id)
            client: Optional[Client] = session.scalars(stmt).one_or_none()

            if client is None:
                raise ValueError(f"Client with id {client_id} not found")
        return client

    def get_client_by_tg_id_if_exists(self, tg_client_id: int) -> Optional[Client]:
        with self._engine.session() as session:
            stmt = select(Client).where(Client.tg_client_id == tg_client_id)
            return session.scalars(stmt).one_or_none()

    def get_client_appointments(self, client_id: int) -> Optional[list[Appointment]]:
        with self._engine.session() as session:
            stmt = select(Appointment).where(
                Appointment.client_id == client_id
            ).order_by(Appointment.created_at)
            return list(session.scalars(stmt).all())
