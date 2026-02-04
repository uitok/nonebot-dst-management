import pytest

from nonebot_plugin_dst_management.utils import permission


class DummyConfig:
    def __init__(self, admin_users=None, admin_groups=None):
        self.dst_admin_users = admin_users or []
        self.dst_admin_groups = admin_groups or []


class DummyEvent:
    def __init__(self, user_id):
        self.user_id = user_id


class DummyGroupEvent(DummyEvent):
    def __init__(self, user_id, group_id):
        super().__init__(user_id)
        self.group_id = group_id


@pytest.mark.asyncio
async def test_check_admin_with_admin_list(monkeypatch):
    monkeypatch.setattr(permission, "get_dst_config", lambda: DummyConfig(admin_users=[123]))

    async def fake_superuser(bot, event):
        return False

    monkeypatch.setattr(permission, "SUPERUSER", fake_superuser)

    assert await permission.check_admin(None, DummyEvent(123)) is True
    assert await permission.check_admin(None, DummyEvent(999)) is False


@pytest.mark.asyncio
async def test_check_admin_with_superuser(monkeypatch):
    monkeypatch.setattr(permission, "get_dst_config", lambda: DummyConfig(admin_users=[]))

    async def fake_superuser(bot, event):
        return True

    monkeypatch.setattr(permission, "SUPERUSER", fake_superuser)

    assert await permission.check_admin(None, DummyEvent(42)) is True


@pytest.mark.asyncio
async def test_check_group(monkeypatch):
    monkeypatch.setattr(permission, "GroupMessageEvent", DummyGroupEvent)
    monkeypatch.setattr(permission, "get_dst_config", lambda: DummyConfig(admin_groups=[100]))

    assert await permission.check_group(DummyEvent(1)) is False
    assert await permission.check_group(DummyGroupEvent(1, 100)) is True
    assert await permission.check_group(DummyGroupEvent(1, 200)) is False

    monkeypatch.setattr(permission, "get_dst_config", lambda: DummyConfig(admin_groups=[]))
    assert await permission.check_group(DummyGroupEvent(1, 200)) is True


@pytest.mark.asyncio
async def test_check_permission_levels(monkeypatch):
    monkeypatch.setattr(permission, "GroupMessageEvent", DummyGroupEvent)

    async def fake_superuser(bot, event):
        return event.user_id == 1

    monkeypatch.setattr(permission, "SUPERUSER", fake_superuser)
    monkeypatch.setattr(permission, "get_dst_config", lambda: DummyConfig(admin_users=[2], admin_groups=[10]))

    event = DummyGroupEvent(2, 10)
    assert await permission.check_permission(None, event, "user") is True
    assert await permission.check_permission(None, event, "admin") is True
    assert await permission.check_permission(None, event, "super") is False

    super_event = DummyGroupEvent(1, 10)
    assert await permission.check_permission(None, super_event, "super") is True
    assert await permission.check_permission(None, super_event, "unknown") is False
