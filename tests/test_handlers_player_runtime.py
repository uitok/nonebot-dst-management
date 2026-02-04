import pytest

from nonebot.adapters.onebot.v11 import Message

from nonebot_plugin_dst_management.handlers import player as player_handler


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
async def test_players_handler_success_and_error(monkeypatch):
    commands = setup_fake_commands(monkeypatch, player_handler)

    async def allow_group(event):
        return True

    monkeypatch.setattr(player_handler, "check_group", allow_group)

    class ApiClient:
        async def get_room_info(self, room_id):
            return {"success": False}

        async def get_online_players(self, room_id):
            return {"success": True, "data": [{"name": "A"}]}

    player_handler.init(ApiClient())

    await commands[0].handlers[0](object(), Message("1"))
    assert commands[0].finished

    class ApiClientFail:
        async def get_room_info(self, room_id):
            return {"success": True, "data": {"gameName": "Room"}}

        async def get_online_players(self, room_id):
            return {"success": False, "error": "boom"}

    commands = setup_fake_commands(monkeypatch, player_handler)
    monkeypatch.setattr(player_handler, "check_group", allow_group)
    player_handler.init(ApiClientFail())
    await commands[0].handlers[0](object(), Message("1"))
    assert commands[0].finished


@pytest.mark.asyncio
async def test_players_handler_invalid_args(monkeypatch):
    commands = setup_fake_commands(monkeypatch, player_handler)

    async def allow_group(event):
        return True

    monkeypatch.setattr(player_handler, "check_group", allow_group)

    class ApiClient:
        async def get_room_info(self, room_id):
            return {"success": True, "data": {"gameName": "Room"}}

        async def get_online_players(self, room_id):
            return {"success": True, "data": []}

    player_handler.init(ApiClient())

    await commands[0].handlers[0](object(), Message("abc"))
    assert commands[0].finished


@pytest.mark.asyncio
async def test_kick_handler_paths(monkeypatch):
    commands = setup_fake_commands(monkeypatch, player_handler)

    async def allow_admin(bot, event):
        return True

    monkeypatch.setattr(player_handler, "check_admin", allow_admin)

    class ApiClient:
        async def execute_console_command(self, room_id, world_id, command):
            return {"success": True}

    player_handler.init(ApiClient())

    await commands[1].handlers[0](object(), object(), Message(""))
    assert commands[1].finished

    await commands[1].handlers[0](object(), object(), Message("abc 123"))
    assert commands[1].finished

    await commands[1].handlers[0](object(), object(), Message("1 KU123"))
    assert commands[1].sent
    assert commands[1].finished

    class ApiClientFail:
        async def execute_console_command(self, room_id, world_id, command):
            return {"success": False, "error": "nope"}

    commands = setup_fake_commands(monkeypatch, player_handler)
    monkeypatch.setattr(player_handler, "check_admin", allow_admin)
    player_handler.init(ApiClientFail())

    await commands[1].handlers[0](object(), object(), Message("1 KU123"))
    assert commands[1].finished
