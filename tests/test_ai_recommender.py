import json

import pytest

from nonebot_plugin_dst_management.ai.recommender import ModRecommender
from nonebot_plugin_dst_management.ai.client import AIClient, MockProvider
from nonebot_plugin_dst_management.ai.config import AIConfig
from nonebot_plugin_dst_management.ai.base import AITransientError


class DummyApiClient:
    async def get_room_mods(self, room_id: int):
        return {
            "success": True,
            "data": {
                "enabled": ["workshop-1000000001"],
                "disabled": [],
                "duplicates": [],
            },
        }


@pytest.mark.asyncio
async def test_recommend_mods_returns_ai_report() -> None:
    response = json.dumps(
        {
            "recommendations": [
                {
                    "mod_id": "workshop-1000000003",
                    "name": "Test Mod",
                    "score": 9.1,
                    "reason": "works",
                }
            ]
        }
    )
    config = AIConfig(enabled=True, provider="mock")
    provider = MockProvider(config, response=response)
    ai_client = AIClient(config, provider=provider)

    recommender = ModRecommender(DummyApiClient(), ai_client)
    result = await recommender.recommend_mods(2, None)

    assert "Test Mod" in result["report"]
    assert result["recommendations"][0]["mod_id"] == "workshop-1000000003"


@pytest.mark.asyncio
async def test_recommend_mods_fallback_on_ai_error() -> None:
    config = AIConfig(enabled=True, provider="mock")
    provider = MockProvider(config, error=AITransientError("down"))
    ai_client = AIClient(config, provider=provider)

    recommender = ModRecommender(DummyApiClient(), ai_client)
    result = await recommender.recommend_mods(2, "functional")

    assert "模组推荐报告" in result["report"]
    assert result["recommendations"]
