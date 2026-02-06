"""
房间管理命令处理器

处理房间相关的命令：list, info, start, stop, restart
"""

from nonebot import on_command
from nonebot.adapters.onebot.v11 import Bot, MessageEvent, Message
from nonebot.params import CommandArg

from ..client.api_client import DSTApiClient
from ..services.monitors.sign_monitor import get_sign_monitor
from ..utils.permission import check_admin, check_group
from ..helpers.formatters import (
    format_error,
    format_success,
    format_info,
    status_badge,
    render_auto,
)
from ..helpers.room_context import RoomSource, remember_room, resolve_room_id


def init(api_client: DSTApiClient):
    """
    初始化房间管理命令
    
    Args:
        api_client: DMP API 客户端实例
    """
    
    # ========== 查看房间列表 ==========
    room_list = on_command(
        "dst list",
        aliases={"dst 房间列表", "dst 列表", "dst 查看房间", "dst 查房间", "dst 查房列表"},
        priority=10,
        block=True
    )
    
    @room_list.handle()
    async def handle_room_list(event: MessageEvent, args: Message = CommandArg()):
        # 检查群组权限
        if not await check_group(event):
            await room_list.finish(format_error("当前群组未授权使用此功能"))
            return
        
        # 解析页码
        page_str = args.extract_plain_text().strip()
        page = int(page_str) if page_str.isdigit() else 1
        
        # 调用 API
        result = await api_client.get_room_list(page=page, page_size=10)
        
        if not result["success"]:
            await room_list.finish(format_error(f"获取房间列表失败：{result['error']}"))
            return
        
        # 格式化输出
        data = result["data"]
        rooms = data.get("rows", [])
        total = data.get("totalCount", 0)
        total_pages = max(1, (total + 9) // 10)
        
        message = await render_auto(
            "room_list",
            event=event,
            rooms=rooms,
            page=page,
            total_pages=total_pages,
            total=total,
        )
        await room_list.finish(message)
    
    # ========== 查看房间详情 ==========
    room_info = on_command(
        "dst info",
        aliases={"dst 房间详情", "dst 详情", "dst 房间信息", "dst 查房", "dst 查房间详情", "dst 查详情"},
        priority=10,
        block=True
    )
    
    @room_info.handle()
    async def handle_room_info(event: MessageEvent, args: Message = CommandArg()):
        # 检查群组权限
        if not await check_group(event):
            await room_info.finish(format_error("当前群组未授权使用此功能"))
            return
        
        # 解析房间 ID（支持会话锁定）
        room_arg = args.extract_plain_text().strip()
        resolved = await resolve_room_id(event, room_arg if room_arg else None)
        if resolved is None:
            if room_arg:
                await room_info.finish(format_error("请提供有效的房间ID：/dst info <房间ID>"))
            else:
                await room_info.finish(format_error("请提供房间ID：/dst info <房间ID>\n或先使用一次带房间ID的命令以锁定房间"))
            return

        room_id = int(resolved.room_id)

        if resolved.source == RoomSource.LAST:
            await room_info.send(format_info(f"未指定房间ID，使用上次操作的房间 {room_id}..."))
        elif resolved.source == RoomSource.DEFAULT:
            await room_info.send(format_info(f"未指定房间ID，使用默认房间 {room_id}..."))
        
        # 获取房间信息
        room_result = await api_client.get_room_info(room_id)
        if not room_result["success"]:
            await room_info.finish(format_error(f"获取房间信息失败：{room_result['error']}"))
            return
        
        # 获取世界列表
        worlds_result = await api_client.get_world_list(room_id)
        worlds = []
        if worlds_result["success"]:
            worlds = worlds_result["data"].get("rows", [])
        
        # 获取在线玩家
        players_result = await api_client.get_online_players(room_id)
        players = []
        if players_result["success"]:
            players = players_result["data"] or []

        # ✨ 触发签到奖励检查
        monitor = get_sign_monitor()
        if monitor:
            try:
                await monitor.check_room_pending_rewards(room_id)
            except Exception:
                pass
        
        # 格式化输出
        message = await render_auto(
            "room_detail",
            event=event,
            room=room_result["data"],
            worlds=worlds,
            players=players,
        )
        await remember_room(event, room_id)
        await room_info.finish(message)
    
    # ========== 启动房间 ==========
    room_start = on_command(
        "dst start",
        aliases={"dst 启动", "dst 启动房间", "dst 开房", "dst 开启房间", "dst 开服"},
        priority=10,
        block=True,
    )
    
    @room_start.handle()
    async def handle_room_start(bot: Bot, event: MessageEvent, args: Message = CommandArg()):
        # 检查管理员权限
        if not await check_admin(bot, event):
            await room_start.finish(format_error("只有管理员才能执行此操作"))
            return
        
        # 解析房间 ID（支持会话锁定）
        room_arg = args.extract_plain_text().strip()
        resolved = await resolve_room_id(event, room_arg if room_arg else None)
        if resolved is None:
            if room_arg:
                await room_start.finish(format_error("请提供有效的房间ID：/dst start <房间ID>"))
            else:
                await room_start.finish(format_error("请提供房间ID：/dst start <房间ID>\n或先使用一次带房间ID的命令以锁定房间"))
            return

        room_id = int(resolved.room_id)
        
        # 发送提示
        source_hint = ""
        if resolved.source == RoomSource.LAST:
            source_hint = "（使用上次操作的房间）"
        elif resolved.source == RoomSource.DEFAULT:
            source_hint = "（使用默认房间）"
        await room_start.send(format_info(f"正在启动房间 {room_id}{source_hint}..."))
        
        # 调用 API
        result = await api_client.activate_room(room_id)
        
        if result["success"]:
            await remember_room(event, room_id)
            await room_start.finish(format_success(f"房间 {room_id} 启动成功 {status_badge(True)}"))
        else:
            await room_start.finish(format_error(f"启动失败：{result['error']}"))
    
    # ========== 关闭房间 ==========
    room_stop = on_command(
        "dst stop",
        aliases={"dst 停止", "dst 停止房间", "dst 关闭", "dst 关闭房间", "dst 关房", "dst 关服"},
        priority=10,
        block=True,
    )
    
    @room_stop.handle()
    async def handle_room_stop(bot: Bot, event: MessageEvent, args: Message = CommandArg()):
        # 检查管理员权限
        if not await check_admin(bot, event):
            await room_stop.finish(format_error("只有管理员才能执行此操作"))
            return
        
        # 解析房间 ID（支持会话锁定）
        room_arg = args.extract_plain_text().strip()
        resolved = await resolve_room_id(event, room_arg if room_arg else None)
        if resolved is None:
            if room_arg:
                await room_stop.finish(format_error("请提供有效的房间ID：/dst stop <房间ID>"))
            else:
                await room_stop.finish(format_error("请提供房间ID：/dst stop <房间ID>\n或先使用一次带房间ID的命令以锁定房间"))
            return

        room_id = int(resolved.room_id)
        
        # 发送提示
        source_hint = ""
        if resolved.source == RoomSource.LAST:
            source_hint = "（使用上次操作的房间）"
        elif resolved.source == RoomSource.DEFAULT:
            source_hint = "（使用默认房间）"
        await room_stop.send(format_info(f"正在关闭房间 {room_id}{source_hint}..."))
        
        # 调用 API
        result = await api_client.deactivate_room(room_id)
        
        if result["success"]:
            await remember_room(event, room_id)
            await room_stop.finish(format_success(f"房间 {room_id} 已关闭 {status_badge(False)}"))
        else:
            await room_stop.finish(format_error(f"关闭失败：{result['error']}"))
    
    # ========== 重启房间 ==========
    room_restart = on_command(
        "dst restart",
        aliases={"dst 重启", "dst 重启房间", "dst 重开房间", "dst 一键维护", "dst 维护"},
        priority=10,
        block=True,
    )
    
    @room_restart.handle()
    async def handle_room_restart(bot: Bot, event: MessageEvent, args: Message = CommandArg()):
        # 检查管理员权限
        if not await check_admin(bot, event):
            await room_restart.finish(format_error("只有管理员才能执行此操作"))
            return
        
        # 解析房间 ID（支持会话锁定）
        room_arg = args.extract_plain_text().strip()
        resolved = await resolve_room_id(event, room_arg if room_arg else None)
        if resolved is None:
            if room_arg:
                await room_restart.finish(format_error("请提供有效的房间ID：/dst restart <房间ID>"))
            else:
                await room_restart.finish(format_error("请提供房间ID：/dst restart <房间ID>\n或先使用一次带房间ID的命令以锁定房间"))
            return

        room_id = int(resolved.room_id)
        
        # 发送提示
        source_hint = ""
        if resolved.source == RoomSource.LAST:
            source_hint = "（使用上次操作的房间）"
        elif resolved.source == RoomSource.DEFAULT:
            source_hint = "（使用默认房间）"
        await room_restart.send(format_info(f"正在重启房间 {room_id}{source_hint}..."))
        
        # 调用 API
        result = await api_client.restart_room(room_id)
        
        if result["success"]:
            await remember_room(event, room_id)
            await room_restart.finish(format_success(f"房间 {room_id} 重启成功 {status_badge(True)}"))
        else:
            await room_restart.finish(format_error(f"重启失败：{result['error']}"))
