from datetime import date, timedelta

import pytest

from nonebot_plugin_dst_management.database import (
    create_user_binding,
    get_user_binding,
    init_db,
    set_db_path,
    update_user_sign_stats,
)
from nonebot_plugin_dst_management.database.connection import get_db_path
from nonebot_plugin_dst_management.services.sign_service import SignService


class FakeApiClient:
    def __init__(self):
        self.commands = []

    async def execute_console_command(self, room_id, world_id, command):
        self.commands.append((room_id, world_id, command))
        return {"success": True}

    async def get_room_players(self, room_id: int):
        return {
            "success": True,
            "data": [
                {"uid": "KU_TEST", "name": "TestPlayer"}
            ],
        }


@pytest.fixture
async def db_path(tmp_path):
    original = get_db_path()
    db_file = tmp_path / "sign.db"
    set_db_path(db_file)
    await init_db()
    yield db_file
    set_db_path(original)


@pytest.mark.asyncio
async def test_sign_bind_and_sign(db_path):
    api_client = FakeApiClient()
    service = SignService(api_client)

    bind_result = await service.bind_user("100", "KU_TEST", 1)
    assert bind_result.success

    sign_result = await service.sign_in("100", 1, sign_date=date(2026, 2, 5))
    assert sign_result.success
    assert sign_result.reward is not None
    assert api_client.commands

    user = await get_user_binding("100", 1)
    assert user is not None
    assert user.sign_count == 1
    assert user.continuous_days == 1
    assert user.last_sign_time == date(2026, 2, 5)

    second = await service.sign_in("100", 1, sign_date=date(2026, 2, 5))
    assert not second.success


@pytest.mark.asyncio
async def test_sign_continuous_days(db_path):
    api_client = FakeApiClient()
    service = SignService(api_client)

    await create_user_binding("200", "KU_TEST2", 2)
    yesterday = date(2026, 2, 4)
    await update_user_sign_stats(
        "200",
        2,
        last_sign_time=yesterday,
        sign_count=2,
        continuous_days=2,
        level=1,
        total_points=0,
    )

    result = await service.sign_in("200", 2, sign_date=date(2026, 2, 5))
    assert result.success

    user = await get_user_binding("200", 2)
    assert user is not None
    assert user.continuous_days == 3
    assert user.sign_count == 3
