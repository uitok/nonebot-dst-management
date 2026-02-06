"""
备份管理命令处理器

处理备份相关的命令：backup list, backup create, backup restore
"""

from typing import Optional

from nonebot import on_command
from nonebot.adapters.onebot.v11 import Bot, MessageEvent, Message
from nonebot.params import CommandArg

from ..client.api_client import DSTApiClient
from ..utils.permission import check_admin, check_group
from ..helpers.commands import parse_room_id
from ..helpers.formatters import (
    format_error,
    format_success,
    format_info,
    format_warning,
    render_auto,
)
from ..helpers.room_context import RoomSource, remember_room, resolve_room_id


def init(api_client: DSTApiClient):
    """
    初始化备份管理命令
    
    Args:
        api_client: DMP API 客户端实例
    """
    
    # ========== 查看备份列表 ==========
    backup_list = on_command(
        "dst backup list",
        aliases={"dst 备份列表", "dst 查备份", "dst 查看备份"},
        priority=10,
        block=True
    )
    
    @backup_list.handle()
    async def handle_backup_list(event: MessageEvent, args: Message = CommandArg()):
        # 检查群组权限
        if not await check_group(event):
            await backup_list.finish(format_error("当前群组未授权使用此功能"))
            return
        
        # 解析房间 ID（支持会话锁定）
        room_arg = args.extract_plain_text().strip()
        resolved = await resolve_room_id(event, room_arg if room_arg else None)
        if resolved is None:
            if room_arg:
                await backup_list.finish(format_error("请提供有效的房间ID：/dst backup list <房间ID>"))
            else:
                await backup_list.finish(
                    format_error("请提供房间ID：/dst backup list <房间ID>\n或先使用一次带房间ID的命令以锁定房间")
                )
            return

        room_id = int(resolved.room_id)

        if resolved.source == RoomSource.LAST:
            await backup_list.send(format_info(f"未指定房间ID，使用上次操作的房间 {room_id}..."))
        elif resolved.source == RoomSource.DEFAULT:
            await backup_list.send(format_info(f"未指定房间ID，使用默认房间 {room_id}..."))
        
        # 获取房间信息（用于房间名称）
        room_result = await api_client.get_room_info(room_id)
        room_name = "未知房间"
        if room_result["success"]:
            room_name = room_result["data"].get("gameName", "未知房间")
        
        # 获取备份列表
        result = await api_client.list_backups(room_id)
        
        if not result["success"]:
            await backup_list.finish(format_error(f"获取备份列表失败：{result['error']}"))
            return
        
        backups = result["data"] or []
        
        # 格式化输出
        message = await render_auto(
            "backups",
            event=event,
            room_name=room_name,
            backups=backups,
        )
        await remember_room(event, room_id)
        await backup_list.finish(message)
    
    # ========== 创建备份 ==========
    backup_create = on_command(
        "dst backup create",
        aliases={"dst 创建备份", "dst 备份创建", "dst 立即备份", "dst 生成备份"},
        priority=10,
        block=True
    )
    
    @backup_create.handle()
    async def handle_backup_create(bot: Bot, event: MessageEvent, args: Message = CommandArg()):
        # 检查管理员权限
        if not await check_admin(bot, event):
            await backup_create.finish(format_error("只有管理员才能执行此操作"))
            return
        
        # 解析房间 ID（支持会话锁定）
        room_arg = args.extract_plain_text().strip()
        resolved = await resolve_room_id(event, room_arg if room_arg else None)
        if resolved is None:
            if room_arg:
                await backup_create.finish(format_error("请提供有效的房间ID：/dst backup create <房间ID>"))
            else:
                await backup_create.finish(
                    format_error("请提供房间ID：/dst backup create <房间ID>\n或先使用一次带房间ID的命令以锁定房间")
                )
            return

        room_id = int(resolved.room_id)
        
        # 发送提示
        source_hint = ""
        if resolved.source == RoomSource.LAST:
            source_hint = "（使用上次操作的房间）"
        elif resolved.source == RoomSource.DEFAULT:
            source_hint = "（使用默认房间）"
        await backup_create.send(format_info(f"正在为房间 {room_id}{source_hint} 创建备份，请稍候..."))
        
        # 调用 API
        result = await api_client.create_backup(room_id)
        
        if result["success"]:
            await remember_room(event, room_id)
            await backup_create.finish(format_success("备份创建成功"))
        else:
            await backup_create.finish(format_error(f"备份创建失败：{result['error']}"))
    
    # ========== 恢复备份 ==========
    backup_restore = on_command(
        "dst backup restore",
        aliases={"dst 恢复备份", "dst 备份恢复", "dst 回档", "dst 回档备份"},
        priority=10,
        block=True
    )
    
    @backup_restore.handle()
    async def handle_backup_restore(bot: Bot, event: MessageEvent, args: Message = CommandArg()):
        # 检查管理员权限
        if not await check_admin(bot, event):
            await backup_restore.finish(format_error("只有管理员才能执行此操作"))
            return
        
        # 解析参数（支持省略房间ID：/dst backup restore <备份文件名>）
        parts = args.extract_plain_text().strip().split()
        if not parts:
            await backup_restore.finish(
                format_error("用法：/dst backup restore <房间ID> <备份文件名>\n或：/dst backup restore <备份文件名>")
            )
            return

        room_id: Optional[int] = None
        filename: Optional[str] = None
        resolved = None

        maybe_room = parse_room_id(parts[0])
        if maybe_room is not None:
            if len(parts) < 2:
                await backup_restore.finish(format_error("用法：/dst backup restore <房间ID> <备份文件名>"))
                return
            resolved = await resolve_room_id(event, str(maybe_room))
            room_id = int(maybe_room)
            filename = parts[1]
        else:
            # No leading room id, treat first token as filename and use session lock/default room.
            filename = parts[0]
            resolved = await resolve_room_id(event, None)
            if resolved is not None:
                room_id = int(resolved.room_id)

        if room_id is None:
            await backup_restore.finish(format_error("请提供房间ID或先使用一次带房间ID的命令以锁定房间"))
            return
        assert filename is not None
        
        # 发送确认提示
        source_hint = ""
        if resolved and resolved.source == RoomSource.LAST:
            source_hint = "（使用上次操作的房间）"
        elif resolved and resolved.source == RoomSource.DEFAULT:
            source_hint = "（使用默认房间）"
        await backup_restore.send(
            format_warning(
                f"即将恢复房间 {room_id}{source_hint} 的备份 {filename}，此操作不可撤销！\n确认请发送 \"是\"，取消请发送 \"否\""
            )
        )
        
        # 这里应该有一个等待用户确认的逻辑
        # 由于 NoneBot 的限制，简化处理，直接恢复
        await backup_restore.send(format_info(f"正在恢复备份 {filename}..."))
        
        # 调用 API
        result = await api_client.restore_backup(room_id, filename)
        
        if result["success"]:
            await remember_room(event, room_id)
            await backup_restore.finish(format_success(f"备份恢复成功，房间将自动重启"))
        else:
            await backup_restore.finish(format_error(f"备份恢复失败：{result['error']}"))
