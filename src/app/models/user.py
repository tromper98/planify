from typing import Optional
from dataclasses import dataclass
from datetime import datetime

from sqlalchemy.orm import Mapped

from src.common.framework.schema.schema import user

from .base import Base

@dataclass
class User(Base):
    user_id: Mapped[int]
    tg_user_id: Mapped[str]
    first_name: Mapped[str]
    last_name: Mapped[str]
    created_at: Mapped[Optional[datetime]]
    updated_at: Mapped[Optional[datetime]]
    __table__ = user

    def __repr__(self):
        return f'User(user_id={self.user_id}, first_name={self.first_name}, last_name={self.last_name})'

    def __eq__(self, other):
        if self.user_id != other.user_id:
            return False
        if self.tg_user_id != other.tg_client_id:
            return False
        if self.first_name != other.first_name:
            return False
        if self.last_name != other.last_name:
            return False
        return True