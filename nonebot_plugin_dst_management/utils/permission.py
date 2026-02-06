"""
权限管理工具

提供命令权限检查功能。
"""

from __future__ import annotations

from typing import Any, Optional

from nonebot.permission import SUPERUSER

from ..config import get_dst_config


def _extract_user_id(event: Any) -> Optional[str]:
    if event is None:
        return None
    get_user_id = getattr(event, "get_user_id", None)
    if callable(get_user_id):
        try:
            value = get_user_id()
            return str(value) if value else None
        except Exception:
            pass
    user_id = getattr(event, "user_id", None)
    return str(user_id) if user_id is not None else None


def _extract_group_id(event: Any) -> Optional[str]:
    if event is None:
        return None
    # OneBot v11
    if (group_id := getattr(event, "group_id", None)) is not None:
        return str(group_id)
    # Official QQ adapter (best-effort)
    if (group_openid := getattr(event, "group_openid", None)) is not None:
        return str(group_openid)
    if (guild_id := getattr(event, "guild_id", None)) is not None and (
        channel_id := getattr(event, "channel_id", None)
    ) is not None:
        return f"{guild_id}:{channel_id}"
    return None


async def check_admin(bot: Any, event: Any) -> bool:
    """
    检查用户是否是管理员
    
    Args:
        bot: Bot 实例
        event: 消息事件
        
    Returns:
        bool: 是否是管理员
    """
    config = get_dst_config()
    user_id = _extract_user_id(event)
    
    # 检查是否在管理员列表中
    if user_id and any(str(uid) == user_id for uid in config.dst_admin_users):
        return True
    
    # 使用 NoneBot 权限系统检查超级用户
    try:
        if await SUPERUSER(bot, event):
            return True
    except Exception:
        pass
    
    return False


async def check_group(event: Any) -> bool:
    """
    检查是否在允许的群组中
    
    Args:
        event: 消息事件
        
    Returns:
        bool: 是否在允许的群组中
    """
    group_id_raw = _extract_group_id(event)
    if group_id_raw is None:
        return False

    # Best-effort numeric group id (OneBot). For other adapters, group id may be a string.
    group_id_int: Optional[int]
    try:
        group_id_int = int(group_id_raw)
    except Exception:
        group_id_int = None

    config = get_dst_config()
    
    # 如果允许列表为空，则允许所有群组
    if not config.dst_admin_groups:
        return True

    if group_id_int is None:
        # Config list is numeric, but the current adapter/group id isn't.
        return False

    return group_id_int in config.dst_admin_groups


async def check_permission(bot: Any, event: Any, level: str = "user") -> bool:
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
