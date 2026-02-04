import io
import json
from zipfile import ZipFile

import pytest

from nonebot_plugin_dst_management.ai.mod_parser import ModConfigParser
from nonebot_plugin_dst_management.ai.client import AIClient, MockProvider
from nonebot_plugin_dst_management.ai.config import AIConfig
from nonebot_plugin_dst_management.ai.base import AITransientError


def _make_archive_bytes(content: str) -> bytes:
    buffer = io.BytesIO()
    with ZipFile(buffer, "w") as zf:
        zf.writestr("Master/modoverrides.lua", content)
    return buffer.getvalue()


class DummyApiClient:
    def __init__(self, content: bytes):
        self.content = content

    async def download_archive(self, room_id: int):
        return {"success": True, "data": {"content": self.content}}


@pytest.mark.asyncio
async def test_parse_mod_config_ai_response() -> None:
    mod_content = """
return {
  ["workshop-123"] = {
    enabled = true,
    configuration_options = {
      option_a = 1,
    },
  },
}
"""
    archive_bytes = _make_archive_bytes(mod_content)
    response = json.dumps(
        {
            "status": "valid",
            "warnings": [],
            "suggestions": ["ok"],
            "optimized_config": mod_content.strip(),
        }
    )

    config = AIConfig(enabled=True, provider="mock")
    provider = MockProvider(config, response=response)
    ai_client = AIClient(config, provider=provider)

    parser = ModConfigParser(DummyApiClient(archive_bytes), ai_client)
    result = await parser.parse_mod_config(2, "Master")

    assert "模组配置解析报告" in result["report"]
    assert "workshop-123" in result["report"]
    assert "optimized_config" in result


@pytest.mark.asyncio
async def test_parse_mod_config_fallback_on_error() -> None:
    mod_content = "return {}"
    archive_bytes = _make_archive_bytes(mod_content)

    config = AIConfig(enabled=True, provider="mock")
    provider = MockProvider(config, error=AITransientError("down"))
    ai_client = AIClient(config, provider=provider)

    parser = ModConfigParser(DummyApiClient(archive_bytes), ai_client)
    result = await parser.parse_mod_config(3, "Master")

    assert "模组配置解析报告" in result["report"]
    assert "AI 分析失败" in result["report"]


def test_parse_lua_config_nested_tables() -> None:
    mod_content = r"""
return {
  ["123"] = {
    enabled = false,
    configuration_options = {
      str = "line1\n\t\"quote\"",
      flag = true,
      list = { "x", 2, false },
      nested = { inner = { value = 1 } },
      none = nil,
      empty = {},
    },
  },
}
"""
    config = AIConfig(enabled=True, provider="mock")
    provider = MockProvider(config, response="{}")
    ai_client = AIClient(config, provider=provider)
    parser = ModConfigParser(DummyApiClient(b""), ai_client)

    parsed = parser._parse_lua_config(mod_content)
    assert parsed.mod_count == 1
    assert parsed.option_count == 6
    options = parsed.mods[0]["configuration_options"]
    assert options["flag"] is True
    assert options["list"] == ["x", 2, False]
