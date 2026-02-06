"""
控制台命令处理器

处理控制台相关命令：console, announce
"""

from nonebot import on_command
from nonebot.adapters.onebot.v11 import Bot, MessageEvent, Message
from nonebot.params import CommandArg
from nonebot.permission import Permission
from nonebot.rule import Rule

from ..client.api_client import DSTApiClient
from ..utils.permission import check_admin, check_group
from ..utils.formatter import (
    format_error,
    format_success,
    format_info,
)
from ..helpers.commands import (
    parse_room_id,
    parse_console_command_args,
    parse_room_and_message,
    escape_console_string,
)
from ..helpers.room_context import RoomSource, remember_room, resolve_room_id


def init(api_client: DSTApiClient):
    """
    初始化控制台命令

    Args:
        api_client: DMP API 客户端实例
    """

    # ========== 执行控制台命令 ==========
    group_rule = Rule(check_group)
    admin_permission = Permission(check_admin)
    console_cmd = on_command(
        "dst console",
        priority=10,
        block=True,
        rule=group_rule,
        permission=admin_permission,
    )

    @console_cmd.handle()
    async def handle_console(bot: Bot, event: MessageEvent, args: Message = CommandArg()):
        # 检查群组权限
        if not await check_group(event):
            await console_cmd.finish(format_error("当前群组未授权使用此功能"))
            return

        # 检查管理员权限
        if not await check_admin(bot, event):
            await console_cmd.finish(format_error("只有管理员才能执行此操作"))
            return

        usage = "/dst console <房间ID> [世界ID] <命令>"
        raw = args.extract_plain_text().strip()
        if not raw:
            await console_cmd.finish(format_error(f"用法：{usage}\n或先使用一次带房间ID的命令以锁定房间"))
            return

        resolved = None
        first = raw.split()[0] if raw.split() else ""
        if parse_room_id(first) is None:
            resolved = await resolve_room_id(event, None)
            if resolved is None:
                await console_cmd.finish(format_error(f"用法：{usage}\n或先使用一次带房间ID的命令以锁定房间"))
                return
            raw = f"{resolved.room_id} {raw}"

        # 解析参数（支持省略房间ID）
        room_id, world_id, command, error = parse_console_command_args(raw, usage)
        if error:
            await console_cmd.finish(format_error(error))
            return

        world_text = "全部世界" if world_id is None else f"世界 {world_id}"
        source_hint = ""
        if resolved and resolved.source == RoomSource.LAST:
            source_hint = "（使用上次操作的房间）"
        elif resolved and resolved.source == RoomSource.DEFAULT:
            source_hint = "（使用默认房间）"
        await console_cmd.send(format_info(f"正在向房间 {room_id}{source_hint} 的 {world_text} 发送命令..."))

        try:
            result = await api_client.execute_console_command(room_id, world_id, command)
        except Exception as exc:
            await console_cmd.finish(format_error(f"API 调用失败：{exc}"))
            return

        success = bool(result.get("success")) if isinstance(result, dict) else False
        error_msg = result.get("error") if isinstance(result, dict) else None

        if success:
            await remember_room(event, room_id)
            await console_cmd.finish(format_success("命令已发送"))
        else:
            await console_cmd.finish(format_error(f"执行失败：{error_msg or '未知错误'}"))

    # ========== 发送全服公告 ==========
    announce_cmd = on_command(
        "dst announce",
        priority=10,
        block=True,
        rule=group_rule,
        permission=admin_permission,
    )

    @announce_cmd.handle()
    async def handle_announce(bot: Bot, event: MessageEvent, args: Message = CommandArg()):
        # 检查群组权限
        if not await check_group(event):
            await announce_cmd.finish(format_error("当前群组未授权使用此功能"))
            return

        # 检查管理员权限
        if not await check_admin(bot, event):
            await announce_cmd.finish(format_error("只有管理员才能执行此操作"))
            return

        usage = "/dst announce <房间ID> <消息>"
        raw = args.extract_plain_text().strip()
        if not raw:
            await announce_cmd.finish(format_error(f"用法：{usage}\n或先使用一次带房间ID的命令以锁定房间"))
            return

        resolved = None
        first = raw.split()[0] if raw.split() else ""
        if parse_room_id(first) is None:
            resolved = await resolve_room_id(event, None)
            if resolved is None:
                await announce_cmd.finish(format_error(f"用法：{usage}\n或先使用一次带房间ID的命令以锁定房间"))
                return
            raw = f"{resolved.room_id} {raw}"

        # 解析参数（支持省略房间ID）
        room_id, message, error = parse_room_and_message(raw, usage)
        if error:
            await announce_cmd.finish(format_error(error))
            return

        safe_message = escape_console_string(message)
        source_hint = ""
        if resolved and resolved.source == RoomSource.LAST:
            source_hint = "（使用上次操作的房间）"
        elif resolved and resolved.source == RoomSource.DEFAULT:
            source_hint = "（使用默认房间）"
        await announce_cmd.send(format_info(f"正在向房间 {room_id}{source_hint} 发送公告..."))

        try:
            result = await api_client.execute_console_command(
                room_id,
                None,
                f'c_announce("{safe_message}")'
            )
        except Exception as exc:
            await announce_cmd.finish(format_error(f"API 调用失败：{exc}"))
            return

        success = bool(result.get("success")) if isinstance(result, dict) else False
        error_msg = result.get("error") if isinstance(result, dict) else None

        if success:
            await remember_room(event, room_id)
            await announce_cmd.finish(format_success("公告已发送"))
        else:
            await announce_cmd.finish(format_error(f"发送失败：{error_msg or '未知错误'}"))
