import pytest

from nonebot.adapters.onebot.v11 import Message

from nonebot_plugin_dst_management.handlers import player_enhanced as player_enhanced_handler


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


class FakeEvent:
    def __init__(self, user_id: int = 123):
        self.user_id = user_id


@pytest.mark.asyncio
async def test_player_online_denied(monkeypatch: pytest.MonkeyPatch) -> None:
    commands = setup_fake_commands(monkeypatch, player_enhanced_handler)

    async def deny_group(event):
        return False

    monkeypatch.setattr(player_enhanced_handler, "check_group", deny_group)

    class ApiClient:
        async def get_online_players(self, room_id):
            raise AssertionError("should not be called")

    player_enhanced_handler.init(ApiClient())

    await commands[0].handlers[0](FakeEvent(), Message("1"))
    assert commands[0].finished
    assert "未授权" in str(commands[0].finished[0])


@pytest.mark.asyncio
async def test_player_online_requires_room_or_default(monkeypatch: pytest.MonkeyPatch) -> None:
    commands = setup_fake_commands(monkeypatch, player_enhanced_handler)

    async def allow_group(event):
        return True

    async def resolve_room_id(qq_id: str, room_arg):
        return None

    monkeypatch.setattr(player_enhanced_handler, "check_group", allow_group)
    monkeypatch.setattr(player_enhanced_handler.default_room, "resolve_room_id", resolve_room_id)

    class ApiClient:
        async def get_online_players(self, room_id):
            raise AssertionError("should not be called")

    player_enhanced_handler.init(ApiClient())

    await commands[0].handlers[0](FakeEvent(), Message(""))
    assert commands[0].finished
    assert "请提供房间ID" in str(commands[0].finished[0])


@pytest.mark.asyncio
async def test_player_online_api_error(monkeypatch: pytest.MonkeyPatch) -> None:
    commands = setup_fake_commands(monkeypatch, player_enhanced_handler)

    async def allow_group(event):
        return True

    monkeypatch.setattr(player_enhanced_handler, "check_group", allow_group)

    class ApiClient:
        async def get_online_players(self, room_id):
            return {"success": False, "error": "boom"}

    player_enhanced_handler.init(ApiClient())

    await commands[0].handlers[0](FakeEvent(), Message("1"))
    assert commands[0].finished
    assert "获取失败" in str(commands[0].finished[0])


@pytest.mark.asyncio
async def test_player_online_empty_players(monkeypatch: pytest.MonkeyPatch) -> None:
    commands = setup_fake_commands(monkeypatch, player_enhanced_handler)

    async def allow_group(event):
        return True

    monkeypatch.setattr(player_enhanced_handler, "check_group", allow_group)

    class ApiClient:
        async def get_online_players(self, room_id):
            return {"success": True, "data": []}

    player_enhanced_handler.init(ApiClient())

    await commands[0].handlers[0](FakeEvent(), Message("1"))
    assert commands[0].finished
    assert "没有玩家在线" in str(commands[0].finished[0])


@pytest.mark.asyncio
async def test_player_online_success_triggers_reward_check(monkeypatch: pytest.MonkeyPatch) -> None:
    commands = setup_fake_commands(monkeypatch, player_enhanced_handler)

    async def allow_group(event):
        return True

    monkeypatch.setattr(player_enhanced_handler, "check_group", allow_group)

    called = {"room_id": None}

    class Monitor:
        async def check_room_pending_rewards(self, room_id):
            called["room_id"] = room_id
            raise RuntimeError("boom")  # should be swallowed

    monkeypatch.setattr(player_enhanced_handler, "get_sign_monitor", lambda: Monitor())

    class ApiClient:
        async def get_online_players(self, room_id):
            return {
                "success": True,
                "data": [
                    {"uid": "KU123", "name": "Alice", "duration": 3661},
                ],
            }

    player_enhanced_handler.init(ApiClient())

    await commands[0].handlers[0](FakeEvent(), Message("1"))
    assert called["room_id"] == 1
    assert commands[0].finished
    msg = str(commands[0].finished[0])
    assert "KU123" in msg
    assert "Alice" in msg
    assert "1h 1m" in msg

