"""
玩家管理命令处理器

实现玩家相关的所有命令。
"""

from nonebot import on_command
from nonebot.adapters.onebot.v11 import MessageEvent, Message
from nonebot.params import CommandArg

from ..client.api_client import DSTApiClient
from ..utils.permission import check_admin
from ..utils.formatter import (
    format_player_list,
    format_success,
    format_error,
    format_loading
)


def init(api_client: DSTApiClient):
    """
    初始化玩家管理命令
    
    Args:
        api_client: DMP API 客户端实例
    """
    
    # 查看在线玩家
    players_list = on_command("dst players", priority=10, block=True)
    
    @players_list.handle()
    async def handle_players_list(event: MessageEvent, args: Message = CommandArg()):
        """处理查看在线玩家命令"""
        room_id_str = args.extract_plain_text().strip()
        
        if not room_id_str.isdigit():
            await players_list.finish(await format_error(
                "请提供有效的房间ID：/dst players <房间ID>"
            ))
        
        room_id = int(room_id_str)
        
        # 发送加载消息
        await players_list.send(await format_loading("获取玩家列表..."))
        
        # 获取房间信息（用于房间名称）
        room_result = await api_client.get_room_info(room_id)
        if not room_result["success"]:
            await players_list.finish(await format_error(
                f"获取房间信息失败：{room_result.get('error', '未知错误')}"
            ))
        
        room_name = room_result["data"].get("gameName", f"房间{room_id}")
        
        # 获取在线玩家
        result = await api_client.get_online_players(room_id)
        
        if not result["success"]:
            await players_list.finish(await format_error(
                f"获取玩家列表失败：{result.get('error', '未知错误')}"
            ))
        
        players = result.get("data", [])
        message = await format_player_list(room_name, players)
        await players_list.finish(message)
    
    # 踢出玩家
    player_kick = on_command("dst kick", priority=10, block=True)
    
    @player_kick.handle()
    async def handle_player_kick(event: MessageEvent, args: Message = CommandArg()):
        """处理踢出玩家命令"""
        # 权限检查
        if not await check_admin(event):
            await player_kick.finish(await format_error("只有管理员才能执行此操作"))
        
        args_text = args.extract_plain_text().strip().split()
        
        if len(args_text) < 2:
            await player_kick.finish(await format_error(
                "用法：/dst kick <房间ID> <KU_ID>"
            ))
        
        room_id_str = args_text[0]
        ku_id = args_text[1]
        
        if not room_id_str.isdigit():
            await player_kick.finish(await format_error(
                "请提供有效的房间ID"
            ))
        
        room_id = int(room_id_str)
        
        # 发送加载消息
        await player_kick.send(await format_loading(f"正在踢出玩家 {ku_id}..."))
        
        # 更新玩家列表（添加到黑名单）
        result = await api_client.update_player_list(
            room_id,
            [ku_id],
            "blacklist",
            "add"
        )
        
        if result["success"]:
            await player_kick.finish(await format_success(
                f"玩家 {ku_id} 已踢出"
            ))
        else:
            await player_kick.finish(await format_error(
                f"踢出失败：{result.get('error', '未知错误')}"
            ))


__all__ = ["init"]
