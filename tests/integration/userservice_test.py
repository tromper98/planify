from src.app.models import User
from src.app.services import UserService
from src.infrastructure.postgres.databaseengine import DatabaseEngine

from tests.integration.common.fixture import clean_database


def test_admin_service_add_admin(clean_database):
    engine = DatabaseEngine()
    service = UserService(engine)

    user = User(
        user_id=1,
        tg_user_id=1,
        first_name='Test',
        last_name='Test'
    )

    service.add_user(user)

    result = service.get_user_by_id(user_id=1)

    assert user == result