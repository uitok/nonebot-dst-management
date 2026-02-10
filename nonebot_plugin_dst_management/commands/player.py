"""
玩家管理命令 (Alconna 版本)

处理玩家相关的命令：players, kick
"""

from __future__ import annotations

from typing import Any, Optional

from arclet.alconna import (
    Alconna,
    Args,
    CommandMeta,
)
from nonebot import Bot
from nonebot.internal.adapter import Event

from ..client.api_client import DSTApiClient
from ..utils.permission import ADMIN_PERMISSION, USER_PERMISSION
from ..helpers.formatters import format_error, format_success, format_info
from ..helpers.commands import parse_room_id
from ..helpers.room_context import RoomSource, remember_room, resolve_room_id


# 全局 API 客户端，由 init 函数设置
_api_client: Optional[DSTApiClient] = None


def get_api_client() -> DSTApiClient:
    """获取 API 客户端"""
    if _api_client is None:
        raise RuntimeError("API 客户端未初始化，请先调用 init() 函数")
    return _api_client


# ========== 命令定义 ==========

players_command = Alconna(
    "dst players",
    Args["room_id", str, None],
    meta=CommandMeta(
        description="查看在线玩家",
        usage="/dst players [房间ID]",
        example="/dst players 1",
    ),
)


kick_command = Alconna(
    "dst kick",
    Args["room_id_or_kuid", str]["kuid", str, None],
    meta=CommandMeta(
        description="踢出玩家",
        usage="/dst kick [房间ID] <KU_ID>",
        example="/dst kick 1 KU_12345678 或 /dst kick KU_12345678",
    ),
)


# ========== 命令处理函数 ==========

async def handle_players(bot: Bot, event: Event, room_id: Optional[str] = None) -> str:
    """处理查看在线玩家命令"""
    if not await USER_PERMISSION(bot, event):
        return format_error("当前群组未授权使用此功能")

    client = get_api_client()

    # 解析房间 ID（支持会话锁定）
    resolved = await resolve_room_id(event, room_id if room_id else None)
    if resolved is None:
        if room_id:
            return format_error("请提供有效的房间ID：/dst players <房间ID>")
        else:
            return format_error("请提供房间ID：/dst players <房间ID>\n或先使用一次带房间ID的命令以锁定房间")

    actual_room_id = int(resolved.room_id)

    # 获取房间信息（用于房间名称）
    room_result = await client.get_room_info(actual_room_id)
    room_name = "未知房间"
    if room_result["success"]:
        room_name = room_result["data"].get("gameName", "未知房间")

    # 获取在线玩家
    result = await client.get_online_players(actual_room_id)

    if not result["success"]:
        return format_error(f"获取玩家列表失败：{result['error']}")

    players = result["data"] or []

    await remember_room(event, actual_room_id)

    # 格式化输出
    lines = [f"👥 在线玩家 ({room_name})", f"共 {len(players)} 人", ""]

    if not players:
        lines.append("🈶 当前无在线玩家")
    else:
        for idx, player in enumerate(players, 1):
            nickname = player.get("nickname", "未知")
            uid = player.get("uid", "未知")
            prefab = player.get("prefab", "未知")
            lines.append(f"{idx}. {nickname} ({uid}) - {prefab}")

    return "\n".join(lines)


async def handle_kick(
    bot: Bot,
    event: Event,
    room_id_or_kuid: str,
    kuid: Optional[str] = None,
) -> str:
    """处理踢出玩家命令"""
    if not await ADMIN_PERMISSION(bot, event):
        return format_error("只有管理员才能执行此操作")

    client = get_api_client()

    # 解析参数（支持省略房间ID：/dst kick <KU_ID>）
    actual_room_id: Optional[int] = None
    actual_kuid: Optional[str] = None
    resolved = None

    maybe_room = parse_room_id(room_id_or_kuid)
    if maybe_room is not None:
        if kuid is None:
            return format_error("用法：/dst kick <房间ID> <KU_ID>")
        resolved = await resolve_room_id(event, str(maybe_room))
        actual_room_id = int(maybe_room)
        actual_kuid = kuid
    else:
        # No leading room id, treat first token as KU_ID and use session lock/default room.
        actual_kuid = room_id_or_kuid
        resolved = await resolve_room_id(event, None)
        if resolved is not None:
            actual_room_id = int(resolved.room_id)

    if actual_room_id is None:
        return format_error("请提供房间ID或先使用一次带房间ID的命令以锁定房间")

    assert actual_kuid is not None

    source_hint = ""
    if resolved and resolved.source == RoomSource.LAST:
        source_hint = "（使用上次操作的房间）"
    elif resolved and resolved.source == RoomSource.DEFAULT:
        source_hint = "（使用默认房间）"

    # 使用控制台命令踢人
    # c_kick(userid) - 踢出指定玩家
    result = await client.execute_console_command(
        actual_room_id,
        None,  # 所有世界
        f'c_kick("{actual_kuid}")'
    )

    if result["success"]:
        await remember_room(event, actual_room_id)
        return format_success(f"玩家 {actual_kuid} 已踢出")
    else:
        return format_error(f"踢出失败：{result['error']}")


def init(api_client: DSTApiClient) -> None:
    """
    初始化玩家管理命令

    Args:
        api_client: DMP API 客户端实例
    """
    global _api_client
    _api_client = api_client


__all__ = [
    "players_command",
    "kick_command",
    "handle_players",
    "handle_kick",
    "init",
]
