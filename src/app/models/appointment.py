from enum import Enum
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from sqlalchemy.orm import Mapped

from src.common.framework.schema.schema import appointment

from .base import Base

class AppointmentStatus(Enum):
    PENDING = 'pending' # Ожидает подтверждения
    CONFIRMED = 'confirmed' # Подтверждена
    COMPLETED = 'completed' # Завершена
    CANCELLED = 'cancelled' # Отменена
    RESCHEDULED = 'rescheduled' # Перенесена

@dataclass
class Appointment(Base):
    appointment_id: Mapped[int]
    client_id: Mapped[int]
    user_id: Mapped[int]
    slot_id: Mapped[int]
    description: Mapped[str]
    location: Mapped[str]
    status: Mapped[AppointmentStatus]
    created_at: Mapped[Optional[datetime]]
    updated_at: Mapped[Optional[datetime]]
    __table__ = appointment

    def __repr__(self):
        return (f"Appointment(appointment={self.appointment_id}, title={self.title}, scheduled_time={self.scheduled_time},"
                f"duration={self.duration}, status={self.status})")

    def __eq__(self, other):
        if self.appointment_id != other.appointment_id:
            return False
        if self.client_id != other.client_id:
            return False
        if self.user_id != other.user_id:
            return False
        if self.slot_id != other.slot_id:
            return False
        if self.description != other.description:
            return False
        if self.status != other.status:
            return False

        return True