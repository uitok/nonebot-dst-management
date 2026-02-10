"""
控制台命令 (Alconna 版本)

处理控制台相关命令：console, announce
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
from ..utils.permission import ADMIN_PERMISSION
from ..helpers.formatters import format_error, format_success, format_info
from ..helpers.commands import (
    parse_room_id,
    parse_console_command_args,
    parse_room_and_message,
    escape_console_string,
)
from ..helpers.room_context import RoomSource, remember_room, resolve_room_id


# 全局 API 客户端，由 init 函数设置
_api_client: Optional[DSTApiClient] = None


def get_api_client() -> DSTApiClient:
    """获取 API 客户端"""
    if _api_client is None:
        raise RuntimeError("API 客户端未初始化，请先调用 init() 函数")
    return _api_client


# ========== 命令定义 ==========

console_command = Alconna(
    "dst console",
    Args["room_id", str, None]["world_id", str, None]["command", str, None],
    meta=CommandMeta(
        description="执行控制台命令",
        usage="/dst console <房间ID> [世界ID] <命令>",
        example="/dst console 1 c_announce(\"测试公告\")",
    ),
)


announce_command = Alconna(
    "dst announce",
    Args["room_id", str, None]["message", str, None],
    meta=CommandMeta(
        description="发送全服公告",
        usage="/dst announce <房间ID> <消息>",
        example="/dst announce 1 欢迎来到服务器！",
    ),
)


# ========== 命令处理函数 ==========

async def handle_console(
    bot: Bot,
    event: Event,
    room_id: Optional[str] = None,
    world_id: Optional[str] = None,
    command: Optional[str] = None,
) -> str:
    """处理控制台命令"""
    if not await ADMIN_PERMISSION(bot, event):
        return format_error("只有管理员才能执行此操作")

    client = get_api_client()
    usage = "/dst console <房间ID> [世界ID] <命令>"

    # 构建原始输入字符串
    parts = []
    if room_id:
        parts.append(room_id)
    if world_id:
        parts.append(world_id)
    if command:
        parts.append(command)
    raw = " ".join(parts) if parts else ""

    if not raw:
        return format_error(f"用法：{usage}\n或先使用一次带房间ID的命令以锁定房间")

    resolved = None
    first = raw.split()[0] if raw.split() else ""
    if parse_room_id(first) is None:
        resolved = await resolve_room_id(event, None)
        if resolved is None:
            return format_error(f"用法：{usage}\n或先使用一次带房间ID的命令以锁定房间")
        raw = f"{resolved.room_id} {raw}"

    # 解析参数（支持省略房间ID）
    parsed_room_id, parsed_world_id, parsed_command, error = parse_console_command_args(raw, usage)
    if error:
        return format_error(error)

    world_text = "全部世界" if parsed_world_id is None else f"世界 {parsed_world_id}"
    source_hint = ""
    if resolved and resolved.source == RoomSource.LAST:
        source_hint = "（使用上次操作的房间）"
    elif resolved and resolved.source == RoomSource.DEFAULT:
        source_hint = "（使用默认房间）"

    try:
        result = await client.execute_console_command(parsed_room_id, parsed_world_id, parsed_command)
    except Exception as exc:
        return format_error(f"API 调用失败：{exc}")

    success = bool(result.get("success")) if isinstance(result, dict) else False
    error_msg = result.get("error") if isinstance(result, dict) else None

    if success:
        await remember_room(event, parsed_room_id)
        return format_success("命令已发送")
    else:
        return format_error(f"执行失败：{error_msg or '未知错误'}")


async def handle_announce(
    bot: Bot,
    event: Event,
    room_id: Optional[str] = None,
    message: Optional[str] = None,
) -> str:
    """处理发送公告命令"""
    if not await ADMIN_PERMISSION(bot, event):
        return format_error("只有管理员才能执行此操作")

    client = get_api_client()
    usage = "/dst announce <房间ID> <消息>"

    # 构建原始输入字符串
    parts = []
    if room_id:
        parts.append(room_id)
    if message:
        parts.append(message)
    raw = " ".join(parts) if parts else ""

    if not raw:
        return format_error(f"用法：{usage}\n或先使用一次带房间ID的命令以锁定房间")

    resolved = None
    first = raw.split()[0] if raw.split() else ""
    if parse_room_id(first) is None:
        resolved = await resolve_room_id(event, None)
        if resolved is None:
            return format_error(f"用法：{usage}\n或先使用一次带房间ID的命令以锁定房间")
        raw = f"{resolved.room_id} {raw}"

    # 解析参数（支持省略房间ID）
    parsed_room_id, parsed_message, error = parse_room_and_message(raw, usage)
    if error:
        return format_error(error)

    safe_message = escape_console_string(parsed_message)
    source_hint = ""
    if resolved and resolved.source == RoomSource.LAST:
        source_hint = "（使用上次操作的房间）"
    elif resolved and resolved.source == RoomSource.DEFAULT:
        source_hint = "（使用默认房间）"

    try:
        result = await client.execute_console_command(
            parsed_room_id,
            None,
            f'c_announce("{safe_message}")'
        )
    except Exception as exc:
        return format_error(f"API 调用失败：{exc}")

    success = bool(result.get("success")) if isinstance(result, dict) else False
    error_msg = result.get("error") if isinstance(result, dict) else None

    if success:
        await remember_room(event, parsed_room_id)
        return format_success("公告已发送")
    else:
        return format_error(f"发送失败：{error_msg or '未知错误'}")


def init(api_client: DSTApiClient) -> None:
    """
    初始化控制台命令

    Args:
        api_client: DMP API 客户端实例
    """
    global _api_client
    _api_client = api_client


__all__ = [
    "console_command",
    "announce_command",
    "handle_console",
    "handle_announce",
    "init",
]
