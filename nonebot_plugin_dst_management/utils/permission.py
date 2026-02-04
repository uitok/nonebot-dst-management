"""
权限管理工具

提供命令权限检查功能。
"""

from nonebot.adapters.onebot.v11 import Bot, MessageEvent, GroupMessageEvent
from nonebot.permission import SUPERUSER

from ..config import get_dst_config


async def check_admin(bot: Bot, event: MessageEvent) -> bool:
    """
    检查用户是否是管理员
    
    Args:
        bot: Bot 实例
        event: 消息事件
        
    Returns:
        bool: 是否是管理员
    """
    config = get_dst_config()
    user_id = str(event.user_id)
    
    # 检查是否在管理员列表中
    if any(str(uid) == user_id for uid in config.dst_admin_users):
        return True
    
    # 使用 NoneBot 权限系统检查超级用户
    if await SUPERUSER(bot, event):
        return True
    
    return False


async def check_group(event: MessageEvent) -> bool:
    """
    检查是否在允许的群组中
    
    Args:
        event: 消息事件
        
    Returns:
        bool: 是否在允许的群组中
    """
    # 如果不是群消息，返回 False
    if not isinstance(event, GroupMessageEvent):
        return False
    
    group_id = event.group_id
    config = get_dst_config()
    
    # 如果允许列表为空，则允许所有群组
    if not config.dst_admin_groups:
        return True
    
    return group_id in config.dst_admin_groups


async def check_permission(bot: Bot, event: MessageEvent, level: str = "user") -> bool:
    """
    检查用户权限等级
    
    Args:
        bot: Bot 实例
        event: 消息事件
        level: 权限等级（user/admin/super）
        
    Returns:
        bool: 是否有权限
    """
    if level == "user":
        # 所有用户都有权限
        return await check_group(event)
    
    if level == "admin":
        # 需要管理员权限
        return await check_admin(bot, event) and await check_group(event)
    
    if level == "super":
        # 需要超级用户权限
        return await SUPERUSER(bot, event)
    
    return False


__all__ = ["check_admin", "check_group", "check_permission"]
