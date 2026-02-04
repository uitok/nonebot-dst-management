import pytest

from nonebot_plugin_dst_management.ai import session as session_module
from nonebot_plugin_dst_management.ai.session import SessionManager


def test_session_expiry_resets_history(monkeypatch: pytest.MonkeyPatch) -> None:
    clock = {"value": 0.0}

    def fake_monotonic() -> float:
        return clock["value"]

    monkeypatch.setattr(session_module.time, "monotonic", fake_monotonic)

    manager = SessionManager(max_rounds=2, ttl_seconds=10)
    manager.append_turn("s1", "q1", "a1")
    assert manager.list_history("s1")

    clock["value"] = 11.0
    assert manager.list_history("s1") == []

    manager.append_turn("s1", "q2", "a2")
    history = manager.list_history("s1")
    assert len(history) == 2
