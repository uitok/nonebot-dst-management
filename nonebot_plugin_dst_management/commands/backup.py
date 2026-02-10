"""
备份管理命令 (on_alconna)

提供备份相关命令：backup list, backup create, backup restore
支持房间上下文（resolve_room_id / remember_room）。
"""

from __future__ import annotations

from typing import Optional

from arclet.alconna import Alconna, Args, CommandMeta
from nonebot.internal.adapter import Event

from nonebot_plugin_alconna import Match, AlconnaMatch, on_alconna

from ..client.api_client import DSTApiClient
from ..utils.permission import ADMIN_PERMISSION, USER_PERMISSION, check_group
from ..helpers.commands import parse_room_id
from ..helpers.formatters import (
    format_error,
    format_success,
    format_info,
    format_warning,
    render_auto,
)
from ..helpers.room_context import RoomSource, remember_room, resolve_room_id


# 全局 API 客户端
_api_client: Optional[DSTApiClient] = None


def get_api_client() -> DSTApiClient:
    if _api_client is None:
        raise RuntimeError("API 客户端未初始化，请先调用 init() 函数")
    return _api_client


# ========== Alconna 命令定义 ==========

backup_list_command = Alconna(
    "dst backup list",
    Args["room_id", str, None],
    meta=CommandMeta(
        description="查看备份列表",
        usage="/dst backup list [房间ID]",
        example="/dst backup list 1",
    ),
)

backup_create_command = Alconna(
    "dst backup create",
    Args["room_id", str, None],
    meta=CommandMeta(
        description="创建备份",
        usage="/dst backup create [房间ID]",
        example="/dst backup create 1",
    ),
)

backup_restore_command = Alconna(
    "dst backup restore",
    Args["room_id_or_file", str, None]["filename", str, None],
    meta=CommandMeta(
        description="恢复备份",
        usage="/dst backup restore <房间ID> <备份文件名>\n或：/dst backup restore <备份文件名>",
        example="/dst backup restore 1 backup_20240101.tar.gz",
    ),
)

# ========== on_alconna 匹配器 ==========

backup_list_matcher = on_alconna(
    backup_list_command, permission=USER_PERMISSION, priority=10, block=True
)
backup_create_matcher = on_alconna(
    backup_create_command, permission=ADMIN_PERMISSION, priority=10, block=True
)
backup_restore_matcher = on_alconna(
    backup_restore_command, permission=ADMIN_PERMISSION, priority=10, block=True
)


# ========== 命令处理 ==========

@backup_list_matcher.handle()
async def handle_backup_list(
    event: Event,
    room_id: Match[str] = AlconnaMatch("room_id"),
) -> None:
    """处理备份列表命令"""
    if not await check_group(event):
        await backup_list_matcher.finish(format_error("当前群组未授权使用此功能"))
        return

    client = get_api_client()
    room_arg = room_id.result if room_id.available else None

    resolved = await resolve_room_id(event, room_arg)
    if resolved is None:
        if room_arg:
            await backup_list_matcher.finish(
                format_error("请提供有效的房间ID：/dst backup list <房间ID>")
            )
        else:
            await backup_list_matcher.finish(
                format_error(
                    "请提供房间ID：/dst backup list <房间ID>\n或先使用一次带房间ID的命令以锁定房间"
                )
            )
        return

    rid = int(resolved.room_id)

    if resolved.source == RoomSource.LAST:
        await backup_list_matcher.send(format_info(f"未指定房间ID，使用上次操作的房间 {rid}..."))
    elif resolved.source == RoomSource.DEFAULT:
        await backup_list_matcher.send(format_info(f"未指定房间ID，使用默认房间 {rid}..."))

    # 获取房间名称
    room_result = await client.get_room_info(rid)
    room_name = "未知房间"
    if room_result["success"]:
        room_name = room_result["data"].get("gameName", "未知房间")

    # 获取备份列表
    result = await client.list_backups(rid)

    if not result["success"]:
        await backup_list_matcher.finish(format_error(f"获取备份列表失败：{result['error']}"))
        return

    backups = result["data"] or []

    message = await render_auto(
        "backups",
        event=event,
        room_name=room_name,
        backups=backups,
    )
    await remember_room(event, rid)
    await backup_list_matcher.finish(message)


