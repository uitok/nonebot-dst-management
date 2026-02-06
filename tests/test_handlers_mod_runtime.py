import pytest

from nonebot.adapters.onebot.v11 import Message

from nonebot_plugin_dst_management.handlers import mod as mod_handler
from nonebot_plugin_dst_management.ai.base import AIError


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
async def test_mod_search_paths(monkeypatch):
    commands = setup_fake_commands(monkeypatch, mod_handler)

    async def allow_group(event):
        return True

    monkeypatch.setattr(mod_handler, "check_group", allow_group)

    class ApiClientMissing:
        pass

    mod_handler.init(ApiClientMissing())

    await commands[0].handlers[0](object(), Message(""))
    assert commands[0].finished

    await commands[0].handlers[0](object(), Message("abc"))
    assert commands[0].finished

    class ApiClientFail:
        async def search_mod(self, mode, keyword):
            return {"success": False, "error": "boom"}

    commands = setup_fake_commands(monkeypatch, mod_handler)
    monkeypatch.setattr(mod_handler, "check_group", allow_group)
    mod_handler.init(ApiClientFail())

    await commands[0].handlers[0](object(), Message("flower"))
    assert commands[0].sent
    assert commands[0].finished

    class ApiClientOk:
        async def search_mod(self, mode, keyword):
            return {"success": True, "data": [{"name": "X", "id": "1"}]}

    commands = setup_fake_commands(monkeypatch, mod_handler)
    monkeypatch.setattr(mod_handler, "check_group", allow_group)
    mod_handler.init(ApiClientOk())

    await commands[0].handlers[0](object(), Message("flower"))
    assert commands[0].finished


@pytest.mark.asyncio
async def test_mod_list_and_check(monkeypatch):
    commands = setup_fake_commands(monkeypatch, mod_handler)

    async def allow_group(event):
        return True

    monkeypatch.setattr(mod_handler, "check_group", allow_group)

    class ApiClient:
        async def get_room_info(self, room_id):
            return {"success": True, "data": {"modData": "workshop-1 workshop-1"}}

    mod_handler.init(ApiClient())

    await commands[1].handlers[0](object(), Message("abc"))
    assert commands[1].finished

    await commands[1].handlers[0](object(), Message("1"))
    assert commands[1].finished

    await commands[4].handlers[0](object(), Message("1"))
    assert commands[4].finished

    class ApiClientNoMods:
        async def get_room_info(self, room_id):
            return {"success": True, "data": {"modData": ""}}

    commands = setup_fake_commands(monkeypatch, mod_handler)
    monkeypatch.setattr(mod_handler, "check_group", allow_group)
    mod_handler.init(ApiClientNoMods())

    await commands[4].handlers[0](object(), Message("1"))
    assert commands[4].finished


@pytest.mark.asyncio
async def test_mod_add_and_remove(monkeypatch):
    commands = setup_fake_commands(monkeypatch, mod_handler)

    async def allow_admin(bot, event):
        return True

    monkeypatch.setattr(mod_handler, "check_admin", allow_admin)

    class ApiClientMissing:
        pass

    mod_handler.init(ApiClientMissing())

    await commands[2].handlers[0](object(), object(), Message(""))
    assert commands[2].finished

    await commands[2].handlers[0](object(), object(), Message("a b c"))
    assert commands[2].finished

    await commands[2].handlers[0](object(), object(), Message("1 2 999"))
    assert commands[2].finished

    await commands[3].handlers[0](object(), object(), Message("1 2 mod"))
    assert commands[3].finished

    class ApiClientFail:
        async def download_mod(self, mod_id):
            return {"success": False, "error": "down"}

        async def get_mod_setting_struct(self, mod_id):
            return {"success": True, "data": {}}

        async def update_mod_setting(self, room_id, world_id, mod_id, data):
            return {"success": True}

        async def enable_mod(self, room_id, world_id, mod_id):
            return {"success": True}

    commands = setup_fake_commands(monkeypatch, mod_handler)
    monkeypatch.setattr(mod_handler, "check_admin", allow_admin)
    mod_handler.init(ApiClientFail())

    await commands[2].handlers[0](object(), object(), Message("1 2 999"))
    assert commands[2].sent
    assert commands[2].finished

    class ApiClientOk:
        async def download_mod(self, mod_id):
            return {"success": True}

        async def get_mod_setting_struct(self, mod_id):
            return {"success": True, "data": {"a": 1}}

        async def update_mod_setting(self, room_id, world_id, mod_id, data):
            return {"success": True}

        async def enable_mod(self, room_id, world_id, mod_id):
            return {"success": True}

        async def disable_mod(self, room_id, world_id, mod_id):
            return {"success": False, "error": "no"}

    commands = setup_fake_commands(monkeypatch, mod_handler)
    monkeypatch.setattr(mod_handler, "check_admin", allow_admin)
    mod_handler.init(ApiClientOk())

    await commands[2].handlers[0](object(), object(), Message("1 2 999"))
    assert commands[2].finished

    await commands[3].handlers[0](object(), object(), Message("1 2 999"))
    assert commands[3].sent
    assert commands[3].finished


@pytest.mark.asyncio
async def test_mod_config_save_paths(monkeypatch):
    commands = setup_fake_commands(monkeypatch, mod_handler)

    async def allow_group(event):
        return True

    async def allow_admin(bot, event):
        return True

    monkeypatch.setattr(mod_handler, "check_group", allow_group)
    monkeypatch.setattr(mod_handler, "check_admin", allow_admin)

    class ApiClient:
        pass

    mod_handler.init(ApiClient())

    await commands[5].handlers[0](object(), object(), Message(""))
    assert commands[5].finished

    await commands[5].handlers[0](object(), object(), Message("1 2 --bad"))
    assert commands[5].finished

    await commands[5].handlers[0](object(), object(), Message("1 2 --optimized"))
    assert commands[5].finished

    class FakeParser:
        def __init__(self, api_client, ai_client):
            self._cached = "optimized"

        def get_cached_optimized(self, room_id, world_id):
            return self._cached

        async def parse_mod_config(self, room_id, world_id):
            raise AIError("boom")

    monkeypatch.setattr(mod_handler, "ModConfigParser", FakeParser)

    class ApiClientSave:
        async def save_mod_config(self, room_id, world_id, optimized):
            return {"success": True}

    commands = setup_fake_commands(monkeypatch, mod_handler)
    monkeypatch.setattr(mod_handler, "check_group", allow_group)
    monkeypatch.setattr(mod_handler, "check_admin", allow_admin)
    mod_handler.init(ApiClientSave(), ai_client=object())

    await commands[5].handlers[0](object(), object(), Message("1 2 --optimized"))
    assert commands[5].sent
    assert commands[5].finished
