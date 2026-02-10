"""
控制台命令 (on_alconna 版本)

使用 nonebot-plugin-alconna 的 on_alconna 匹配器。
"""

from __future__ import annotations

from typing import Optional

from arclet.alconna import Alconna, Args, CommandMeta
from nonebot.internal.adapter import Event

from nonebot_plugin_alconna import Match, AlconnaMatch, on_alconna

from ..client.api_client import DSTApiClient
from ..utils.permission import ADMIN_PERMISSION
from ..helpers.formatters import format_error, format_success
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
        example='/dst console 1 c_announce("测试公告")',
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

# ========== on_alconna 匹配器 ==========

console_matcher = on_alconna(console_command, permission=ADMIN_PERMISSION, priority=10, block=True)
announce_matcher = on_alconna(announce_command, permission=ADMIN_PERMISSION, priority=10, block=True)


# ========== 命令处理函数 ==========

@console_matcher.handle()
async def handle_console(
    event: Event,
    room_id: Match[str] = AlconnaMatch("room_id"),
    world_id: Match[str] = AlconnaMatch("world_id"),
    command: Match[str] = AlconnaMatch("command"),
) -> None:
    """处理控制台命令"""
    client = get_api_client()
    usage = "/dst console <房间ID> [世界ID] <命令>"

    # 构建原始输入字符串
    parts = []
    if room_id.available:
        parts.append(room_id.result)
    if world_id.available:
        parts.append(world_id.result)
    if command.available:
        parts.append(command.result)
    raw = " ".join(parts) if parts else ""

    if not raw:
        await console_matcher.finish(format_error(f"用法：{usage}\n或先使用一次带房间ID的命令以锁定房间"))

    resolved = None
    first = raw.split()[0] if raw.split() else ""
    if parse_room_id(first) is None:
        resolved = await resolve_room_id(event, None)
        if resolved is None:
            await console_matcher.finish(format_error(f"用法：{usage}\n或先使用一次带房间ID的命令以锁定房间"))
        raw = f"{resolved.room_id} {raw}"

    parsed_room_id, parsed_world_id, parsed_command, error = parse_console_command_args(raw, usage)
    if error:
        await console_matcher.finish(format_error(error))

    try:
        result = await client.execute_console_command(parsed_room_id, parsed_world_id, parsed_command)
    except Exception as exc:
        await console_matcher.finish(format_error(f"API 调用失败：{exc}"))

    success = bool(result.get("success")) if isinstance(result, dict) else False
    error_msg = result.get("error") if isinstance(result, dict) else None

    if success:
        await remember_room(event, parsed_room_id)
        await console_matcher.finish(format_success("命令已发送"))
    else:
        await console_matcher.finish(format_error(f"执行失败：{error_msg or '未知错误'}"))


@announce_matcher.handle()
async def handle_announce(
    event: Event,
    room_id: Match[str] = AlconnaMatch("room_id"),
    message: Match[str] = AlconnaMatch("message"),
) -> None:
    """处理发送公告命令"""
    client = get_api_client()
    usage = "/dst announce <房间ID> <消息>"

    parts = []
    if room_id.available:
        parts.append(room_id.result)
    if message.available:
        parts.append(message.result)
    raw = " ".join(parts) if parts else ""

    if not raw:
        await announce_matcher.finish(format_error(f"用法：{usage}\n或先使用一次带房间ID的命令以锁定房间"))

    resolved = None
    first = raw.split()[0] if raw.split() else ""
    if parse_room_id(first) is None:
        resolved = await resolve_room_id(event, None)
        if resolved is None:
            await announce_matcher.finish(format_error(f"用法：{usage}\n或先使用一次带房间ID的命令以锁定房间"))
        raw = f"{resolved.room_id} {raw}"

    parsed_room_id, parsed_message, error = parse_room_and_message(raw, usage)
    if error:
        await announce_matcher.finish(format_error(error))

    safe_message = escape_console_string(parsed_message)

    try:
        result = await client.execute_console_command(
            parsed_room_id,
            None,
            f'c_announce("{safe_message}")'
        )
    except Exception as exc:
        await announce_matcher.finish(format_error(f"API 调用失败：{exc}"))

    success = bool(result.get("success")) if isinstance(result, dict) else False
    error_msg = result.get("error") if isinstance(result, dict) else None

    if success:
        await remember_room(event, parsed_room_id)
        await announce_matcher.finish(format_success("公告已发送"))
    else:
        await announce_matcher.finish(format_error(f"发送失败：{error_msg or '未知错误'}"))


def init(api_client: DSTApiClient) -> None:
    """初始化控制台命令"""
    global _api_client
    _api_client = api_client


__all__ = [
    "console_command",
    "announce_command",
    "console_matcher",
    "announce_matcher",
    "handle_console",
    "handle_announce",
    "init",
]
