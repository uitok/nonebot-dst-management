from __future__ import annotations

from datetime import date

import httpx
import pytest

from tests.mock_api import app

from nonebot_plugin_dst_management.client.api_client import DSTApiClient
from nonebot_plugin_dst_management.database import (
    create_sign_record,
    create_user_binding,
    get_sign_record,
    init_db,
    set_db_path,
)
from nonebot_plugin_dst_management.database.connection import get_db_path
from nonebot_plugin_dst_management.services.monitors.sign_monitor import SignMonitor


@pytest.fixture
async def db_path(tmp_path):
    original = get_db_path()
    db_file = tmp_path / "sign_monitor.db"
    set_db_path(db_file)
    await init_db()
    yield db_file
    set_db_path(original)


@pytest.fixture
async def api_client():
    client = DSTApiClient(base_url="http://testserver", token="test")
    transport = httpx.ASGITransport(app=app)
    client.client = httpx.AsyncClient(
        transport=transport,
        base_url="http://testserver/v3",
        headers={
            "X-DMP-TOKEN": "test",
            "Content-Type": "application/json",
        },
    )
    yield client
    await client.client.aclose()


@pytest.mark.asyncio
async def test_check_room_pending_rewards_online_and_offline(db_path, api_client):
    await create_user_binding("100", "KU_TEST1", 1, "player1")
    await create_user_binding("101", "KU_OFF", 1, "player2")

    sign_day = date(2026, 2, 5)
    online_id = await create_sign_record(
        "100",
        1,
        sign_day,
        1,
        [{"prefab": "goldnugget", "amount": 10}],
        status=0,
    )
    offline_id = await create_sign_record(
        "101",
        1,
        sign_day,
        1,
        [{"prefab": "cutgrass", "amount": 5}],
        status=0,
    )

    monitor = SignMonitor(api_client)
    await monitor.check_room_pending_rewards(1)

    online_record = await get_sign_record("100", sign_day, room_id=1)
    offline_record = await get_sign_record("101", sign_day, room_id=1)

    assert online_record is not None
    assert offline_record is not None
    assert online_record.id == online_id
    assert offline_record.id == offline_id
    assert online_record.status == 1
    assert offline_record.status == 0


@pytest.mark.asyncio
async def test_check_user_pending_rewards(db_path, api_client):
    await create_user_binding("200", "KU_TEST1", 1, "player1")
    sign_day = date(2026, 2, 5)
    await create_sign_record(
        "200",
        1,
        sign_day,
        1,
        [{"prefab": "goldnugget", "amount": 10}],
        status=0,
    )
    await create_sign_record(
        "200",
        1,
        date(2026, 2, 4),
        1,
        [{"prefab": "cutgrass", "amount": 5}],
        status=0,
    )

    monitor = SignMonitor(api_client)
    success = await monitor.check_user_pending_rewards("200", "KU_TEST1", 1)
    assert success is True

    record = await get_sign_record("200", sign_day, room_id=1)
    assert record is not None
    assert record.status == 1


@pytest.mark.asyncio
async def test_check_user_pending_rewards_offline(db_path, api_client):
    await create_user_binding("201", "KU_OFF", 1, "player2")
    sign_day = date(2026, 2, 5)
    await create_sign_record(
        "201",
        1,
        sign_day,
        1,
        [{"prefab": "goldnugget", "amount": 10}],
        status=0,
    )

    monitor = SignMonitor(api_client)
    success = await monitor.check_user_pending_rewards("201", "KU_OFF", 1)
    assert success is False

    record = await get_sign_record("201", sign_day, room_id=1)
    assert record is not None
    assert record.status == 0
