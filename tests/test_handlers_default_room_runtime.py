import pytest

from nonebot.adapters.onebot.v11 import Message

from nonebot_plugin_dst_management.handlers import default_room as default_room_handler


class Finished(Exception):
    pass


class FakeCommand:
    def __init__(self):
        self.finished = []

    async def finish(self, message):
        self.finished.append(message)
        raise Finished()


class FakeEvent:
    def __init__(self, user_id: int = 123):
        self.user_id = user_id


@pytest.mark.asyncio
async def test_default_room_set_paths(monkeypatch: pytest.MonkeyPatch) -> None:
    cmd = FakeCommand()
    monkeypatch.setattr(default_room_handler, "cmd_set", cmd)

    storage: dict[str, int] = {}

    async def fake_set_user_default_room(qq_id: str, room_id: int) -> None:
        storage[qq_id] = room_id

    monkeypatch.setattr(default_room_handler, "set_user_default_room", fake_set_user_default_room)

    async def deny_group(event):
        return False

    monkeypatch.setattr(default_room_handler, "check_group", deny_group)
    with pytest.raises(Finished):
        await default_room_handler.handle_set_default(object(), FakeEvent(), Message("1"))
    assert "权限不足" in str(cmd.finished[-1])
    assert not storage

    async def allow_group(event):
        return True

    monkeypatch.setattr(default_room_handler, "check_group", allow_group)
    with pytest.raises(Finished):
        await default_room_handler.handle_set_default(object(), FakeEvent(), Message(""))
    assert "用法" in str(cmd.finished[-1])

    with pytest.raises(Finished):
        await default_room_handler.handle_set_default(object(), FakeEvent(), Message("abc"))
    assert "正整数" in str(cmd.finished[-1])

    class ApiClientMissing:
        async def get_room_info(self, room_id: int):
            return {"success": False}

    default_room_handler.init(ApiClientMissing())
    with pytest.raises(Finished):
        await default_room_handler.handle_set_default(object(), FakeEvent(), Message("2"))
    assert "不存在" in str(cmd.finished[-1])

    class ApiClientBoom:
        async def get_room_info(self, room_id: int):
            raise RuntimeError("boom")

    default_room_handler.init(ApiClientBoom())
    with pytest.raises(Finished):
        await default_room_handler.handle_set_default(object(), FakeEvent(), Message("2"))
    assert "验证房间失败" in str(cmd.finished[-1])

    class ApiClientOK:
        async def get_room_info(self, room_id: int):
            return {"success": True, "data": {"id": room_id}}

    default_room_handler.init(ApiClientOK())
    with pytest.raises(Finished):
        await default_room_handler.handle_set_default(object(), FakeEvent(999), Message("5"))
    assert storage == {"999": 5}
    assert "已设置默认房间为 5" in str(cmd.finished[-1])


@pytest.mark.asyncio
async def test_default_room_clear_and_show_paths(monkeypatch: pytest.MonkeyPatch) -> None:
    cmd_clear = FakeCommand()
    cmd_show = FakeCommand()
    monkeypatch.setattr(default_room_handler, "cmd_clear", cmd_clear)
    monkeypatch.setattr(default_room_handler, "cmd_show", cmd_show)

    storage: dict[str, int] = {}

    async def fake_get_user_default_room(qq_id: str):
        return storage.get(qq_id)

    async def fake_clear_user_default_room(qq_id: str) -> None:
        storage.pop(qq_id, None)

    monkeypatch.setattr(default_room_handler, "get_user_default_room", fake_get_user_default_room)
    monkeypatch.setattr(default_room_handler, "clear_user_default_room", fake_clear_user_default_room)

    async def deny_group(event):
        return False

    monkeypatch.setattr(default_room_handler, "check_group", deny_group)
    with pytest.raises(Finished):
        await default_room_handler.handle_clear_default(object(), FakeEvent())
    assert "权限不足" in str(cmd_clear.finished[-1])

    with pytest.raises(Finished):
        await default_room_handler.handle_show_default(object(), FakeEvent())
    assert "权限不足" in str(cmd_show.finished[-1])

    async def allow_group(event):
        return True

    monkeypatch.setattr(default_room_handler, "check_group", allow_group)

    # clear without default
    with pytest.raises(Finished):
        await default_room_handler.handle_clear_default(object(), FakeEvent(1))
    assert "未设置默认房间" in str(cmd_clear.finished[-1])

    # show without default
    with pytest.raises(Finished):
        await default_room_handler.handle_show_default(object(), FakeEvent(1))
    assert "未设置默认房间" in str(cmd_show.finished[-1])

    # clear with default
    storage["2"] = 7
    with pytest.raises(Finished):
        await default_room_handler.handle_clear_default(object(), FakeEvent(2))
    assert "已清除默认房间" in str(cmd_clear.finished[-1])
    assert "原房间：7" in str(cmd_clear.finished[-1])
    assert "2" not in storage

    # show with default
    storage["3"] = 9
    with pytest.raises(Finished):
        await default_room_handler.handle_show_default(object(), FakeEvent(3))
    assert "当前默认房间：9" in str(cmd_show.finished[-1])

