import pathlib

import pytest

from nonebot.adapters.onebot.v11 import Message

from nonebot_plugin_dst_management.handlers import archive as archive_handler
from nonebot_plugin_dst_management.services.archive_service import ArchiveInfo


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
async def test_archive_upload_and_replace(monkeypatch, tmp_path):
    commands = setup_fake_commands(monkeypatch, archive_handler)

    async def allow_group(event):
        return True

    async def allow_admin(bot, event):
        return True

    monkeypatch.setattr(archive_handler, "check_group", allow_group)
    monkeypatch.setattr(archive_handler, "check_admin", allow_admin)

    archive_path = tmp_path / "a.zip"
    archive_path.write_bytes(b"zip")

    class FakeArchiveService:
        def __init__(self):
            self.work_dir = tmp_path
            self.cleaned = []

        async def prepare_archive(self, source):
            return {"success": True, "path": str(archive_path), "cleanup": True}

        def validate_archive(self, archive_path):
            info = ArchiveInfo(
                worlds=["Master"],
                mod_count=1,
                game_mode="survival",
                cluster_name="Room",
                warnings=[],
            )
            return {"success": True, "info": info}

        def analyze_with_ai(self, info):
            return "AI summary"

        def cleanup_file(self, path):
            self.cleaned.append(path)

    monkeypatch.setattr(archive_handler, "ArchiveService", FakeArchiveService)

    class ApiClient:
        async def create_backup(self, room_id):
            return {"success": True}

        async def upload_archive(self, room_id, archive_path):
            return {"success": True}

        async def replace_archive(self, room_id, archive_path):
            return {"success": True}

    archive_handler.init(ApiClient())

    await commands[0].handlers[0](object(), object(), Message("1 /tmp/a.zip"))
    assert commands[0].sent
    assert commands[0].finished

    await commands[2].handlers[0](object(), object(), Message("1 /tmp/a.zip"))
    assert commands[2].sent
    assert commands[2].finished


@pytest.mark.asyncio
async def test_archive_download_and_validate(monkeypatch, tmp_path):
    commands = setup_fake_commands(monkeypatch, archive_handler)

    async def allow_group(event):
        return True

    async def allow_admin(bot, event):
        return True

    monkeypatch.setattr(archive_handler, "check_group", allow_group)
    monkeypatch.setattr(archive_handler, "check_admin", allow_admin)

    class FakeArchiveService:
        def __init__(self):
            self.work_dir = tmp_path
            self._prepared = tmp_path / "prepared.zip"
            self._prepared.write_bytes(b"zip")

        async def prepare_archive(self, source):
            return {"success": True, "path": str(self._prepared), "cleanup": True}

        def validate_archive(self, archive_path):
            return {
                "success": False,
                "errors": ["bad"],
                "warnings": ["warn"],
            }

        def cleanup_file(self, path):
            pass

    monkeypatch.setattr(archive_handler, "ArchiveService", FakeArchiveService)

    class ApiClient:
        async def download_archive(self, room_id):
            return {
                "success": True,
                "data": {"filename": "a.zip", "content": b"data"},
            }

    archive_handler.init(ApiClient())

    await commands[1].handlers[0](object(), Message("1"))
    assert commands[1].sent
    assert commands[1].finished

    await commands[3].handlers[0](object(), Message(""))
    assert commands[3].finished

    await commands[3].handlers[0](object(), Message("/tmp/a.zip"))
    assert commands[3].sent
    assert commands[3].finished


@pytest.mark.asyncio
async def test_archive_error_paths(monkeypatch):
    commands = setup_fake_commands(monkeypatch, archive_handler)

    async def allow_group(event):
        return True

    async def allow_admin(bot, event):
        return True

    monkeypatch.setattr(archive_handler, "check_group", allow_group)
    monkeypatch.setattr(archive_handler, "check_admin", allow_admin)

    class FakeArchiveService:
        def __init__(self):
            self.work_dir = pathlib.Path("/tmp")

        async def prepare_archive(self, source):
            return {"success": False, "error": "nope"}

    monkeypatch.setattr(archive_handler, "ArchiveService", FakeArchiveService)

    class ApiClient:
        async def create_backup(self, room_id):
            return {"success": False, "error": "no"}

    archive_handler.init(ApiClient())

    await commands[0].handlers[0](object(), object(), Message(""))
    assert commands[0].finished

    await commands[2].handlers[0](object(), object(), Message(""))
    assert commands[2].finished

    await commands[0].handlers[0](object(), object(), Message("1 /tmp/a.zip"))
    assert commands[0].sent
    assert commands[0].finished
