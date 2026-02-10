"""
房间管理命令 (on_alconna 版本)

使用 nonebot-plugin-alconna 的 on_alconna 匹配器。
"""

from __future__ import annotations

from typing import Optional

from arclet.alconna import Alconna, Args, CommandMeta
from nonebot.internal.adapter import Event

from nonebot_plugin_alconna import Match, AlconnaMatch, on_alconna

from ..client.api_client import DSTApiClient
from ..utils.permission import ADMIN_PERMISSION, USER_PERMISSION
from ..helpers.formatters import (
    format_error,
    format_success,
    status_badge,
)
from ..helpers.room_context import remember_room, resolve_room_id
from ..services.monitors.sign_monitor import get_sign_monitor


# 全局 API 客户端，由 init 函数设置
_api_client: Optional[DSTApiClient] = None


def get_api_client() -> DSTApiClient:
    """获取 API 客户端"""
    if _api_client is None:
        raise RuntimeError("API 客户端未初始化，请先调用 init() 函数")
    return _api_client


# ========== 命令定义 + on_alconna 匹配器 ==========

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

# ========== on_alconna 匹配器 ==========

list_matcher = on_alconna(room_list_command, permission=USER_PERMISSION, priority=10, block=True)
info_matcher = on_alconna(room_info_command, permission=USER_PERMISSION, priority=10, block=True)
start_matcher = on_alconna(room_start_command, permission=ADMIN_PERMISSION, priority=10, block=True)
stop_matcher = on_alconna(room_stop_command, permission=ADMIN_PERMISSION, priority=10, block=True)
restart_matcher = on_alconna(room_restart_command, permission=ADMIN_PERMISSION, priority=10, block=True)


# ========== 命令处理函数 ==========

@list_matcher.handle()
async def handle_room_list(
    event: Event,
    page: Match[int] = AlconnaMatch("page"),
) -> None:
    """处理房间列表命令"""
    client = get_api_client()
    page_num = page.result if page.available else 1

    result = await client.get_room_list(page=page_num, page_size=10)
    if not result["success"]:
        await list_matcher.finish(format_error(f"获取房间列表失败：{result['error']}"))

    data = result["data"]
    rooms = data.get("rows", [])
    total = data.get("totalCount", 0)
    total_pages = max(1, (total + 9) // 10)

    lines = [f"📋 房间列表 (第 {page_num}/{total_pages} 页)", f"总计: {total} 个房间", ""]
    for room in rooms:
        status = "🟢 运行中" if room.get("status") else "🔴 已停止"
        lines.append(f"{room['id']}. {room.get('gameName', '未知')} - {status}")

    await list_matcher.finish("\n".join(lines))


@info_matcher.handle()
async def handle_room_info(
    event: Event,
    room_id: Match[str] = AlconnaMatch("room_id"),
) -> None:
    """处理房间详情命令"""
    client = get_api_client()
    room_id_val = room_id.result if room_id.available else None

    resolved = await resolve_room_id(event, room_id_val)
    if resolved is None:
        if room_id_val:
            await info_matcher.finish(format_error("请提供有效的房间ID：/dst info <房间ID>"))
        else:
            await info_matcher.finish(format_error("请提供房间ID：/dst info <房间ID>\n或先使用一次带房间ID的命令以锁定房间"))

    actual_room_id = int(resolved.room_id)

    room_result = await client.get_room_info(actual_room_id)
    if not room_result["success"]:
        await info_matcher.finish(format_error(f"获取房间信息失败：{room_result['error']}"))

    worlds_result = await client.get_world_list(actual_room_id)
    worlds = worlds_result["data"].get("rows", []) if worlds_result["success"] else []

    players_result = await client.get_online_players(actual_room_id)
    players = players_result["data"] or [] if players_result["success"] else []

    monitor = get_sign_monitor()
    if monitor:
        try:
            await monitor.check_room_pending_rewards(actual_room_id)
        except Exception:
            pass

    await remember_room(event, actual_room_id)

    room = room_result["data"]
    lines = [
        "🏠 房间详情",
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

    await info_matcher.finish("\n".join(lines))


async def _room_action(
    matcher,
    event: Event,
    room_id_match: Match[str],
    action_name: str,
    api_call,
    success_status: bool,
) -> None:
    """通用房间操作处理"""
    client = get_api_client()
    room_id_val = room_id_match.result if room_id_match.available else None

    resolved = await resolve_room_id(event, room_id_val)
    if resolved is None:
        if room_id_val:
            await matcher.finish(format_error(f"请提供有效的房间ID：/dst {action_name} <房间ID>"))
        else:
            await matcher.finish(format_error(f"请提供房间ID：/dst {action_name} <房间ID>\n或先使用一次带房间ID的命令以锁定房间"))

    actual_room_id = int(resolved.room_id)
    result = await api_call(actual_room_id)

    if result["success"]:
        await remember_room(event, actual_room_id)
        action_text = {"start": "启动成功", "stop": "已关闭", "restart": "重启成功"}[action_name]
        await matcher.finish(format_success(f"房间 {actual_room_id} {action_text} {status_badge(success_status)}"))
    else:
        action_text = {"start": "启动", "stop": "关闭", "restart": "重启"}[action_name]
        await matcher.finish(format_error(f"{action_text}失败：{result['error']}"))


@start_matcher.handle()
async def handle_room_start(
    event: Event,
    room_id: Match[str] = AlconnaMatch("room_id"),
) -> None:
    """处理启动房间命令"""
    await _room_action(start_matcher, event, room_id, "start", get_api_client().activate_room, True)


@stop_matcher.handle()
async def handle_room_stop(
    event: Event,
    room_id: Match[str] = AlconnaMatch("room_id"),
) -> None:
    """处理关闭房间命令"""
    await _room_action(stop_matcher, event, room_id, "stop", get_api_client().deactivate_room, False)


@restart_matcher.handle()
async def handle_room_restart(
    event: Event,
    room_id: Match[str] = AlconnaMatch("room_id"),
) -> None:
    """处理重启房间命令"""
    await _room_action(restart_matcher, event, room_id, "restart", get_api_client().restart_room, True)


def init(api_client: DSTApiClient) -> None:
    """初始化房间管理命令"""
    global _api_client
    _api_client = api_client


__all__ = [
    "room_list_command",
    "room_info_command",
    "room_start_command",
    "room_stop_command",
    "room_restart_command",
    "list_matcher",
    "info_matcher",
    "start_matcher",
    "stop_matcher",
    "restart_matcher",
    "handle_room_list",
    "handle_room_info",
    "handle_room_start",
    "handle_room_stop",
    "handle_room_restart",
    "init",
]
