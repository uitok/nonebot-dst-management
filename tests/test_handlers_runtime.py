import pytest

from nonebot.adapters.onebot.v11 import Message

from nonebot_plugin_dst_management.handlers import backup as backup_handler
from nonebot_plugin_dst_management.handlers import console as console_handler
from nonebot_plugin_dst_management.handlers import room as room_handler


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


def setup_fake_commands(monkeypatch, module):
    commands = []

    def fake_on_command(*args, **kwargs):
        cmd = FakeCommand()
        commands.append(cmd)
        return cmd

    monkeypatch.setattr(module, "on_command", fake_on_command)
    return commands


@pytest.mark.asyncio
async def test_backup_handlers(monkeypatch):
    commands = setup_fake_commands(monkeypatch, backup_handler)

    async def allow_group(event):
        return True

    async def allow_admin(bot, event):
        return True

    monkeypatch.setattr(backup_handler, "check_group", allow_group)
    monkeypatch.setattr(backup_handler, "check_admin", allow_admin)

    class ApiClient:
        async def get_room_info(self, room_id):
            return {"success": True, "data": {"gameName": "Test Room"}}

        async def list_backups(self, room_id):
            return {"success": True, "data": [{"filename": "a.zip", "size": 0}]}

        async def create_backup(self, room_id):
            return {"success": True}

        async def restore_backup(self, room_id, filename):
            return {"success": True}

    backup_handler.init(ApiClient())

    await commands[0].handlers[0](object(), Message("1"))
    assert commands[0].finished

    await commands[1].handlers[0](object(), object(), Message("1"))
    assert commands[1].sent
    assert commands[1].finished

    await commands[2].handlers[0](object(), object(), Message("1 backup.zip"))
    assert commands[2].sent
    assert commands[2].finished


@pytest.mark.asyncio
async def test_console_handlers(monkeypatch):
    commands = setup_fake_commands(monkeypatch, console_handler)

    async def allow_group(event):
        return True

    async def allow_admin(bot, event):
        return True

    monkeypatch.setattr(console_handler, "check_group", allow_group)
    monkeypatch.setattr(console_handler, "check_admin", allow_admin)

    class ApiClient:
        async def execute_console_command(self, room_id, world_id, command):
            return {"success": True}

    console_handler.init(ApiClient())

    await commands[0].handlers[0](object(), object(), Message("1 c_announce('hi')"))
    assert commands[0].sent
    assert commands[0].finished

    await commands[1].handlers[0](object(), object(), Message("1 hello"))
    assert commands[1].sent
    assert commands[1].finished


@pytest.mark.asyncio
async def test_room_handlers(monkeypatch):
    commands = setup_fake_commands(monkeypatch, room_handler)

    async def allow_group(event):
        return True

    async def allow_admin(bot, event):
        return True

    monkeypatch.setattr(room_handler, "check_group", allow_group)
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

    await commands[0].handlers[0](object(), Message(""))
    assert commands[0].finished

    await commands[1].handlers[0](object(), Message("1"))
    assert commands[1].finished

    await commands[2].handlers[0](object(), object(), Message("1"))
    assert commands[2].sent
    assert commands[2].finished

    await commands[3].handlers[0](object(), object(), Message("1"))
    assert commands[3].sent
    assert commands[3].finished

    await commands[4].handlers[0](object(), object(), Message("1"))
    assert commands[4].sent
    assert commands[4].finished
