from __future__ import annotations

import pytest

from nonebot_plugin_dst_management.services.reward_service import (
    RewardService,
    RewardTier,
    format_reward_items,
    merge_reward_items,
)


@pytest.mark.asyncio
async def test_calculate_reward_with_continuous_and_specials():
    tiers = [
        RewardTier(
            level=1,
            continuous_days=0,
            reward_items=[{"prefab": "twigs", "amount": 2}],
            bonus_points=1,
            description="基础奖励",
        ),
        RewardTier(
            level=2,
            continuous_days=5,
            reward_items=[{"prefab": "rope", "amount": 1}],
            bonus_points=3,
            description="连续5天奖励",
        ),
    ]

    service = RewardService(tiers=tiers)
    result = await service.calculate_reward(
        continuous_days=5,
        is_first_sign=True,
        is_full_moon=True,
    )

    assert result.level == 2
    assert result.bonus_points == 3
    assert result.is_first_sign is True
    assert result.is_full_moon is True

    prefabs = {item["prefab"]: item["amount"] for item in result.items}
    assert prefabs.get("rope") == 1
    # 连续3天额外奖励
    assert prefabs.get("goldnugget") == 20
    # 首次签到与满月奖励
    assert prefabs.get("hammer") == 1
    assert prefabs.get("blueprint") == 3


def test_merge_reward_items():
    merged = merge_reward_items(
        [
            {"prefab": "goldnugget", "amount": 10},
            {"prefab": "goldnugget", "amount": "5"},
            {"prefab": "cutgrass", "amount": 3},
            {"prefab": "", "amount": 1},
            {"prefab": "invalid", "amount": "x"},
            {"prefab": "twigs", "amount": -1},
        ]
    )
    assert merged == [
        {"prefab": "cutgrass", "amount": 3},
        {"prefab": "goldnugget", "amount": 15},
    ]


def test_format_reward_items():
    items = [
        {"prefab": "goldnugget", "amount": 10},
        {"prefab": "cutgrass", "amount": 3},
        {"prefab": None, "amount": 1},
        {"prefab": "twigs", "amount": None},
    ]
    assert format_reward_items(items) == "goldnuggetx10、cutgrassx3"
