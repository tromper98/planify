import logging
from typing import Optional
from sqlalchemy import select

from src.app.models import Appointment, AppointmentStatus, Slot
from src.infrastructure.postgres.databaseengine import DatabaseEngine

logger = logging.getLogger(__name__)


class AppointmentService:
    def __init__(self, engine: DatabaseEngine):
        self._engine = engine

    def create_appointment(self, appointment: Appointment) -> None:
        try:
            with self._engine.session() as session:
                session.add(appointment)
                session.commit()

        except Exception as e:
            if hasattr(locals().get('session'), 'rollback'):
                session.rollback()
            logger.error(f"Failed to create Appointment {repr(appointment)}. Error: {e}")
            raise

    def get_appointment_by_id(self, appointment_id: int) -> Optional[Appointment]:
        with self._engine.session() as session:
            stmt = select(Appointment).where(Appointment.appointment_id == appointment_id)
            return session.scalars(stmt).one_or_none()

    def update_appointment(self, appointment: Appointment) -> None:
        with self._engine.session() as session:
            session.merge(appointment)
            session.commit()

    def reschedule_appointment(self, appointment_id: int, new_slot: Slot) -> None:
        if not new_slot.is_free:
            raise ValueError(f"Slot is busy")

        appointment: Optional[Appointment] = self.get_appointment_by_id(appointment_id)

        if not appointment:
            raise ValueError(f"Appointment with appointment_id = {appointment_id} does not exists")
        with self._engine.session() as session:
            appointment.slot_id = new_slot.slot_id
            session.commit()


    def cancel_appointment(self, appointment_id: int) -> None:
        self._update_appointment_status(appointment_id, AppointmentStatus.CANCELLED)

    def confirm_appointment(self, appointment_id: int) -> None:
        self._update_appointment_status(appointment_id, AppointmentStatus.CONFIRMED)

    def complete_appointment(self, appointment_id: int) -> None:
        self._update_appointment_status(appointment_id, AppointmentStatus.COMPLETED)

    def _update_appointment_status(self, appointment_id: int, new_status: AppointmentStatus) -> None:
        with self._engine.session() as session:
            stmt = select(Appointment).where(Appointment.appointment_id == appointment_id)
            appointment: Optional[Appointment] = session.scalars(stmt).one_or_none()

            if appointment is None:
                raise RuntimeError(f'Appointment with appointment_id = {appointment_id} does not found')

            appointment.status = new_status
            session.commit()
