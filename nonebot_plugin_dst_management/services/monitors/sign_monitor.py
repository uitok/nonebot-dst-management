"""
签到异步发放触发式检查器。

在玩家执行命令时触发检查，不使用后台轮询。
"""

from __future__ import annotations

from typing import Optional

from loguru import logger

from ...client.api_client import DSTApiClient
from ...database import PendingSignRecord, list_pending_sign_records, update_sign_record_status
from ..sign_service import SignService


class SignMonitor:
    """签到奖励异步发放监视器（触发式）。"""

    def __init__(self, api_client: DSTApiClient) -> None:
        self.api_client = api_client

    async def check_room_pending_rewards(self, room_id: int) -> None:
        """
        检查指定房间的待发放奖励。

        通常在获取该房间在线玩家列表后调用，复用 API 调用结果。
        """
        pending_records = await list_pending_sign_records()
        if not pending_records:
            return

        # 筛选出该房间的待发放记录
        room_records = [r for r in pending_records if r.room_id == room_id]
        if not room_records:
            return

        # 获取在线玩家（如果调用方已经获取过，可以考虑传入缓存）
        online_result = await self.api_client.get_online_players(room_id)
        if not online_result.get("success"):
            logger.warning(
                "获取在线玩家失败，room_id={} error={}",
                room_id,
                online_result.get("error"),
            )
            return

        players = online_result.get("data") or []
        online_ids = {player.get("uid") for player in players if player.get("uid")}
        if not online_ids:
            return

        # 匹配并发放奖励
        for record in room_records:
            if record.ku_id not in online_ids:
                continue

            rewards = record.reward_items or []
            command = SignService.generate_give_command(record.ku_id, rewards)
            result = await self.api_client.execute_console_command(room_id, None, command)

            if result and result.get("success"):
                await update_sign_record_status(record.id, 1)
                logger.info(
                    "成功发放签到奖励，record_id={} qq_id={} ku_id={} room_id={}",
                    record.id,
                    record.qq_id,
                    record.ku_id,
                    room_id,
                )
            else:
                logger.warning(
                    "发放签到奖励失败，record_id={} room_id={} error={}",
                    record.id,
                    room_id,
                    result.get("error") if isinstance(result, dict) else "未知错误",
                )

    async def check_user_pending_rewards(self, qq_id: str, ku_id: str, room_id: int) -> bool:
        """
        检查指定用户的待发放奖励。

        Args:
            qq_id: QQ号
            ku_id: DST玩家ID
            room_id: 房间ID

        Returns:
            是否成功发放了奖励
        """
        pending_records = await list_pending_sign_records()
        user_records = [
            r
            for r in pending_records
            if r.qq_id == qq_id and r.ku_id == ku_id and r.room_id == room_id
        ]
        if not user_records:
            return False

        # 检查玩家是否在线
        online_result = await self.api_client.get_online_players(room_id)
        if not online_result.get("success"):
            return False

        players = online_result.get("data") or []
        online_ids = {player.get("uid") for player in players if player.get("uid")}
        if ku_id not in online_ids:
            return False

        # 发放所有待发放奖励
        success_count = 0
        for record in user_records:
            rewards = record.reward_items or []
            command = SignService.generate_give_command(ku_id, rewards)
            result = await self.api_client.execute_console_command(room_id, None, command)

            if result and result.get("success"):
                await update_sign_record_status(record.id, 1)
                success_count += 1
                logger.info(
                    "成功补发签到奖励，record_id={} qq_id={} ku_id={} room_id={}",
                    record.id,
                    qq_id,
                    ku_id,
                    room_id,
                )
            else:
                logger.warning(
                    "补发签到奖励失败，record_id={} room_id={} error={}",
                    record.id,
                    room_id,
                    result.get("error") if isinstance(result, dict) else "未知错误",
                )

        return success_count > 0


# 全局单例（用于命令触发）
_monitor: Optional[SignMonitor] = None


def get_sign_monitor() -> Optional[SignMonitor]:
    """获取签到监视器实例。"""
    return _monitor


def init_sign_monitor(api_client: DSTApiClient) -> SignMonitor:
    """初始化签到监视器（不需要启动后台任务）。"""
    global _monitor
    if _monitor is None:
        _monitor = SignMonitor(api_client)
        logger.info("签到触发式发放监视器已初始化")
    return _monitor


__all__ = ["SignMonitor", "get_sign_monitor", "init_sign_monitor"]
