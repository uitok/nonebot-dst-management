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
    parse_console_command_args,
    parse_room_and_message,
    escape_console_string,
)


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

        # 解析参数
        room_id, world_id, command, error = parse_console_command_args(
            args.extract_plain_text(),
            "/dst console <房间ID> [世界ID] <命令>"
        )
        if error:
            await console_cmd.finish(format_error(error))
            return

        world_text = "全部世界" if world_id is None else f"世界 {world_id}"
        await console_cmd.send(
            format_info(f"正在向房间 {room_id} 的 {world_text} 发送命令...")
        )

        try:
            result = await api_client.execute_console_command(room_id, world_id, command)
        except Exception as exc:
            await console_cmd.finish(format_error(f"API 调用失败：{exc}"))
            return

        success = bool(result.get("success")) if isinstance(result, dict) else False
        error_msg = result.get("error") if isinstance(result, dict) else None

        if success:
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

        # 解析参数
        room_id, message, error = parse_room_and_message(
            args.extract_plain_text(),
            "/dst announce <房间ID> <消息>"
        )
        if error:
            await announce_cmd.finish(format_error(error))
            return

        safe_message = escape_console_string(message)
        await announce_cmd.send(format_info(f"正在向房间 {room_id} 发送公告..."))

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
            await announce_cmd.finish(format_success("公告已发送"))
        else:
            await announce_cmd.finish(format_error(f"发送失败：{error_msg or '未知错误'}"))
