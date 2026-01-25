import pytest

from datetime import datetime

from src.app.models import Slot
from src.app.services import SlotService
from src.infrastructure.postgres.databaseengine import DatabaseEngine

from tests.integration.common.fixture import clean_database

def test_slot_service_add_slot(clean_database):
    engine = DatabaseEngine()
    service = SlotService(engine)

    slot = Slot(
        start_time = datetime(2025, 10, 15, 12, 0 ,0),
        end_time = datetime(2025, 10, 15, 12, 0,0),
        duration_in_minutes = 60
    )

    service.add_slot(slot)
    result = service.get_slot_by_id(1)

    expected = Slot(
        slot_id = 1,
        start_time=datetime(2025, 10, 15, 12, 0, 0),
        end_time=datetime(2025, 10, 15, 12, 0, 0),
        duration_in_minutes=60
    )

    assert result == expected

def test_slot_service_add_slot_raise_error(clean_database):
    engine = DatabaseEngine()
    service = SlotService(engine)

    slot = Slot(
        slot_id = 1,
        start_time = datetime(2025, 10, 15, 12, 0 ,0),
        end_time = datetime(2025, 10, 15, 12, 0,0),
        duration_in_minutes = 60
    )

    slot2 = Slot(
        slot_id = 1,
        start_time = datetime(2025, 10, 15, 12, 0 ,0),
        end_time = datetime(2025, 10, 15, 12, 0,0),
        duration_in_minutes = 60
    )

    service.add_slot(slot)

    with pytest.raises(Exception):
        service.add_slot(slot2)


def test_slot_service_get_slot_by_id_raise_error(clean_database):
    engine = DatabaseEngine()
    service = SlotService(engine)

    with pytest.raises(ValueError):
        service.get_slot_by_id(9999)

def test_slot_service_get_slots_by_date(clean_database):
    engine = DatabaseEngine()
    service = SlotService(engine)

    dt = datetime(2025, 11, 11).date()

    slot = Slot(
        slot_id = 1,
        start_time = datetime(2025, 11, 11, 12, 0 ,0),
        end_time = datetime(2025, 11, 11, 13, 00,0),
        duration_in_minutes = 60
    )

    slot2 = Slot(
        slot_id = 2,
        start_time = datetime(2025, 11, 11, 13, 30 ,0),
        end_time = datetime(2025, 11, 11, 15, 0,0),
        duration_in_minutes = 90
    )

    slot3 = Slot(
        slot_id = 3,
        start_time = datetime(2025, 11, 11, 16, 30 ,0),
        end_time = datetime(2025, 11, 11, 17, 30,0),
        duration_in_minutes = 60
    )

    slots = [slot, slot2, slot3]

    for s in slots:
        service.add_slot(s)

    result = service.get_slots_by_date(dt)

    assert all(a == b for a, b in zip(slots, result))

def test_slot_service_get_slots_by_date_return_no_one(clean_database):
    engine = DatabaseEngine()
    service = SlotService(engine)

    dt = datetime(2025, 11, 11).date()

    expected = []
    result = service.get_slots_by_date(dt)

    assert expected == result
