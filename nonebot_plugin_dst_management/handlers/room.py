"""
房间管理命令处理器

实现房间相关的所有命令。
"""

from nonebot import on_command
from nonebot.adapters.onebot.v11 import MessageEvent, Message
from nonebot.params import CommandArg
from typing import Dict, Any

from ..client.api_client import DSTApiClient
from ..utils.permission import check_admin
from ..utils.formatter import (
    format_room_list,
    format_room_detail,
    format_success,
    format_error,
    format_loading
)


def init(api_client: DSTApiClient):
    """
    初始化房间管理命令
    
    Args:
        api_client: DMP API 客户端实例
    """
    
    # 查看房间列表
    room_list = on_command("dst list", priority=10, block=True)
    
    @room_list.handle()
    async def handle_room_list(event: MessageEvent, args: Message = CommandArg()):
        """处理房间列表命令"""
        page_str = args.extract_plain_text().strip()
        page = int(page_str) if page_str.isdigit() else 1
        
        # 发送加载消息
        await room_list.send(await format_loading("获取房间列表..."))
        
        # 调用 API
        result = await api_client.get_room_list(page=page, page_size=10)
        
        if not result["success"]:
            await room_list.finish(await format_error(
                f"获取房间列表失败：{result.get('error', '未知错误')}"
            ))
        
        # 格式化并发送结果
        data = result["data"]
        rooms = data.get("rows", [])
        total = data.get("totalCount", 0)
        total_pages = max(1, (total + 9) // 10)
        
        message = await format_room_list(rooms, page, total_pages, total)
        await room_list.finish(message)
    
    # 查看房间详情
    room_info = on_command("dst info", priority=10, block=True)
    
    @room_info.handle()
    async def handle_room_info(event: MessageEvent, args: Message = CommandArg()):
        """处理房间详情命令"""
        room_id_str = args.extract_plain_text().strip()
        
        if not room_id_str.isdigit():
            await room_info.finish(await format_error(
                "请提供有效的房间ID：/dst info <房间ID>"
            ))
        
        room_id = int(room_id_str)
        
        # 发送加载消息
        await room_info.send(await format_loading("获取房间信息..."))
        
        # 获取房间信息
        room_result = await api_client.get_room_info(room_id)
        if not room_result["success"]:
            await room_info.finish(await format_error(
                f"获取房间信息失败：{room_result.get('error', '未知错误')}"
            ))
        
        # 获取世界列表
        worlds_result = await api_client.get_world_list(room_id)
        worlds = worlds_result.get("data", {}).get("rows", []) if worlds_result["success"] else []
        
        # 获取在线玩家
        players_result = await api_client.get_online_players(room_id)
        players = players_result.get("data", []) if players_result["success"] else []
        
        # 格式化并发送结果
        message = await format_room_detail(
            room_result["data"],
            worlds,
            players
        )
        await room_info.finish(message)
    
    # 启动房间
    room_start = on_command("dst start", priority=10, block=True)
    
    @room_start.handle()
    async def handle_room_start(event: MessageEvent, args: Message = CommandArg()):
        """处理启动房间命令"""
        # 权限检查
        if not await check_admin(event):
            await room_start.finish(await format_error("只有管理员才能执行此操作"))
        
        room_id_str = args.extract_plain_text().strip()
        
        if not room_id_str.isdigit():
            await room_start.finish(await format_error(
                "请提供有效的房间ID：/dst start <房间ID>"
            ))
        
        room_id = int(room_id_str)
        
        # 发送加载消息
        await room_start.send(await format_loading(f"正在启动房间 {room_id}..."))
        
        # 调用 API
        result = await api_client.activate_room(room_id)
        
        if result["success"]:
            await room_start.finish(await format_success(f"房间 {room_id} 启动成功"))
        else:
            await room_start.finish(await format_error(
                f"启动失败：{result.get('error', '未知错误')}"
            ))
    
    # 关闭房间
    room_stop = on_command("dst stop", priority=10, block=True)
    
    @room_stop.handle()
    async def handle_room_stop(event: MessageEvent, args: Message = CommandArg()):
        """处理关闭房间命令"""
        # 权限检查
        if not await check_admin(event):
            await room_stop.finish(await format_error("只有管理员才能执行此操作"))
        
        room_id_str = args.extract_plain_text().strip()
        
        if not room_id_str.isdigit():
            await room_stop.finish(await format_error(
                "请提供有效的房间ID：/dst stop <房间ID>"
            ))
        
        room_id = int(room_id_str)
        
        # 发送加载消息
        await room_stop.send(await format_loading(f"正在关闭房间 {room_id}..."))
        
        # 调用 API
        result = await api_client.deactivate_room(room_id)
        
        if result["success"]:
            await room_stop.finish(await format_success(f"房间 {room_id} 已关闭"))
        else:
            await room_stop.finish(await format_error(
                f"关闭失败：{result.get('error', '未知错误')}"
            ))
    
    # 重启房间
    room_restart = on_command("dst restart", priority=10, block=True)
    
    @room_restart.handle()
    async def handle_room_restart(event: MessageEvent, args: Message = CommandArg()):
        """处理重启房间命令"""
        # 权限检查
        if not await check_admin(event):
            await room_restart.finish(await format_error("只有管理员才能执行此操作"))
        
        room_id_str = args.extract_plain_text().strip()
        
        if not room_id_str.isdigit():
            await room_restart.finish(await format_error(
                "请提供有效的房间ID：/dst restart <房间ID>"
            ))
        
        room_id = int(room_id_str)
        
        # 发送加载消息
        await room_restart.send(await format_loading(f"正在重启房间 {room_id}..."))
        
        # 调用 API
        result = await api_client.restart_room(room_id)
        
        if result["success"]:
            await room_restart.finish(await format_success(f"房间 {room_id} 重启成功"))
        else:
            await room_restart.finish(await format_error(
                f"重启失败：{result.get('error', '未知错误')}"
            ))


__all__ = ["init"]
