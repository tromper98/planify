import logging
from typing import Optional
from datetime import date, datetime

from sqlalchemy import select, delete, or_

from src.app.models import Slot, Appointment
from src.infrastructure.postgres.databaseengine import DatabaseEngine

logger = logging.getLogger(__name__)

class SlotService:
    def __init__(self, engine: DatabaseEngine):
        self._engine = engine

    def add_slot(self, slot: Slot) -> None:
        try:
            with self._engine.session() as session:
                session.add(slot)
                session.commit()

        except Exception as e:
            if hasattr(locals().get('session'), 'rollback'):
                session.rollback()
            logger.error(f"Failed to create Slot {repr(slot)}. Error: {e}")
            raise

    def get_slot_by_id(self, slot_id: int) -> Optional[Slot]:
        with self._engine.session() as session:
            stmt = select(Slot).where(Slot.slot_id == slot_id)
            slot: Optional[Slot] = session.scalars(stmt).one_or_none()

        return slot

    def get_slots(self) -> list[Slot]:
        with self._engine.session() as session:
            stmt = select(Slot).order_by(Slot.start_time)
            slots: list[Slot] = session.scalars(stmt).all()

        return slots

    def get_slots_by_date(self, dt: date) -> Optional[list[Slot]]:
        start_of_day = datetime.combine(dt, datetime.min.time())
        end_of_day = datetime.combine(dt, datetime.max.time())
        with self._engine.session() as session:
            stmt = select(Slot).where(
                Slot.start_time.between(start_of_day, end_of_day)) \
                .order_by(Slot.start_time)
            return list(session.scalars(stmt).all())

    def delete_slot_by_id(self, slot_id: int) -> None:
        with self._engine.session() as session:
            stmt = delete(Slot).where(Slot.slot_id == slot_id)
            session.scalars(stmt).all()
            session.commit()

    def delete_slot_between_two_dates(self, start_date: datetime, end_date: datetime) -> None:
        with self._engine.session() as session:
            stmt = delete(Slot).where(Slot.start_time.between(start_date, end_date))
            session.scalars(stmt).all()

    def is_slot_free(self, slot_id: int) -> bool:
        with self._engine.session() as session:
            stmt = select(Appointment).where(Appointment.slot_id == slot_id)
            result = session.scalars(stmt).one_or_none()

            return False if result is None else True

    def is_slot_intersect_with_others(self, slot: Slot) -> bool:
        with self._engine.session() as session:
            stmt = select(Slot).where(
                or_(
                    (slot.start_time.between(Slot.start_time, Slot.end_time)),
                    (slot.end_time.between(Slot.start_time, Slot.end_time))
                )
            )
            result = session.scalars(stmt).one_or_none()
            return False if result is None else True
