from sqlalchemy import MetaData
from sqlalchemy  import Table, Column, INTEGER, VARCHAR, TIMESTAMP, DATE, TIME, SMALLINT, TEXT, Enum, text, ForeignKey

metadata = MetaData()

user = Table(
    'user',
    metadata,
    Column('user_id', INTEGER, primary_key=True, autoincrement=True),
    Column('tg_user_id', INTEGER, unique=True),
    Column('first_name', VARCHAR(255)),
    Column('last_name', VARCHAR(255)),
    Column('created_at', TIMESTAMP, nullable=False, default=text('NOW()')),
    Column('updated_at', TIMESTAMP, onupdate=text('NOW()'))
    )

client = Table(
    'client',
    metadata,
    Column('client_id', INTEGER, primary_key=True, autoincrement=True),
    Column('tg_user_id', INTEGER, unique=True),
    Column('first_name', VARCHAR(255)),
    Column('last_name', VARCHAR(255)),
    Column('created_at', TIMESTAMP, nullable=False, default=text('NOW()')),
    Column('updated_at', TIMESTAMP, onupdate=text('NOW()'))
)

schedule= Table(
    'schedule',
    metadata,
    Column('schedule_id', INTEGER, primary_key=True, autoincrement=True),
    Column('admin_id', INTEGER, ForeignKey('user.user_id', ondelete='CASCADE'), nullable=False),
    Column('date', DATE, nullable=False),
    Column('start_time', TIME, nullable=False),
    Column('end_time', TIME, nullable=False),
    Column('is_active', SMALLINT, nullable=False),
    Column('created_at', TIMESTAMP, nullable=False, default=text('NOW()')),
    Column('updated_at', TIMESTAMP, onupdate=text('NOW()'))
)

slot = Table(
    'slot',
    metadata,
    Column('slot_id', INTEGER, primary_key=True, autoincrement=True),
    Column('start_time', TIMESTAMP, nullable=False),
    Column('end_time', TIMESTAMP, nullable=False),
    Column('duration_in_minutes', INTEGER, nullable=False),
    Column('created_at', TIMESTAMP, nullable=False, default=text('NOW()')),
    Column('updated_at', TIMESTAMP, onupdate=text('NOW()'))
)

appointment = Table(
    'appointment',
    metadata,
    Column('appointment_id', INTEGER, primary_key=True, autoincrement=True),
    Column('user_id', INTEGER, ForeignKey('user.user_id', ondelete='SET NULL')),
    Column('client_id', INTEGER, ForeignKey('client.client_id', ondelete='SET NULL')),
    Column('slot_id', INTEGER, ForeignKey('slot.slot_id', ondelete='SET NULL')),
    Column('description', TEXT),
    Column('location', VARCHAR(512)),
    Column('status', Enum, nullable=False),
    Column('created_at', TIMESTAMP, nullable=False, default=text('NOW()')),
    Column('updated_at', TIMESTAMP, onupdate=text('NOW()'))
)

__all__ = [
    'user',
    'client',
    'schedule',
    'slot',
    'appointment',
]
