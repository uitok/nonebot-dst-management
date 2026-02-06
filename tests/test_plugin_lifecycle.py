import pytest


@pytest.mark.asyncio
async def test_plugin_init_and_close(monkeypatch: pytest.MonkeyPatch) -> None:
    import nonebot_plugin_dst_management as plugin

    # Ensure a clean lifecycle for this test
    monkeypatch.setattr(plugin, "_api_client", None)
    monkeypatch.setattr(plugin, "_ai_client", None)

    class FakeConfig:
        dst_api_url = "http://example.invalid"
        dst_api_token = "token"
        dst_timeout = 5

        def get_ai_config(self):
            return {"enabled": False}

    monkeypatch.setattr(plugin, "get_dst_config", lambda: FakeConfig())

    created: dict[str, object] = {}

    class FakeDSTApiClient:
        def __init__(self, base_url: str, token: str, timeout: int) -> None:
            created["api_args"] = (base_url, token, timeout)
            self.closed = False

        async def close(self) -> None:
            self.closed = True

    class FakeAIClient:
        def __init__(self, ai_config) -> None:
            created["ai_config"] = ai_config
            self.closed = False

        async def close(self) -> None:
            self.closed = True

    monkeypatch.setattr(plugin, "DSTApiClient", FakeDSTApiClient)
    monkeypatch.setattr(plugin, "AIClient", FakeAIClient)

    import nonebot_plugin_dst_management.services.monitors.sign_monitor as sign_monitor

    monitor_calls: dict[str, object] = {}
    monkeypatch.setattr(sign_monitor, "init_sign_monitor", lambda api_client: monitor_calls.setdefault("api", api_client))

    import nonebot_plugin_dst_management.handlers as handlers

    init_calls: list[tuple[str, tuple[object, ...]]] = []

    def make_stub(name: str):
        def _stub(*args, **kwargs):
            init_calls.append((name, args))

        return _stub

    for name in [
        "room",
        "player",
        "backup",
        "mod",
        "console",
        "archive",
        "ai_analyze",
        "ai_recommend",
        "ai_mod_parse",
        "ai_mod_apply",
        "ai_archive",
        "ai_qa",
        "default_room",
        "sign",
    ]:
        monkeypatch.setattr(getattr(handlers, name), "init", make_stub(name))

    await plugin.init_client()

    assert created["api_args"] == ("http://example.invalid", "token", 5)
    assert created["ai_config"] == {"enabled": False}

    api_client = plugin.get_api_client()
    assert isinstance(api_client, FakeDSTApiClient)
    assert monitor_calls["api"] is api_client

    called_names = {name for name, _ in init_calls}
    assert "room" in called_names
    assert "player" in called_names
    assert "mod" in called_names
    assert "default_room" in called_names
    assert "sign" in called_names

    await plugin.close_client()
    assert plugin._api_client.closed is True
    assert plugin._ai_client.closed is True

