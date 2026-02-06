"""
默认房间功能测试
"""

import pytest

from nonebot_plugin_dst_management.database import (
    clear_user_default_room,
    get_user_default_room,
    init_db,
    set_db_path,
    set_user_default_room,
)
from nonebot_plugin_dst_management.database.connection import get_db_path
from nonebot_plugin_dst_management.handlers import default_room


@pytest.fixture
async def db_path(tmp_path):
    original = get_db_path()
    db_file = tmp_path / "sign.db"
    set_db_path(db_file)
    await init_db()
    yield db_file
    set_db_path(original)


@pytest.mark.asyncio
async def test_set_get_clear_default_room(db_path):
    qq_id = "123"

    assert await get_user_default_room(qq_id) is None

    await set_user_default_room(qq_id, 2)
    assert await get_user_default_room(qq_id) == 2

    await set_user_default_room(qq_id, 5)
    assert await get_user_default_room(qq_id) == 5

    await clear_user_default_room(qq_id)
    assert await get_user_default_room(qq_id) is None


@pytest.mark.asyncio
async def test_resolve_room_id_priority(db_path):
    qq_id = "456"

    await set_user_default_room(qq_id, 3)

    assert await default_room.resolve_room_id(qq_id, "5") == 5
    assert await default_room.resolve_room_id(qq_id, None) == 3


@pytest.mark.asyncio
async def test_resolve_room_id_invalid_arg(db_path):
    qq_id = "789"

    await set_user_default_room(qq_id, 2)

    assert await default_room.resolve_room_id(qq_id, "abc") is None
    assert await default_room.resolve_room_id(qq_id, "") is None


@pytest.mark.asyncio
async def test_resolve_room_id_no_default(db_path):
    qq_id = "000"

    assert await default_room.resolve_room_id(qq_id, None) is None
