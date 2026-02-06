"""
签到奖励计算服务

提供等级奖励、连续签到奖励与特殊奖励的计算。
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable, Optional

from ..database import list_sign_rewards


@dataclass(frozen=True)
class RewardTier:
    level: int
    continuous_days: int
    reward_items: list[dict[str, Any]]
    bonus_points: int = 0
    description: Optional[str] = None


@dataclass(frozen=True)
class RewardResult:
    level: int
    continuous_days: int
    items: list[dict[str, Any]]
    bonus_points: int
    descriptions: list[str]
    is_first_sign: bool
    is_full_moon: bool


DEFAULT_LEVEL_REWARDS: list[RewardTier] = [
    RewardTier(
        level=1,
        continuous_days=0,
        reward_items=[
            {"prefab": "goldnugget", "amount": 10},
            {"prefab": "cookedmeat", "amount": 5},
        ],
        bonus_points=0,
        description="新用户奖励",
    ),
    RewardTier(
        level=2,
        continuous_days=3,
        reward_items=[
            {"prefab": "goldnugget", "amount": 20},
            {"prefab": "cookedmeat", "amount": 10},
            {"prefab": "cutgrass", "amount": 20},
        ],
        bonus_points=0,
        description="连续3天奖励",
    ),
    RewardTier(
        level=3,
        continuous_days=7,
        reward_items=[
            {"prefab": "goldnugget", "amount": 30},
            {"prefab": "nightmare_timepiece", "amount": 2},
            {"prefab": "gears", "amount": 1},
        ],
        bonus_points=0,
        description="连续7天奖励",
    ),
    RewardTier(
        level=4,
        continuous_days=14,
        reward_items=[
            {"prefab": "goldnugget", "amount": 50},
            {"prefab": "nightmare_timepiece", "amount": 5},
            {"prefab": "redgem", "amount": 1},
        ],
        bonus_points=0,
        description="连续14天奖励",
    ),
    RewardTier(
        level=5,
        continuous_days=30,
        reward_items=[
            {"prefab": "goldnugget", "amount": 100},
            {"prefab": "nightmare_timepiece", "amount": 10},
            {"prefab": "redgem", "amount": 2},
        ],
        bonus_points=0,
        description="连续30天奖励",
    ),
]

CONTINUOUS_BONUS: dict[int, list[dict[str, Any]]] = {
    3: [{"prefab": "goldnugget", "amount": 20}],
    7: [{"prefab": "nightmare_timepiece", "amount": 1}],
    30: [{"prefab": "redgem", "amount": 1}],
}

SPECIAL_REWARDS: dict[str, list[dict[str, Any]]] = {
    "first_sign": [{"prefab": "hammer", "amount": 1}],
    "full_moon": [{"prefab": "blueprint", "amount": 3}],
}


def merge_reward_items(items: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
    """合并奖励列表，按 prefab 聚合数量。"""
    merged: dict[str, int] = {}
    for item in items:
        prefab = str(item.get("prefab") or "").strip()
        if not prefab:
            continue
        try:
            amount = int(item.get("amount", 0))
        except (TypeError, ValueError):
            continue
        if amount <= 0:
            continue
        merged[prefab] = merged.get(prefab, 0) + amount
    return [{"prefab": prefab, "amount": merged[prefab]} for prefab in sorted(merged)]


class RewardService:
    """奖励计算服务。"""

    def __init__(self, tiers: Optional[list[RewardTier]] = None) -> None:
        self._tiers_override = tiers

    async def load_reward_tiers(self) -> list[RewardTier]:
        if self._tiers_override is not None:
            return self._tiers_override
        rewards = await list_sign_rewards()
        if not rewards:
            return DEFAULT_LEVEL_REWARDS
        tiers: list[RewardTier] = []
        for reward in rewards:
            tiers.append(
                RewardTier(
                    level=reward.level,
                    continuous_days=reward.continuous_days,
                    reward_items=reward.reward_items,
                    bonus_points=reward.bonus_points,
                    description=reward.description,
                )
            )
        return tiers

    async def calculate_reward(
        self,
        continuous_days: int,
        is_first_sign: bool = False,
        is_full_moon: bool = False,
    ) -> RewardResult:
        tiers = await self.load_reward_tiers()
        return self._calculate_from_tiers(
            tiers,
            continuous_days=continuous_days,
            is_first_sign=is_first_sign,
            is_full_moon=is_full_moon,
        )

    def _calculate_from_tiers(
        self,
        tiers: list[RewardTier],
        continuous_days: int,
        is_first_sign: bool,
        is_full_moon: bool,
    ) -> RewardResult:
        continuous_days = max(0, int(continuous_days))
        tiers_sorted = sorted(tiers, key=lambda item: item.continuous_days)
        selected = tiers_sorted[0] if tiers_sorted else DEFAULT_LEVEL_REWARDS[0]
        for tier in tiers_sorted:
            if continuous_days >= tier.continuous_days:
                selected = tier
        items: list[dict[str, Any]] = list(selected.reward_items)
        descriptions: list[str] = []
        if selected.description:
            descriptions.append(selected.description)

        bonus_points = selected.bonus_points

        for threshold in sorted(CONTINUOUS_BONUS):
            if continuous_days >= threshold:
                items.extend(CONTINUOUS_BONUS[threshold])
                descriptions.append(f"连续{threshold}天额外奖励")

        if is_first_sign:
            items.extend(SPECIAL_REWARDS["first_sign"])
            descriptions.append("首次签到奖励")

        if is_full_moon:
            items.extend(SPECIAL_REWARDS["full_moon"])
            descriptions.append("满月签到奖励")

        merged_items = merge_reward_items(items)
        return RewardResult(
            level=selected.level,
            continuous_days=continuous_days,
            items=merged_items,
            bonus_points=bonus_points,
            descriptions=descriptions,
            is_first_sign=is_first_sign,
            is_full_moon=is_full_moon,
        )


def format_reward_items(items: Iterable[dict[str, Any]]) -> str:
    """格式化奖励物品列表。"""
    parts = []
    for item in items:
        prefab = item.get("prefab")
        amount = item.get("amount")
        if prefab is None or amount is None:
            continue
        parts.append(f"{prefab}x{amount}")
    return "、".join(parts) if parts else "无"


__all__ = [
    "RewardTier",
    "RewardResult",
    "RewardService",
    "merge_reward_items",
    "format_reward_items",
]
