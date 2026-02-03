"""
备份管理命令处理器

实现备份相关的所有命令。
"""

from nonebot import on_command
from nonebot.adapters.onebot.v11 import MessageEvent, Message
from nonebot.params import CommandArg

from ..client.api_client import DSTApiClient
from ..utils.permission import check_admin
from ..utils.formatter import (
    format_backup_list,
    format_success,
    format_error,
    format_loading
)


def init(api_client: DSTApiClient):
    """
    初始化备份管理命令
    
    Args:
        api_client: DMP API 客户端实例
    """
    
    # 查看备份列表
    backup_list = on_command("dst backup list", priority=10, block=True)
    
    @backup_list.handle()
    async def handle_backup_list(event: MessageEvent, args: Message = CommandArg()):
        """处理查看备份列表命令"""
        # 提取房间ID（去掉前面的命令部分）
        room_id_str = args.extract_plain_text().strip()
        
        if not room_id_str.isdigit():
            await backup_list.finish(await format_error(
                "请提供有效的房间ID：/dst backup list <房间ID>"
            ))
        
        room_id = int(room_id_str)
        
        # 发送加载消息
        await backup_list.send(await format_loading("获取备份列表..."))
        
        # 获取房间信息（用于房间名称）
        room_result = await api_client.get_room_info(room_id)
        if not room_result["success"]:
            await backup_list.finish(await format_error(
                f"获取房间信息失败：{room_result.get('error', '未知错误')}"
            ))
        
        room_name = room_result["data"].get("gameName", f"房间{room_id}")
        
        # 获取备份列表
        result = await api_client.list_backups(room_id)
        
        if not result["success"]:
            await backup_list.finish(await format_error(
                f"获取备份列表失败：{result.get('error', '未知错误')}"
            ))
        
        backups = result.get("data", [])
        message = await format_backup_list(room_name, backups)
        await backup_list.finish(message)
    
    # 创建备份
    backup_create = on_command("dst backup create", priority=10, block=True)
    
    @backup_create.handle()
    async def handle_backup_create(event: MessageEvent, args: Message = CommandArg()):
        """处理创建备份命令"""
        # 权限检查
        if not await check_admin(event):
            await backup_create.finish(await format_error("只有管理员才能执行此操作"))
        
        room_id_str = args.extract_plain_text().strip()
        
        if not room_id_str.isdigit():
            await backup_create.finish(await format_error(
                "请提供有效的房间ID：/dst backup create <房间ID>"
            ))
        
        room_id = int(room_id_str)
        
        # 发送加载消息
        await backup_create.send(await format_loading(f"正在为房间 {room_id} 创建备份..."))
        
        # 调用 API
        result = await api_client.create_backup(room_id)
        
        if result["success"]:
            await backup_create.finish(await format_success(
                f"房间 {room_id} 备份创建成功"
            ))
        else:
            await backup_create.finish(await format_error(
                f"创建备份失败：{result.get('error', '未知错误')}"
            ))


__all__ = ["init"]
