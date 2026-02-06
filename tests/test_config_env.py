import os

import pytest

from nonebot_plugin_dst_management import config as dst_config
from nonebot_plugin_dst_management.ai.config import AIConfig


def test_parse_bool():
    assert dst_config._parse_bool("true") is True
    assert dst_config._parse_bool("1") is True
    assert dst_config._parse_bool("false") is False
    assert dst_config._parse_bool("0") is False
    with pytest.raises(ValueError):
        dst_config._parse_bool("maybe")


def test_parse_int_list():
    assert dst_config._parse_int_list("1,2, 3") == [1, 2, 3]
    assert dst_config._parse_int_list("") == []


def test_apply_env_overrides(monkeypatch):
    monkeypatch.setenv("DST_API_URL", "http://example.com")
    monkeypatch.setenv("DST_API_TOKEN", "token")
    monkeypatch.setenv("DST_TIMEOUT", "15")
    monkeypatch.setenv("DST_ADMIN_USERS", "1,2")
    monkeypatch.setenv("DST_ADMIN_GROUPS", "10,20")
    monkeypatch.setenv("DST_ENABLE_AI", "true")
    monkeypatch.setenv("DST_AI_PROVIDER", "mock")
    monkeypatch.setenv("DST_AI_API_KEY", "key")
    monkeypatch.setenv("DST_AI_MODEL", "gpt-4")
    monkeypatch.setenv("DST_AI_BASE_URL", "http://ai.example.com")

    monkeypatch.setenv("AI_ENABLED", "false")
    monkeypatch.setenv("AI_PROVIDER", "openai")
    monkeypatch.setenv("AI_API_KEY", "key2")
    monkeypatch.setenv("AI_API_URL", "http://ai2.example.com")
    monkeypatch.setenv("AI_MODEL", "gpt-4o-mini")
    monkeypatch.setenv("AI_TEMPERATURE", "0.9")
    monkeypatch.setenv("AI_MAX_TOKENS", "1000")
    monkeypatch.setenv("AI_TIMEOUT", "20")
    monkeypatch.setenv("AI_CACHE_TTL", "3600")
    monkeypatch.setenv("AI_RETRIES", "2")
    monkeypatch.setenv("AI_RETRY_BACKOFF", "0.2")
    monkeypatch.setenv("AI_RETRY_MAX_BACKOFF", "1.0")

    cfg = dst_config.DSTConfig()
    updated = dst_config._apply_env_overrides(cfg)

    assert updated.dst_api_url == "http://example.com"
    assert updated.dst_api_token == "token"
    assert updated.dst_timeout == 15
    assert updated.dst_admin_users == [1, 2]
    assert updated.dst_admin_groups == [10, 20]
    assert updated.dst_enable_ai is True
    assert updated.dst_ai_provider == "mock"
    assert updated.dst_ai_api_key == "key"
    assert updated.dst_ai_model == "gpt-4"
    assert updated.dst_ai_base_url == "http://ai.example.com"

    assert isinstance(updated.ai, AIConfig)
    assert updated.ai.enabled is False
    assert updated.ai.provider == "openai"
    assert updated.ai.api_key == "key2"
    assert updated.ai.api_url == "http://ai2.example.com"
    assert updated.ai.model == "gpt-4o-mini"
    assert updated.ai.temperature == 0.9
    assert updated.ai.max_tokens == 1000
    assert updated.ai.timeout == 20
    assert updated.ai.cache_ttl == 3600
    assert updated.ai.retries == 2
    assert updated.ai.retry_backoff == 0.2
    assert updated.ai.retry_max_backoff == 1.0


def test_load_dotenv(tmp_path, monkeypatch):
    env_file = tmp_path / "test.env"
    env_file.write_text("TEST_KEY=VALUE\n#comment\nexport OTHER=123\nEMPTY=\n", encoding="utf-8")

    monkeypatch.delenv("TEST_KEY", raising=False)
    monkeypatch.delenv("OTHER", raising=False)

    dst_config._load_dotenv(str(env_file))

    assert os.environ.get("TEST_KEY") == "VALUE"
    assert os.environ.get("OTHER") == "123"


def test_get_ai_config_merges_legacy_fields():
    cfg = dst_config.DSTConfig(
        dst_enable_ai=True,
        dst_ai_provider="mock",
        dst_ai_api_key="secret",
        dst_ai_model="gpt-4",
        dst_ai_base_url="http://ai.example.com",
    )
    merged = cfg.get_ai_config()

    assert merged.enabled is True
    assert merged.provider == "mock"
    assert merged.api_key == "secret"
    assert merged.model == "gpt-4"
    assert merged.api_url == "http://ai.example.com"


def test_get_dst_config_defaults():
    dst_config._dst_config = None
    loaded = dst_config.get_dst_config()
    assert loaded.dst_api_url == "http://localhost:8080"
