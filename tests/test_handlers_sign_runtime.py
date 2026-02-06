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


@pytest.mark.asyncio
async def test_sign_handlers(monkeypatch):
    commands = setup_fake_commands(monkeypatch, sign_handler)

    async def allow_group(event):
        return True

    monkeypatch.setattr(sign_handler, "check_group", allow_group)

    class FakeService:
        async def bind_user(self, qq_id, ku_id, room_id, player_name=None):
            return type("Result", (), {"success": True, "message": "绑定成功"})()

        async def sign_in(self, qq_id, room_id, sign_date=None, is_full_moon=False):
            return type("Result", (), {"success": True, "message": "签到成功"})()

    monkeypatch.setattr(sign_handler, "SignService", lambda api_client: FakeService())

    class ApiClient:
        pass

    sign_handler.init(ApiClient())

    event = FakeEvent()
    await commands[0].handlers[0](event, Message("KU_TEST 1"))
    assert commands[0].finished

    await commands[1].handlers[0](event, Message("1"))
    assert commands[1].sent
    assert commands[1].finished
