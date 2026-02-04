import pytest

from nonebot.adapters.onebot.v11 import Message

from nonebot_plugin_dst_management.ai.base import AIError
from nonebot_plugin_dst_management.handlers import ai_analyze as analyze_handler
from nonebot_plugin_dst_management.handlers import ai_recommend as recommend_handler
from nonebot_plugin_dst_management.handlers import ai_mod_parse as parse_handler
from nonebot_plugin_dst_management.handlers import ai_archive as archive_handler
from nonebot_plugin_dst_management.handlers import ai_qa as qa_handler


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
async def test_ai_analyze_handler(monkeypatch):
    commands = setup_fake_commands(monkeypatch, analyze_handler)

    class FakeAnalyzer:
        def __init__(self, api_client, ai_client):
            pass

        async def analyze_server(self, room_id):
            return "report"

    monkeypatch.setattr(analyze_handler, "ServerConfigAnalyzer", FakeAnalyzer)

    analyze_handler.init(object(), object())

    await commands[0].handlers[0](object(), Message("abc"))
    assert commands[0].finished

    await commands[0].handlers[0](object(), Message("1"))
    assert commands[0].sent
    assert commands[0].finished

    class FakeAnalyzerFail:
        def __init__(self, api_client, ai_client):
            pass

        async def analyze_server(self, room_id):
            raise AIError("bad")

    commands = setup_fake_commands(monkeypatch, analyze_handler)
    monkeypatch.setattr(analyze_handler, "ServerConfigAnalyzer", FakeAnalyzerFail)
    analyze_handler.init(object(), object())

    await commands[0].handlers[0](object(), Message("1"))
    assert commands[0].finished


@pytest.mark.asyncio
async def test_ai_recommend_handler(monkeypatch):
    commands = setup_fake_commands(monkeypatch, recommend_handler)

    async def allow_group(event):
        return True

    monkeypatch.setattr(recommend_handler, "check_group", allow_group)

    class FakeRecommender:
        def __init__(self, api_client, ai_client):
            pass

        async def recommend_mods(self, room_id, mod_type):
            return {"report": "ok"}

    monkeypatch.setattr(recommend_handler, "ModRecommender", FakeRecommender)

    recommend_handler.init(object(), object())

    await commands[0].handlers[0](object(), Message(""))
    assert commands[0].finished

    await commands[0].handlers[0](object(), Message("abc"))
    assert commands[0].finished

    await commands[0].handlers[0](object(), Message("1 pve"))
    assert commands[0].sent
    assert commands[0].finished

    class FakeRecommenderFail:
        def __init__(self, api_client, ai_client):
            pass

        async def recommend_mods(self, room_id, mod_type):
            raise AIError("bad")

    commands = setup_fake_commands(monkeypatch, recommend_handler)
    monkeypatch.setattr(recommend_handler, "check_group", allow_group)
    monkeypatch.setattr(recommend_handler, "ModRecommender", FakeRecommenderFail)
    recommend_handler.init(object(), object())

    await commands[0].handlers[0](object(), Message("1"))
    assert commands[0].finished


@pytest.mark.asyncio
async def test_ai_mod_parse_handler(monkeypatch):
    commands = setup_fake_commands(monkeypatch, parse_handler)

    async def allow_group(event):
        return True

    monkeypatch.setattr(parse_handler, "check_group", allow_group)

    class FakeParser:
        def __init__(self, api_client, ai_client):
            pass

        async def parse_mod_config(self, room_id, world_id):
            return {"report": "ok"}

    monkeypatch.setattr(parse_handler, "ModConfigParser", FakeParser)

    parse_handler.init(object(), object())

    await commands[0].handlers[0](object(), Message(""))
    assert commands[0].finished

    await commands[0].handlers[0](object(), Message("1"))
    assert commands[0].finished

    await commands[0].handlers[0](object(), Message("abc 1"))
    assert commands[0].finished

    await commands[0].handlers[0](object(), Message("1 2"))
    assert commands[0].sent
    assert commands[0].finished

    class FakeParserFail:
        def __init__(self, api_client, ai_client):
            pass

        async def parse_mod_config(self, room_id, world_id):
            raise AIError("bad")

    commands = setup_fake_commands(monkeypatch, parse_handler)
    monkeypatch.setattr(parse_handler, "check_group", allow_group)
    monkeypatch.setattr(parse_handler, "ModConfigParser", FakeParserFail)
    parse_handler.init(object(), object())

    await commands[0].handlers[0](object(), Message("1 2"))
    assert commands[0].finished


@pytest.mark.asyncio
async def test_ai_archive_handler(monkeypatch, tmp_path):
    commands = setup_fake_commands(monkeypatch, archive_handler)

    async def allow_group(event):
        return True

    monkeypatch.setattr(archive_handler, "check_group", allow_group)

    archive_path = tmp_path / "a.zip"
    archive_path.write_bytes(b"zip")

    class FakeArchiveService:
        async def prepare_archive(self, source):
            return {"success": True, "path": str(archive_path), "cleanup": True}

        def cleanup_file(self, path):
            pass

    class FakeAnalyzer:
        def __init__(self, ai_client):
            pass

        async def analyze_archive(self, content):
            return "report"

    monkeypatch.setattr(archive_handler, "ArchiveService", FakeArchiveService)
    monkeypatch.setattr(archive_handler, "ArchiveAnalyzer", FakeAnalyzer)

    archive_handler.init(object())

    await commands[0].handlers[0](object(), Message(""))
    assert commands[0].finished

    await commands[0].handlers[0](object(), Message("/tmp/a.zip"))
    assert commands[0].sent
    assert commands[0].finished

    class FakeAnalyzerFail:
        def __init__(self, ai_client):
            pass

        async def analyze_archive(self, content):
            raise AIError("bad")

    commands = setup_fake_commands(monkeypatch, archive_handler)
    monkeypatch.setattr(archive_handler, "check_group", allow_group)
    monkeypatch.setattr(archive_handler, "ArchiveService", FakeArchiveService)
    monkeypatch.setattr(archive_handler, "ArchiveAnalyzer", FakeAnalyzerFail)
    archive_handler.init(object())

    await commands[0].handlers[0](object(), Message("/tmp/a.zip"))
    assert commands[0].finished


@pytest.mark.asyncio
async def test_ai_qa_handler(monkeypatch):
    commands = setup_fake_commands(monkeypatch, qa_handler)

    async def allow_group(event):
        return True

    monkeypatch.setattr(qa_handler, "check_group", allow_group)

    class FakeQA:
        def __init__(self, ai_client):
            pass

        async def ask(self, question, **kwargs):
            return "answer"

    monkeypatch.setattr(qa_handler, "QASystem", FakeQA)

    qa_handler.init(object())

    await commands[0].handlers[0](object(), Message(""))
    assert commands[0].finished

    await commands[0].handlers[0](object(), Message("hi"))
    assert commands[0].sent
    assert commands[0].finished

    class FakeQAFail:
        def __init__(self, ai_client):
            pass

        async def ask(self, question, **kwargs):
            raise AIError("bad")

    commands = setup_fake_commands(monkeypatch, qa_handler)
    monkeypatch.setattr(qa_handler, "check_group", allow_group)
    monkeypatch.setattr(qa_handler, "QASystem", FakeQAFail)
    qa_handler.init(object())

    await commands[0].handlers[0](object(), Message("hi"))
    assert commands[0].finished
