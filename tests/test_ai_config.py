import pytest

from nonebot_plugin_dst_management.ai.config import AIConfig
from nonebot_plugin_dst_management.config import DSTConfig, _apply_env_overrides


def test_api_url_validation() -> None:
    config = AIConfig(api_url="https://example.com/v1", enabled=True)
    assert config.api_url == "https://example.com/v1"

    with pytest.raises(ValueError):
        AIConfig(api_url="not-a-url")


def test_get_ai_config_prefers_new_config() -> None:
    cfg = DSTConfig(ai=AIConfig(provider="claude", model="claude-3"))
    ai_cfg = cfg.get_ai_config()
    assert ai_cfg.provider == "claude"
    assert ai_cfg.model == "claude-3"


def test_get_ai_config_legacy_override() -> None:
    cfg = DSTConfig(dst_ai_provider="ollama", dst_enable_ai=True)
    ai_cfg = cfg.get_ai_config()
    assert ai_cfg.provider == "ollama"
    assert ai_cfg.enabled is True


def test_env_overrides_ai(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("AI_PROVIDER", "ollama")
    monkeypatch.setenv("AI_ENABLED", "true")
    base = DSTConfig()
    updated = _apply_env_overrides(base)
    assert updated.ai.provider == "ollama"
    assert updated.ai.enabled is True
