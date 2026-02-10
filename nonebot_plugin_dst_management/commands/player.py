"""
玩家管理命令 (on_alconna 版本)

使用 nonebot-plugin-alconna 的 on_alconna 匹配器。
"""

from __future__ import annotations

from typing import Optional

from arclet.alconna import Alconna, Args, CommandMeta
from nonebot.internal.adapter import Event

from nonebot_plugin_alconna import Match, AlconnaMatch, on_alconna

from ..client.api_client import DSTApiClient
from ..utils.permission import ADMIN_PERMISSION, USER_PERMISSION
from ..helpers.formatters import format_error, format_success
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

# ========== on_alconna 匹配器 ==========

players_matcher = on_alconna(players_command, permission=USER_PERMISSION, priority=10, block=True)
kick_matcher = on_alconna(kick_command, permission=ADMIN_PERMISSION, priority=10, block=True)


# ========== 命令处理函数 ==========

@players_matcher.handle()
async def handle_players(
    event: Event,
    room_id: Match[str] = AlconnaMatch("room_id"),
) -> None:
    """处理查看在线玩家命令"""
    client = get_api_client()
    room_id_val = room_id.result if room_id.available else None

    resolved = await resolve_room_id(event, room_id_val)
    if resolved is None:
        if room_id_val:
            await players_matcher.finish(format_error("请提供有效的房间ID：/dst players <房间ID>"))
        else:
            await players_matcher.finish(format_error("请提供房间ID：/dst players <房间ID>\n或先使用一次带房间ID的命令以锁定房间"))

    actual_room_id = int(resolved.room_id)

    room_result = await client.get_room_info(actual_room_id)
    room_name = "未知房间"
    if room_result["success"]:
        room_name = room_result["data"].get("gameName", "未知房间")

    result = await client.get_online_players(actual_room_id)
    if not result["success"]:
        await players_matcher.finish(format_error(f"获取玩家列表失败：{result['error']}"))

    players = result["data"] or []
    await remember_room(event, actual_room_id)

    lines = [f"👥 在线玩家 ({room_name})", f"共 {len(players)} 人", ""]
    if not players:
        lines.append("🈶 当前无在线玩家")
    else:
        for idx, player in enumerate(players, 1):
            nickname = player.get("nickname", "未知")
            uid = player.get("uid", "未知")
            prefab = player.get("prefab", "未知")
            lines.append(f"{idx}. {nickname} ({uid}) - {prefab}")

    await players_matcher.finish("\n".join(lines))


@kick_matcher.handle()
async def handle_kick(
    event: Event,
    room_id_or_kuid: Match[str] = AlconnaMatch("room_id_or_kuid"),
    kuid: Match[str] = AlconnaMatch("kuid"),
) -> None:
    """处理踢出玩家命令"""
    client = get_api_client()

    if not room_id_or_kuid.available:
        await kick_matcher.finish(format_error("用法：/dst kick <房间ID> <KU_ID>"))

    actual_room_id: Optional[int] = None
    actual_kuid: Optional[str] = None
    resolved = None

    maybe_room = parse_room_id(room_id_or_kuid.result)
    if maybe_room is not None:
        if not kuid.available:
            await kick_matcher.finish(format_error("用法：/dst kick <房间ID> <KU_ID>"))
        resolved = await resolve_room_id(event, str(maybe_room))
        actual_room_id = int(maybe_room)
        actual_kuid = kuid.result
    else:
        actual_kuid = room_id_or_kuid.result
        resolved = await resolve_room_id(event, None)
        if resolved is not None:
            actual_room_id = int(resolved.room_id)

    if actual_room_id is None:
        await kick_matcher.finish(format_error("请提供房间ID或先使用一次带房间ID的命令以锁定房间"))

    assert actual_kuid is not None

    result = await client.execute_console_command(
        actual_room_id,
        None,
        f'c_kick("{actual_kuid}")'
    )

    if result["success"]:
        await remember_room(event, actual_room_id)
        await kick_matcher.finish(format_success(f"玩家 {actual_kuid} 已踢出"))
    else:
        await kick_matcher.finish(format_error(f"踢出失败：{result['error']}"))


def init(api_client: DSTApiClient) -> None:
    """初始化玩家管理命令"""
    global _api_client
    _api_client = api_client


__all__ = [
    "players_command",
    "kick_command",
    "players_matcher",
    "kick_matcher",
    "handle_players",
    "handle_kick",
    "init",
]
