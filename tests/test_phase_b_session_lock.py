import pytest

from nonebot.adapters.onebot.v11 import Message

from nonebot_plugin_dst_management.database import (
    clear_user_last_room,
    get_user_last_room,
    init_db,
    set_db_path,
    set_user_default_room,
    set_user_last_room,
)
from nonebot_plugin_dst_management.database.connection import get_db_path
from nonebot_plugin_dst_management.helpers.room_context import RoomSource, remember_room, resolve_room_id
from nonebot_plugin_dst_management.handlers import room as room_handler


class FakeEvent:
    def __init__(self, user_id: int = 123, group_id: int = 456):
        self.user_id = user_id
        self.group_id = group_id


@pytest.fixture
async def db_path(tmp_path):
    original = get_db_path()
    db_file = tmp_path / "sign.db"
    set_db_path(db_file)
    await init_db()
    yield db_file
    set_db_path(original)


@pytest.mark.asyncio
async def test_last_room_persistence(db_path):
    key = "123"

    assert await get_user_last_room(key) is None

    await set_user_last_room(key, 2)
    assert await get_user_last_room(key) == 2

    await clear_user_last_room(key)
    assert await get_user_last_room(key) is None


@pytest.mark.asyncio
async def test_resolve_room_id_priority_last_then_default(db_path):
    event = FakeEvent(user_id=100, group_id=200)

    # With only default room set, should fall back to default.
    await set_user_default_room("100", 9)
    resolved = await resolve_room_id(event, None)
    assert resolved is not None
    assert resolved.room_id == 9
    assert resolved.source == RoomSource.DEFAULT

    # After remembering a room, should use session lock first.
    await remember_room(event, 3)
    resolved = await resolve_room_id(event, None)
    assert resolved is not None
    assert resolved.room_id == 3
    assert resolved.source == RoomSource.LAST


@pytest.mark.asyncio
async def test_session_lock_across_multiple_commands(db_path, monkeypatch: pytest.MonkeyPatch):
    # Patch on_command to capture handlers.
    commands = []

    class FakeCommand:
        def __init__(self):
            self.handlers = []
            self.sent = []
            self.finished = []

        def handle(self):
            def decorator(func):
                self.handlers.append(func)
                return func

            return decorator

        async def send(self, message):
            self.sent.append(message)

        async def finish(self, message):
            self.finished.append(message)

    def fake_on_command(*args, **kwargs):
        cmd = FakeCommand()
        commands.append(cmd)
        return cmd

    monkeypatch.setattr(room_handler, "on_command", fake_on_command)

    async def allow_admin(bot, event):
        return True

    monkeypatch.setattr(room_handler, "check_admin", allow_admin)

    class ApiClient:
        async def get_room_list(self, page, page_size):
            return {"success": True, "data": {"rows": [], "totalCount": 0}}

        async def get_room_info(self, room_id):
            return {"success": True, "data": {"id": room_id, "gameName": "Room"}}

        async def get_world_list(self, room_id):
            return {"success": True, "data": {"rows": []}}

        async def get_online_players(self, room_id):
            return {"success": True, "data": []}

        async def activate_room(self, room_id):
            return {"success": True}

        async def deactivate_room(self, room_id):
            return {"success": True}

        async def restart_room(self, room_id):
            return {"success": True}

    room_handler.init(ApiClient())

    # Commands order in room_handler.init: list, info, start, stop, restart
    start_cmd = commands[2]
    stop_cmd = commands[3]

    event = FakeEvent(user_id=111, group_id=222)

    # First command pins the room context.
    await start_cmd.handlers[0](object(), event, Message("2"))
    assert start_cmd.sent

    # Second command omits room id and should use last room automatically.
    await stop_cmd.handlers[0](object(), event, Message(""))
    assert stop_cmd.sent
    assert "2" in str(stop_cmd.sent[-1])
    assert "上次操作" in str(stop_cmd.sent[-1])

