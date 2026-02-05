"""
玩家管理命令处理器

处理玩家相关的命令：players, kick
"""

from nonebot import on_command
from nonebot.adapters.onebot.v11 import Bot, MessageEvent, Message
from nonebot.params import CommandArg

from ..client.api_client import DSTApiClient
from ..utils.permission import check_admin, check_group
from ..utils.formatter import (
    format_players,
    format_error,
    format_success,
    format_info,
)


def init(api_client: DSTApiClient):
    """
    初始化玩家管理命令
    
    Args:
        api_client: DMP API 客户端实例
    """
    
    # ========== 查看在线玩家 ==========
    players_cmd = on_command(
        "dst players",
        aliases={"dst 玩家列表", "dst 在线玩家"},
        priority=10,
        block=True
    )
    
    @players_cmd.handle()
    async def handle_players(event: MessageEvent, args: Message = CommandArg()):
        # 检查群组权限
        if not await check_group(event):
            await players_cmd.finish(format_error("当前群组未授权使用此功能"))
            return
        
        # 解析房间 ID
        room_id_str = args.extract_plain_text().strip()
        if not room_id_str.isdigit():
            await players_cmd.finish(format_error("请提供有效的房间ID：/dst players <房间ID>"))
            return
        
        room_id = int(room_id_str)
        
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
        message = format_players(room_name, players)
        await players_cmd.finish(message)
    
    # ========== 踢出玩家 ==========
    kick_cmd = on_command(
        "dst kick",
        aliases={"dst 踢出玩家", "dst 踢人"},
        priority=10,
        block=True
    )
    
    @kick_cmd.handle()
    async def handle_kick(bot: Bot, event: MessageEvent, args: Message = CommandArg()):
        # 检查管理员权限
        if not await check_admin(bot, event):
            await kick_cmd.finish(format_error("只有管理员才能执行此操作"))
            return
        
        # 解析参数
        arg_parts = args.extract_plain_text().strip().split()
        if len(arg_parts) < 2:
            await kick_cmd.finish(format_error("用法：/dst kick <房间ID> <KU_ID>"))
            return
        
        room_id_str = arg_parts[0]
        ku_id = arg_parts[1]
        
        if not room_id_str.isdigit():
            await kick_cmd.finish(format_error("请提供有效的房间ID"))
            return
        
        room_id = int(room_id_str)
        
        # 发送提示
        await kick_cmd.send(format_info(f"正在踢出玩家 {ku_id}..."))
        
        # 使用控制台命令踢人
        # c_kick(userid) - 踢出指定玩家
        result = await api_client.execute_console_command(
            room_id,
            None,  # 所有世界
            f'c_kick("{ku_id}")'
        )
        
        if result["success"]:
            await kick_cmd.finish(format_success(f"玩家 {ku_id} 已踢出"))
        else:
            await kick_cmd.finish(format_error(f"踢出失败：{result['error']}"))
