import pytest

from nonebot.adapters.onebot.v11 import Message

from nonebot_plugin_dst_management.handlers import sign as sign_handler


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
    def __init__(self, user_id="123", session_id="group_1"):
        self.user_id = user_id
        self._session_id = session_id

    def get_session_id(self):
        return self._session_id


def make_service(bind_result=None, sign_result=None):
    class FakeService:
        async def bind_user(self, qq_id, ku_id, room_id, player_name=None):
            return bind_result

        async def unbind_user(self, qq_id, room_id):
            return bind_result

        async def sign_in(self, qq_id, room_id, sign_date=None, is_full_moon=False):
            return sign_result

    return FakeService()


@pytest.mark.asyncio
async def test_sign_bind_missing_args(monkeypatch):
    commands = setup_fake_commands(monkeypatch, sign_handler)

    async def allow_group(event):
        return True

    monkeypatch.setattr(sign_handler, "check_group", allow_group)
    monkeypatch.setattr(sign_handler, "SignService", lambda api_client: make_service())

    sign_handler.init(object())

    event = FakeEvent()
    await commands[0].handlers[0](event, Message(""))

    assert commands[0].finished
    assert "用法" in str(commands[0].finished[-1])


@pytest.mark.asyncio
async def test_sign_bind_invalid_room(monkeypatch):
    commands = setup_fake_commands(monkeypatch, sign_handler)

    async def allow_group(event):
        return True

    monkeypatch.setattr(sign_handler, "check_group", allow_group)
    monkeypatch.setattr(sign_handler, "SignService", lambda api_client: make_service())

    sign_handler.init(object())

    event = FakeEvent()
    await commands[0].handlers[0](event, Message("KU_TEST abc"))

    assert commands[0].finished
    assert "房间ID" in str(commands[0].finished[-1])


@pytest.mark.asyncio
async def test_sign_bind_success(monkeypatch):
    commands = setup_fake_commands(monkeypatch, sign_handler)

    async def allow_group(event):
        return True

    bind_result = type("Result", (), {"success": True, "message": "绑定成功"})()
    monkeypatch.setattr(sign_handler, "check_group", allow_group)
    monkeypatch.setattr(sign_handler, "SignService", lambda api_client: make_service(bind_result=bind_result))

    sign_handler.init(object())

    event = FakeEvent()
    await commands[0].handlers[0](event, Message("KU_TEST 2"))

    assert commands[0].finished
    assert "绑定成功" in str(commands[0].finished[-1])


@pytest.mark.asyncio
async def test_sign_command_bind_hint(monkeypatch):
    commands = setup_fake_commands(monkeypatch, sign_handler)

    async def allow_group(event):
        return True

    monkeypatch.setattr(sign_handler, "check_group", allow_group)
    monkeypatch.setattr(sign_handler, "SignService", lambda api_client: make_service())

    sign_handler.init(object())

    event = FakeEvent()
    await commands[2].handlers[0](event, Message("bind KU_TEST"))

    assert commands[2].finished
    assert "sign bind" in str(commands[2].finished[-1])


@pytest.mark.asyncio
async def test_sign_command_invalid_room(monkeypatch):
    commands = setup_fake_commands(monkeypatch, sign_handler)

    async def allow_group(event):
        return True

    monkeypatch.setattr(sign_handler, "check_group", allow_group)
    monkeypatch.setattr(sign_handler, "SignService", lambda api_client: make_service())

    sign_handler.init(object())

    event = FakeEvent()
    await commands[2].handlers[0](event, Message("abc"))

    assert commands[2].finished
    assert "房间ID" in str(commands[2].finished[-1])


@pytest.mark.asyncio
async def test_sign_command_use_default_room(monkeypatch):
    commands = setup_fake_commands(monkeypatch, sign_handler)

    async def allow_group(event):
        return True

    async def resolve_room_id(_qq_id, _room_arg):
        return 1

    monkeypatch.setattr(sign_handler.default_room, "resolve_room_id", resolve_room_id)

    sign_result = type("Result", (), {"success": True, "message": "签到成功", "user": None})()
    monkeypatch.setattr(sign_handler, "check_group", allow_group)
    monkeypatch.setattr(sign_handler, "SignService", lambda api_client: make_service(sign_result=sign_result))
    monkeypatch.setattr(sign_handler, "get_sign_monitor", lambda: None)

    sign_handler.init(object())

    event = FakeEvent()
    await commands[2].handlers[0](event, Message(""))

    assert commands[2].sent
    assert commands[2].finished
    assert "签到成功" in str(commands[2].finished[-1])
