"""
房间管理命令 (Alconna 版本)

处理房间相关的命令：list, info, start, stop, restart
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
from ..helpers.formatters import (
    format_error,
    format_success,
    format_info,
    status_badge,
)
from ..helpers.room_context import RoomSource, remember_room, resolve_room_id
from ..services.monitors.sign_monitor import get_sign_monitor


# 全局 API 客户端，由 init 函数设置
_api_client: Optional[DSTApiClient] = None


def get_api_client() -> DSTApiClient:
    """获取 API 客户端"""
    if _api_client is None:
        raise RuntimeError("API 客户端未初始化，请先调用 init() 函数")
    return _api_client


# ========== 命令定义 ==========

room_list_command = Alconna(
    "dst list",
    Args["page", int, 1],
    meta=CommandMeta(
        description="查看房间列表",
        usage="/dst list [页码]",
        example="/dst list 1",
    ),
)


room_info_command = Alconna(
    "dst info",
    Args["room_id", str, None],
    meta=CommandMeta(
        description="查看房间详情",
        usage="/dst info [房间ID]",
        example="/dst info 1",
    ),
)


room_start_command = Alconna(
    "dst start",
    Args["room_id", str, None],
    meta=CommandMeta(
        description="启动房间",
        usage="/dst start [房间ID]",
        example="/dst start 1",
    ),
)


room_stop_command = Alconna(
    "dst stop",
    Args["room_id", str, None],
    meta=CommandMeta(
        description="关闭房间",
        usage="/dst stop [房间ID]",
        example="/dst stop 1",
    ),
)


room_restart_command = Alconna(
    "dst restart",
    Args["room_id", str, None],
    meta=CommandMeta(
        description="重启房间",
        usage="/dst restart [房间ID]",
        example="/dst restart 1",
    ),
)


# ========== 命令处理函数 ==========

async def handle_room_list(bot: Bot, event: Event, page: int = 1) -> str:
    """处理房间列表命令"""
    if not await USER_PERMISSION(bot, event):
        return format_error("当前群组未授权使用此功能")

    client = get_api_client()
    result = await client.get_room_list(page=page, page_size=10)

    if not result["success"]:
        return format_error(f"获取房间列表失败：{result['error']}")

    # 格式化输出
    data = result["data"]
    rooms = data.get("rows", [])
    total = data.get("totalCount", 0)
    total_pages = max(1, (total + 9) // 10)

    # 简化版格式（后续可调用 render_auto）
    lines = [f"📋 房间列表 (第 {page}/{total_pages} 页)", f"总计: {total} 个房间", ""]
    for room in rooms:
        status = "🟢 运行中" if room.get("status") else "🔴 已停止"
        lines.append(f"{room['id']}. {room.get('gameName', '未知')} - {status}")

    return "\n".join(lines)


async def handle_room_info(bot: Bot, event: Event, room_id: Optional[str] = None) -> str:
    """处理房间详情命令"""
    if not await USER_PERMISSION(bot, event):
        return format_error("当前群组未授权使用此功能")

    client = get_api_client()

    # 解析房间 ID（支持会话锁定）
    resolved = await resolve_room_id(event, room_id if room_id else None)
    if resolved is None:
        if room_id:
            return format_error("请提供有效的房间ID：/dst info <房间ID>")
        else:
            return format_error("请提供房间ID：/dst info <房间ID>\n或先使用一次带房间ID的命令以锁定房间")

    actual_room_id = int(resolved.room_id)

    # 获取房间信息
    room_result = await client.get_room_info(actual_room_id)
    if not room_result["success"]:
        return format_error(f"获取房间信息失败：{room_result['error']}")

    # 获取世界列表
    worlds_result = await client.get_world_list(actual_room_id)
    worlds = []
    if worlds_result["success"]:
        worlds = worlds_result["data"].get("rows", [])

    # 获取在线玩家
    players_result = await client.get_online_players(actual_room_id)
    players = []
    if players_result["success"]:
        players = players_result["data"] or []

    # 触发签到奖励检查
    monitor = get_sign_monitor()
    if monitor:
        try:
            await monitor.check_room_pending_rewards(actual_room_id)
        except Exception:
            pass

    await remember_room(event, actual_room_id)

    # 格式化输出
    room = room_result["data"]
    lines = [
        f"🏠 房间详情",
        f"名称: {room.get('gameName', '未知')}",
        f"模式: {room.get('gameMode', '未知')}",
        f"状态: {'运行中' if room.get('status') else '已停止'} {status_badge(room.get('status'))}",
        f"最大玩家: {room.get('maxPlayer', 0)}",
        f"在线玩家: {len(players)} 人",
        "",
        "🌍 世界列表:",
    ]

    for world in worlds:
        lines.append(f"  - 世界 {world.get('id', '?')}: {world.get('name', '未知')}")

    if players:
        lines.append("")
        lines.append("👥 在线玩家:")
        for player in players:
            lines.append(f"  - {player.get('nickname', '未知')} ({player.get('uid', '未知')})")

    return "\n".join(lines)


async def handle_room_start(bot: Bot, event: Event, room_id: Optional[str] = None) -> str:
    """处理启动房间命令"""
    if not await ADMIN_PERMISSION(bot, event):
        return format_error("只有管理员才能执行此操作")

    client = get_api_client()

    # 解析房间 ID（支持会话锁定）
    resolved = await resolve_room_id(event, room_id if room_id else None)
    if resolved is None:
        if room_id:
            return format_error("请提供有效的房间ID：/dst start <房间ID>")
        else:
            return format_error("请提供房间ID：/dst start <房间ID>\n或先使用一次带房间ID的命令以锁定房间")

    actual_room_id = int(resolved.room_id)

    # 调用 API
    result = await client.activate_room(actual_room_id)

    if result["success"]:
        await remember_room(event, actual_room_id)
        return format_success(f"房间 {actual_room_id} 启动成功 {status_badge(True)}")
    else:
        return format_error(f"启动失败：{result['error']}")


async def handle_room_stop(bot: Bot, event: Event, room_id: Optional[str] = None) -> str:
    """处理关闭房间命令"""
    if not await ADMIN_PERMISSION(bot, event):
        return format_error("只有管理员才能执行此操作")

    client = get_api_client()

    # 解析房间 ID（支持会话锁定）
    resolved = await resolve_room_id(event, room_id if room_id else None)
    if resolved is None:
        if room_id:
            return format_error("请提供有效的房间ID：/dst stop <房间ID>")
        else:
            return format_error("请提供房间ID：/dst stop <房间ID>\n或先使用一次带房间ID的命令以锁定房间")

    actual_room_id = int(resolved.room_id)

    # 调用 API
    result = await client.deactivate_room(actual_room_id)

    if result["success"]:
        await remember_room(event, actual_room_id)
        return format_success(f"房间 {actual_room_id} 已关闭 {status_badge(False)}")
    else:
        return format_error(f"关闭失败：{result['error']}")


async def handle_room_restart(bot: Bot, event: Event, room_id: Optional[str] = None) -> str:
    """处理重启房间命令"""
    if not await ADMIN_PERMISSION(bot, event):
        return format_error("只有管理员才能执行此操作")

    client = get_api_client()

    # 解析房间 ID（支持会话锁定）
    resolved = await resolve_room_id(event, room_id if room_id else None)
    if resolved is None:
        if room_id:
            return format_error("请提供有效的房间ID：/dst restart <房间ID>")
        else:
            return format_error("请提供房间ID：/dst restart <房间ID>\n或先使用一次带房间ID的命令以锁定房间")

    actual_room_id = int(resolved.room_id)

    # 调用 API
    result = await client.restart_room(actual_room_id)

    if result["success"]:
        await remember_room(event, actual_room_id)
        return format_success(f"房间 {actual_room_id} 重启成功 {status_badge(True)}")
    else:
        return format_error(f"重启失败：{result['error']}")


def init(api_client: DSTApiClient) -> None:
    """
    初始化房间管理命令

    Args:
        api_client: DMP API 客户端实例
    """
    global _api_client
    _api_client = api_client


__all__ = [
    "room_list_command",
    "room_info_command",
    "room_start_command",
    "room_stop_command",
    "room_restart_command",
    "handle_room_list",
    "handle_room_info",
    "handle_room_start",
    "handle_room_stop",
    "handle_room_restart",
    "init",
]
