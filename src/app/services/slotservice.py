import logging
from typing import Optional
from datetime import date, datetime
from sqlalchemy import select, text

from src.app.entities import Slot, AppointmentStatusEnum
from src.infrastructure.databaseengine import DatabaseEngine

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

    def get_slot_by_id(self, slot_id: int) -> Slot:
        with self._engine.session() as session:
            stmt = select(Slot).where(Slot.slot_id == slot_id)
            slot: Optional[Slot] = session.scalars(stmt).one_or_none()

            if slot is None:
                raise ValueError(f'Slot with id {slot_id} not found')

        return slot

    def get_slots_by_date(self, dt: date) -> Optional[list[Slot]]:
        start_of_day = datetime.combine(dt, datetime.min.time())
        end_of_day = datetime.combine(dt, datetime.max.time())
        with self._engine.session() as session:
            stmt = select(Slot).where(
                Slot.start_time.between(start_of_day, end_of_day)) \
                .order_by(Slot.start_time)
            return list(session.scalars(stmt).all())
