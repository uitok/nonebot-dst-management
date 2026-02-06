"""
玩家管理命令处理器

处理玩家相关的命令：players, kick
"""

from typing import Optional

from nonebot import on_command
from nonebot.adapters.onebot.v11 import Bot, MessageEvent, Message
from nonebot.params import CommandArg

from ..client.api_client import DSTApiClient
from ..utils.permission import check_admin, check_group
from ..helpers.formatters import (
    format_error,
    format_success,
    format_info,
    render_auto,
)
from ..helpers.commands import parse_room_id
from ..helpers.room_context import RoomSource, remember_room, resolve_room_id


def init(api_client: DSTApiClient):
    """
    初始化玩家管理命令
    
    Args:
        api_client: DMP API 客户端实例
    """
    
    # ========== 查看在线玩家 ==========
    players_cmd = on_command(
        "dst players",
        aliases={"dst 玩家列表", "dst 在线玩家", "dst 查玩家", "dst 查看玩家", "dst 谁在玩", "dst 谁在玩呢", "dst 谁在线"},
        priority=10,
        block=True
    )
    
    @players_cmd.handle()
    async def handle_players(event: MessageEvent, args: Message = CommandArg()):
        # 检查群组权限
        if not await check_group(event):
            await players_cmd.finish(format_error("当前群组未授权使用此功能"))
            return
        
        # 解析房间 ID（支持会话锁定）
        room_arg = args.extract_plain_text().strip()
        resolved = await resolve_room_id(event, room_arg if room_arg else None)
        if resolved is None:
            if room_arg:
                await players_cmd.finish(format_error("请提供有效的房间ID：/dst players <房间ID>"))
            else:
                await players_cmd.finish(format_error("请提供房间ID：/dst players <房间ID>\n或先使用一次带房间ID的命令以锁定房间"))
            return

        room_id = int(resolved.room_id)

        if resolved.source == RoomSource.LAST:
            await players_cmd.send(format_info(f"未指定房间ID，使用上次操作的房间 {room_id}..."))
        elif resolved.source == RoomSource.DEFAULT:
            await players_cmd.send(format_info(f"未指定房间ID，使用默认房间 {room_id}..."))
        
        # 获取房间信息（用于房间名称）
        room_result = await api_client.get_room_info(room_id)
        room_name = "未知房间"
        if room_result["success"]:
            room_name = room_result["data"].get("gameName", "未知房间")
        
        # 获取在线玩家
        result = await api_client.get_online_players(room_id)
        
        if not result["success"]:
            await players_cmd.finish(format_error(f"获取玩家列表失败：{result['error']}"))
            return
        
        players = result["data"] or []
        
        # 格式化输出
        message = await render_auto(
            "players",
            event=event,
            room_name=room_name,
            players=players,
        )
        await remember_room(event, room_id)
        await players_cmd.finish(message)
    
    # ========== 踢出玩家 ==========
    kick_cmd = on_command(
        "dst kick",
        aliases={"dst 踢出玩家", "dst 踢人", "dst 踢出", "dst 踢玩家", "dst 踢走"},
        priority=10,
        block=True
    )
    
    @kick_cmd.handle()
    async def handle_kick(bot: Bot, event: MessageEvent, args: Message = CommandArg()):
        # 检查管理员权限
        if not await check_admin(bot, event):
            await kick_cmd.finish(format_error("只有管理员才能执行此操作"))
            return
        
        # 解析参数（支持省略房间ID：/dst kick <KU_ID>）
        raw_parts = args.extract_plain_text().strip().split()
        if not raw_parts:
            await kick_cmd.finish(format_error("用法：/dst kick <房间ID> <KU_ID>\n或：/dst kick <KU_ID>"))
            return

        room_id: Optional[int] = None
        ku_id: Optional[str] = None
        resolved = None

        maybe_room = parse_room_id(raw_parts[0])
        if maybe_room is not None:
            if len(raw_parts) < 2:
                await kick_cmd.finish(format_error("用法：/dst kick <房间ID> <KU_ID>"))
                return
            resolved = await resolve_room_id(event, str(maybe_room))
            room_id = int(maybe_room)
            ku_id = raw_parts[1]
        else:
            # No leading room id, treat first token as KU_ID and use session lock/default room.
            ku_id = raw_parts[0]
            resolved = await resolve_room_id(event, None)
            if resolved is not None:
                room_id = int(resolved.room_id)

        if room_id is None:
            await kick_cmd.finish(format_error("请提供房间ID或先使用一次带房间ID的命令以锁定房间"))
            return
        assert ku_id is not None
        
        # 发送提示
        source_hint = ""
        if resolved and resolved.source == RoomSource.LAST:
            source_hint = "（使用上次操作的房间）"
        elif resolved and resolved.source == RoomSource.DEFAULT:
            source_hint = "（使用默认房间）"
        await kick_cmd.send(format_info(f"正在踢出玩家 {ku_id}... (房间 {room_id}{source_hint})"))
        
        # 使用控制台命令踢人
        # c_kick(userid) - 踢出指定玩家
        result = await api_client.execute_console_command(
            room_id,
            None,  # 所有世界
            f'c_kick("{ku_id}")'
        )
        
        if result["success"]:
            await remember_room(event, room_id)
            await kick_cmd.finish(format_success(f"玩家 {ku_id} 已踢出"))
        else:
            await kick_cmd.finish(format_error(f"踢出失败：{result['error']}"))
