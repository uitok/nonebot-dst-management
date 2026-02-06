import pytest

from nonebot_plugin_dst_management.handlers import ai_mod_apply as apply_handler


class DummyMessage:
    """模拟 Message 类"""
    def __init__(self, text: str = "") -> None:
        self.text = str(text)

    def extract_plain_text(self) -> str:
        return self.text or ""


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
async def test_mod_config_show_handler_cached(monkeypatch):
    commands = setup_fake_commands(monkeypatch, apply_handler)

    async def allow_group(event):
        return True

    monkeypatch.setattr(apply_handler, "check_group", allow_group)

    class FakeParser:
        def __init__(self, api_client, ai_client):
            pass

        def get_cached_result(self, room_id, world_id):
            return {"report": "ok"}

    monkeypatch.setattr(apply_handler, "ModConfigParser", FakeParser)

    apply_handler.init(object(), object())

    await commands[0].handlers[0](object(), DummyMessage("1 Master"))
    assert commands[0].finished


@pytest.mark.asyncio
async def test_mod_config_show_handler_no_cache(monkeypatch):
    commands = setup_fake_commands(monkeypatch, apply_handler)

    async def allow_group(event):
        return True

    monkeypatch.setattr(apply_handler, "check_group", allow_group)

    class FakeParser:
        def __init__(self, api_client, ai_client):
            pass

        def get_cached_result(self, room_id, world_id):
            return None

    monkeypatch.setattr(apply_handler, "ModConfigParser", FakeParser)

    apply_handler.init(object(), object())

    await commands[0].handlers[0](object(), DummyMessage("1 Master"))
    assert commands[0].finished


@pytest.mark.asyncio
async def test_mod_config_apply_dry_run(monkeypatch):
    commands = setup_fake_commands(monkeypatch, apply_handler)

    async def allow_group(event):
        return True

    async def allow_admin(bot, event):
        return True

    monkeypatch.setattr(apply_handler, "check_group", allow_group)
    monkeypatch.setattr(apply_handler, "check_admin", allow_admin)

    class FakeParser:
        def __init__(self, api_client, ai_client):
            pass

        def get_cached_result(self, room_id, world_id):
            return {"optimized_config": "new", "report": "ok"}

        async def fetch_modoverrides(self, room_id, world_id):
            return "old"

    monkeypatch.setattr(apply_handler, "ModConfigParser", FakeParser)

    apply_handler.init(object(), object())

    await commands[1].handlers[0](object(), DummyMessage("1 Master --dry-run"))
    assert commands[1].finished
    text = commands[1].finished[-1].extract_plain_text()
    assert "配置差异预览" in text


@pytest.mark.asyncio
async def test_mod_config_apply_auto(monkeypatch):
    commands = setup_fake_commands(monkeypatch, apply_handler)

    async def allow_group(event):
        return True

    async def allow_admin(bot, event):
        return True

    monkeypatch.setattr(apply_handler, "check_group", allow_group)
    monkeypatch.setattr(apply_handler, "check_admin", allow_admin)

    class FakeParser:
        def __init__(self, api_client, ai_client):
            pass

        def get_cached_result(self, room_id, world_id):
            return {"optimized_config": "new", "report": "ok"}

    monkeypatch.setattr(apply_handler, "ModConfigParser", FakeParser)

    class FakeApi:
        def __init__(self):
            self.saved = []
            self.restarted = 0

        async def save_mod_config(self, room_id, world_id, config):
            self.saved.append((room_id, world_id, config))
            return {"success": True}

        async def restart_room(self, room_id):
            self.restarted += 1
            return {"success": True}

    fake_api = FakeApi()
    apply_handler.init(fake_api, object())

    await commands[1].handlers[0](object(), DummyMessage("1 Master --auto"))
    assert fake_api.saved
    assert fake_api.restarted == 1
    assert commands[1].finished


@pytest.mark.asyncio
async def test_mod_config_apply_requires_admin(monkeypatch):
    commands = setup_fake_commands(monkeypatch, apply_handler)

    async def allow_group(event):
        return True

    async def deny_admin(bot, event):
        return False

    monkeypatch.setattr(apply_handler, "check_group", allow_group)
    monkeypatch.setattr(apply_handler, "check_admin", deny_admin)

    class FakeParser:
        def __init__(self, api_client, ai_client):
            pass

        def get_cached_result(self, room_id, world_id):
            return {"optimized_config": "new", "report": "ok"}

    monkeypatch.setattr(apply_handler, "ModConfigParser", FakeParser)

    apply_handler.init(object(), object())

    await commands[1].handlers[0](object(), DummyMessage("1 Master --auto"))
    assert commands[1].finished


@pytest.mark.asyncio
async def test_mod_config_apply_no_auto(monkeypatch):
    commands = setup_fake_commands(monkeypatch, apply_handler)

    async def allow_group(event):
        return True

    async def allow_admin(bot, event):
        return True

    monkeypatch.setattr(apply_handler, "check_group", allow_group)
    monkeypatch.setattr(apply_handler, "check_admin", allow_admin)

    class FakeParser:
        def __init__(self, api_client, ai_client):
            pass

        def get_cached_result(self, room_id, world_id):
            return {"optimized_config": "new", "report": "ok"}

    monkeypatch.setattr(apply_handler, "ModConfigParser", FakeParser)

    apply_handler.init(object(), object())

    msg = DummyMessage("1 Master --dry-run")
    await commands[1].handlers[0](object(), msg)
    assert commands[1].finished
