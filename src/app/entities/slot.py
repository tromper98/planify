from sqlalchemy.orm import registry

from src.common.framework.schema.schema import slot, metadata

mapper_registry = registry(metadata=metadata)
Base = mapper_registry.generate_base()


class Slot(Base):
    __table__ = slot

    def __repr__(self):
        return (f'<User(slot_id={self.slot_id}, start_time={self.start_time}, end_time={self.end_time},'
                f' duration_in_minutes={self.duration_in_minutes}>')

    def __eq__(self, other):
        if self.slot_id != other.slot_id:
            return False
        if self.start_time != other.start_time:
            return False
        if self.end_time != other.end_time:
            return False
        if self.duration_in_minutes != other.duration_in_minutes:
            return False
        return True