@backup_create_matcher.handle()
async def handle_backup_create(
    event: Event,
    room_id: Match[str] = AlconnaMatch("room_id"),
) -> None:
    """处理创建备份命令"""
    client = get_api_client()
    room_arg = room_id.result if room_id.available else None

    resolved = await resolve_room_id(event, room_arg)
    if resolved is None:
        if room_arg:
            await backup_create_matcher.finish(
                format_error("请提供有效的房间ID：/dst backup create <房间ID>")
            )
        else:
            await backup_create_matcher.finish(
                format_error(
                    "请提供房间ID：/dst backup create <房间ID>\n或先使用一次带房间ID的命令以锁定房间"
                )
            )
        return

    rid = int(resolved.room_id)

    source_hint = ""
    if resolved.source == RoomSource.LAST:
        source_hint = "（使用上次操作的房间）"
    elif resolved.source == RoomSource.DEFAULT:
        source_hint = "（使用默认房间）"
    await backup_create_matcher.send(format_info(f"正在为房间 {rid}{source_hint} 创建备份，请稍候..."))

    result = await client.create_backup(rid)

    if result["success"]:
        await remember_room(event, rid)
        await backup_create_matcher.finish(format_success("备份创建成功"))
    else:
        await backup_create_matcher.finish(format_error(f"备份创建失败：{result['error']}"))


@backup_restore_matcher.handle()
async def handle_backup_restore(
    event: Event,
    room_id_or_file: Match[str] = AlconnaMatch("room_id_or_file"),
    filename: Match[str] = AlconnaMatch("filename"),
) -> None:
    """处理恢复备份命令"""
    client = get_api_client()

    first_arg = room_id_or_file.result if room_id_or_file.available else None
    second_arg = filename.result if filename.available else None

    if not first_arg:
        await backup_restore_matcher.finish(
            format_error(
                "用法：/dst backup restore <房间ID> <备份文件名>\n或：/dst backup restore <备份文件名>"
            )
        )
        return

    actual_room_id: Optional[int] = None
    actual_filename: Optional[str] = None
    resolved = None

    maybe_room = parse_room_id(first_arg)
    if maybe_room is not None:
        if not second_arg:
            await backup_restore_matcher.finish(
                format_error("用法：/dst backup restore <房间ID> <备份文件名>")
            )
            return
        resolved = await resolve_room_id(event, str(maybe_room))
        actual_room_id = int(maybe_room)
        actual_filename = second_arg
    else:
        # First arg is filename, use room context
        actual_filename = first_arg
        resolved = await resolve_room_id(event, None)
        if resolved is not None:
            actual_room_id = int(resolved.room_id)

    if actual_room_id is None:
        await backup_restore_matcher.finish(
            format_error("请提供房间ID或先使用一次带房间ID的命令以锁定房间")
        )
        return
    assert actual_filename is not None

    source_hint = ""
    if resolved and resolved.source == RoomSource.LAST:
        source_hint = "（使用上次操作的房间）"
    elif resolved and resolved.source == RoomSource.DEFAULT:
        source_hint = "（使用默认房间）"
    await backup_restore_matcher.send(
        format_warning(
            f"即将恢复房间 {actual_room_id}{source_hint} 的备份 {actual_filename}，"
            f"此操作不可撤销！\n确认请发送 \"是\"，取消请发送 \"否\""
        )
    )

    await backup_restore_matcher.send(format_info(f"正在恢复备份 {actual_filename}..."))

    result = await client.restore_backup(actual_room_id, actual_filename)

    if result["success"]:
        await remember_room(event, actual_room_id)
        await backup_restore_matcher.finish(format_success("备份恢复成功，房间将自动重启"))
    else:
        await backup_restore_matcher.finish(format_error(f"备份恢复失败：{result['error']}"))


def init(api_client: DSTApiClient) -> None:
    """初始化备份管理命令"""
    global _api_client
    _api_client = api_client


__all__ = [
    "backup_list_command",
    "backup_create_command",
    "backup_restore_command",
    "backup_list_matcher",
    "backup_create_matcher",
    "backup_restore_matcher",
    "handle_backup_list",
    "handle_backup_create",
    "handle_backup_restore",
    "init",
]
