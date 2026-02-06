import pytest

from nonebot_plugin_dst_management.ai.analyzer import ServerConfigAnalyzer
from nonebot_plugin_dst_management.ai.base import AITransientError
from nonebot_plugin_dst_management.ai.client import AIClient, MockProvider
from nonebot_plugin_dst_management.ai.config import AIConfig


class DummyApiClient:
    async def get_room_info(self, room_id: int):
        return {
            "success": True,
            "data": {
                "id": room_id,
                "gameName": "测试房间",
                "gameMode": "生存",
                "maxPlayer": 8,
                "pvp": False,
                "password": "",
                "description": "测试描述",
            },
        }

    async def get_room_mods(self, room_id: int):
        return {
            "success": True,
            "data": {
                "enabled": ["workshop-1", "workshop-2"],
                "disabled": ["workshop-3"],
                "duplicates": [],
                "raw": "",
            },
        }

    async def get_room_stats(self, room_id: int):
        return {
            "success": True,
            "data": {
                "online_players": 2,
                "players": [],
            },
        }


@pytest.mark.asyncio
async def test_analyze_server_returns_ai_response() -> None:
    config = AIConfig(enabled=True, provider="mock")
    provider = MockProvider(config, response="AI REPORT")
    ai_client = AIClient(config, provider=provider)

    analyzer = ServerConfigAnalyzer(DummyApiClient(), ai_client)
    report = await analyzer.analyze_server(1)

    assert report == "AI REPORT"


@pytest.mark.asyncio
async def test_analyze_server_fallback_on_ai_error() -> None:
    config = AIConfig(enabled=True, provider="mock")
    provider = MockProvider(config, error=AITransientError("down"))
    ai_client = AIClient(config, provider=provider)

    analyzer = ServerConfigAnalyzer(DummyApiClient(), ai_client)
    report = await analyzer.analyze_server(1)

    assert "DST 服务器分析报告" in report
    assert "AI 分析失败" in report


@pytest.mark.asyncio
async def test_analyze_server_uses_cache() -> None:
    calls = 0

    class CountingProvider(MockProvider):
        async def chat(self, messages, system_prompt: str = "", **kwargs):  # type: ignore[override]
            nonlocal calls
            calls += 1
            return await super().chat(messages, system_prompt=system_prompt, **kwargs)

    config = AIConfig(enabled=True, provider="mock", cache_ttl=60)
    provider = CountingProvider(config, response="cached report")
    ai_client = AIClient(config, provider=provider)

    analyzer = ServerConfigAnalyzer(DummyApiClient(), ai_client)
    report1 = await analyzer.analyze_server(1)
    report2 = await analyzer.analyze_server(1)

    assert report1 == "cached report"
    assert report2 == "cached report"
    assert calls == 1
