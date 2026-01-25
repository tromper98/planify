"""Add initial tables

Revision ID: 8e5820ff6e26
Revises: 
Create Date: 2025-10-26 11:20:45.744956

"""
import enum
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import ForeignKey

# revision identifiers, used by Alembic.
revision: str = '8e5820ff6e26'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

class AppointmentStatusEnum(enum.Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    NO_SHOW = "no_show"
    RESCHEDULED = "rescheduled"


def upgrade() -> None:
    op.create_table(
        'user',
        sa.Column('user_id', sa.INTEGER, primary_key=True, autoincrement=True),
        sa.Column('tg_user_id', sa.INTEGER, unique=True),
        sa.Column('first_name', sa.VARCHAR(255)),
        sa.Column('last_name', sa.VARCHAR(255)),
        sa.Column('created_at', sa.TIMESTAMP, nullable=False, default=sa.text('NOW()')),
        sa.Column('updated_at', sa.TIMESTAMP, onupdate=sa.text('NOW()'))
    )

    op.create_table(
        'client',
        sa.Column('client_id', sa.INTEGER, primary_key=True, autoincrement=True),
        sa.Column('tg_client_id', sa.INTEGER, unique=True),
        sa.Column('first_name', sa.VARCHAR(255)),
        sa.Column('last_name', sa.VARCHAR(255)),
        sa.Column('created_at', sa.TIMESTAMP, nullable=False, default=sa.text('NOW()')),
        sa.Column('updated_at', sa.TIMESTAMP, onupdate=sa.text('NOW()'))
    )

    op.create_table(
        'schedule',
        sa.Column('schedule_id', sa.INTEGER, primary_key=True, autoincrement=True),
        sa.Column('admin_id', sa.INTEGER, ForeignKey('user.user_id', ondelete='CASCADE'), nullable=False),
        sa.Column('date', sa.DATE, nullable=False),
        sa.Column('start_time', sa.TIME, nullable=False),
        sa.Column('end_time', sa.TIME, nullable=False),
        sa.Column('is_active', sa.SMALLINT, nullable=False),
        sa.Column('created_at', sa.TIMESTAMP, nullable=False, default=sa.text('NOW()')),
        sa.Column('updated_at', sa.TIMESTAMP, onupdate=sa.text('NOW()'))
    )

    op.create_table(
        'slot',
        sa.Column('slot_id', sa.INTEGER, primary_key=True, autoincrement=True),
        sa.Column('start_time', sa.TIMESTAMP, nullable=False),
        sa.Column('end_time', sa.TIMESTAMP, nullable=False),
        sa.Column('duration_in_minutes', sa.INTEGER, nullable=False),
        sa.Column('created_at', sa.TIMESTAMP, nullable=False, default=sa.text('NOW()')),
        sa.Column('updated_at', sa.TIMESTAMP, onupdate=sa.text('NOW()'))
    )

    op.create_table(
        'appointment',
        sa.Column('appointment_id', sa.INTEGER, primary_key=True, autoincrement=True),
        sa.Column('user_id', sa.INTEGER, ForeignKey('user.user_id', ondelete='SET NULL')),
        sa.Column('client_id', sa.INTEGER, ForeignKey('client.client_id', ondelete='SET NULL')),
        sa.Column('slot_id', sa.INTEGER, ForeignKey('slot.slot_id', ondelete='SET NULL')),
        sa.Column('description', sa.TEXT),
        sa.Column('location', sa.VARCHAR(512)),
        sa.Column('status', sa.Enum(AppointmentStatusEnum), nullable=False),
        sa.Column('created_at', sa.TIMESTAMP, nullable=False, default=sa.text('NOW()')),
        sa.Column('updated_at', sa.TIMESTAMP, onupdate=sa.text('NOW()'))
    )

def downgrade() -> None:
    op.drop_table('appointment')
    op.drop_table('slot')
    op.drop_table('schedule')
    op.drop_table('client')
    op.drop_table('user')
