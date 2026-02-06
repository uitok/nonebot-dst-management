"""
签到业务逻辑服务

负责绑定验证、签到校验、奖励计算与控制台命令生成。
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta
from typing import Any, Optional

from loguru import logger

from ..client.api_client import DSTApiClient
from ..database import (
    SignUser,
    create_sign_record,
    create_user_binding,
    delete_user_binding,
    get_sign_record,
    get_user_binding,
    update_user_sign_stats,
)
from ..helpers.commands import escape_console_string
from ..services.reward_service import RewardResult, RewardService, format_reward_items


@dataclass(frozen=True)
class SignResult:
    success: bool
    message: str
    reward: Optional[RewardResult] = None
    user: Optional[SignUser] = None


class SignService:
    """签到业务服务。"""

    def __init__(self, api_client: DSTApiClient, reward_service: Optional[RewardService] = None) -> None:
        self.api_client = api_client
        self.reward_service = reward_service or RewardService()

    async def bind_user(
        self,
        qq_id: str,
        ku_id: str,
        room_id: int,
        player_name: Optional[str] = None,
    ) -> SignResult:
        if not self._is_valid_ku_id(ku_id):
            return SignResult(False, "KU_ID 格式不正确，应以 KU_ 开头")

        existing = await get_user_binding(qq_id, room_id)
        if existing:
            return SignResult(False, "你已经在该房间绑定过 KU_ID 了")

        binding_id = await create_user_binding(qq_id, ku_id, room_id, player_name)
        if not binding_id:
            return SignResult(False, "绑定失败，可能已存在绑定记录")

        user = await get_user_binding(qq_id, room_id)
        return SignResult(True, "绑定成功", user=user)

    async def unbind_user(self, qq_id: str, room_id: int) -> SignResult:
        existing = await get_user_binding(qq_id, room_id)
        if not existing:
            return SignResult(False, "该房间尚未绑定 KU_ID")

        deleted = await delete_user_binding(qq_id, room_id)
        if deleted <= 0:
            return SignResult(False, "解绑失败，请稍后再试")

        return SignResult(True, "解绑成功", user=existing)

    async def sign_in(
        self,
        qq_id: str,
        room_id: int,
        sign_date: Optional[date] = None,
        is_full_moon: bool = False,
    ) -> SignResult:
        user = await get_user_binding(qq_id, room_id)
        if not user:
            return SignResult(False, "请先使用 /dst sign bind <KU_ID> 绑定账号")

        today = sign_date or date.today()

        record = await get_sign_record(qq_id, today, room_id=room_id)
        if record:
            return SignResult(False, "今天已经签到过了哦")

        continuous_days = self._calculate_continuous_days(user, today)
        is_first_sign = user.sign_count <= 0

        reward = await self.reward_service.calculate_reward(
            continuous_days=continuous_days,
            is_first_sign=is_first_sign,
            is_full_moon=is_full_moon,
        )

        reward_status = 1
        pending_reason: Optional[str] = None
        try:
            online_result = await self.api_client.get_room_players(room_id)
        except Exception as exc:
            online_result = {"success": False, "error": str(exc)}
            logger.warning("获取房间玩家列表失败，room_id={} error={}", room_id, exc)

        if not online_result.get("success"):
            reward_status = 0
            pending_reason = online_result.get("error") or "获取在线玩家失败"
        else:
            players = online_result.get("data") or []
            online_ids = {player.get("uid") for player in players if player.get("uid")}
            if user.ku_id not in online_ids:
                reward_status = 0
                pending_reason = "玩家当前不在线"
                logger.info("玩家不在线，签到奖励改为待发放，qq_id={} ku_id={}", qq_id, user.ku_id)
        if reward_status == 1:
            command = self.generate_give_command(user.ku_id, reward.items)
            try:
                result = await self.api_client.execute_console_command(room_id, None, command)
            except Exception as exc:
                result = {"success": False, "error": str(exc)}
            if not result or not result.get("success"):
                reward_status = 0
                pending_reason = result.get("error") if isinstance(result, dict) else "未知错误"
                logger.warning(
                    "签到奖励发放失败，qq_id={} ku_id={} room_id={} error={}",
                    qq_id,
                    user.ku_id,
                    room_id,
                    pending_reason,
                )
            else:
                logger.info("签到奖励发放成功，qq_id={} ku_id={} room_id={}", qq_id, user.ku_id, room_id)

        sign_count = user.sign_count + 1
        total_points = user.total_points + reward.bonus_points
        await update_user_sign_stats(
            qq_id=qq_id,
            room_id=room_id,
            last_sign_time=today,
            sign_count=sign_count,
            continuous_days=continuous_days,
            level=reward.level,
            total_points=total_points,
        )
        await create_sign_record(
            qq_id=qq_id,
            room_id=room_id,
            sign_date=today,
            reward_level=reward.level,
            reward_items=reward.items,
            status=reward_status,
        )

        message = self.format_sign_message(reward, sign_count, continuous_days)
        if reward_status == 0:
            note = "奖励将在你上线后自动发放"
            if pending_reason:
                note = f"奖励未即时发放（{pending_reason}），上线后将自动发放"
            message = f"{message}\n{note}"
        return SignResult(True, message, reward=reward, user=user)

    @staticmethod
    def _is_valid_ku_id(ku_id: str) -> bool:
        if not ku_id:
            return False
        return ku_id.startswith("KU_") and len(ku_id) > 3

    @staticmethod
    def _calculate_continuous_days(user: SignUser, today: date) -> int:
        if user.last_sign_time is None:
            return 1
        if user.last_sign_time == today:
            return user.continuous_days
        if user.last_sign_time == today - timedelta(days=1):
            return user.continuous_days + 1
        return 1

    @staticmethod
    def generate_give_command(ku_id: str, rewards: list[dict[str, Any]]) -> str:
        """生成给予物品的控制台命令。"""
        safe_ku_id = escape_console_string(ku_id)
        lines = [
            "for i, v in ipairs(AllPlayers) do",
            f"    if v.userid == \"{safe_ku_id}\" then",
        ]
        for reward in rewards:
            prefab = reward.get("prefab")
            amount = reward.get("amount")
            if prefab is None or amount is None:
                continue
            safe_prefab = escape_console_string(str(prefab))
            try:
                amount_value = int(amount)
            except (TypeError, ValueError):
                continue
            if amount_value <= 0:
                continue
            lines.append(f"        c_give(\"{safe_prefab}\", {amount_value})")
        lines.append("    end")
        lines.append("end")
        return "\n".join(lines)

    @staticmethod
    def format_sign_message(reward: RewardResult, sign_count: int, continuous_days: int) -> str:
        items_text = format_reward_items(reward.items)
        desc_text = "，".join(reward.descriptions) if reward.descriptions else "基础签到奖励"
        return (
            f"签到成功！本次获得：{items_text}\n"
            f"连续签到：{continuous_days}天 | 累计签到：{sign_count}天\n"
            f"奖励说明：{desc_text}"
        )


__all__ = ["SignService", "SignResult"]
