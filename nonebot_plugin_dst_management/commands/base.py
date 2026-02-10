"""
Alconna 命令基础框架

提供基于 Alconna 的命令构造器和权限管理。
"""

from __future__ import annotations

from typing import Any, Callable, Optional

from arclet.alconna import Alconna, Args, CommandMeta, Option, Subcommand
from nonebot import Bot
from nonebot.internal.adapter import Event

from ..utils.permission import (
    check_admin,
    check_group,
    check_permission,
    PermissionLevel,
    PermissionChecker,
    USER_PERMISSION,
    ADMIN_PERMISSION,
    SUPER_PERMISSION,
    make_permission_rule,
)


class DSTCommand(Alconna):
    """DST 管理命令基类"""

    def __init__(
        self,
        command: str,
        *args: Any,
        permission_level: str = "user",
        **kwargs: Any,
    ) -> None:
        """
        初始化 DST 命令

        Args:
            command: 命令路径
            permission_level: 权限等级 (user/admin/super)
            *args: 其他位置参数
            **kwargs: 其他关键字参数
        """
        self.permission_level = permission_level

        # 设置命令元数据
        meta = kwargs.pop("meta", None) or CommandMeta(
            description=kwargs.pop("description", ""),
            example=kwargs.pop("example", ""),
            compact=True,
        )

        super().__init__(command, *args, meta=meta, **kwargs)


class DSTPermissionChecker:
    """DST 权限检查器"""

    @staticmethod
    async def check(
        bot: Bot,
        event: Event,
        level: str = "user",
    ) -> bool:
        """
        检查权限

        Args:
            bot: Bot 实例
            event: 消息事件
            level: 权限等级

        Returns:
            bool: 是否有权限
        """
        return await check_permission(bot, event, level)

    @staticmethod
    def make_permission_handler(level: str = "user") -> Callable[[Bot, Event], Any]:
        """
        创建权限处理函数

        Args:
            level: 权限等级

        Returns:
            权限检查函数
        """
        async def handler(bot: Bot, event: Event) -> bool:
            return await DSTPermissionChecker.check(bot, event, level)

        return handler


def require_admin(func: Callable) -> Callable:
    """
    装饰器：要求管理员权限

    Args:
        func: 原函数

    Returns:
        包装后的函数
    """
    async def wrapper(bot: Bot, event: Event, *args: Any, **kwargs: Any) -> Any:
        if not await check_admin(bot, event):
            from ..helpers.formatters import format_error
            # 这里需要通过某种方式返回错误消息
            # 在 Alconna 中可以使用 finish 或 send
            raise PermissionError("只有管理员才能执行此操作")
        return await func(bot, event, *args, **kwargs)

    return wrapper


def require_group(func: Callable) -> Callable:
    """
    装饰器：要求群组权限

    Args:
        func: 原函数

    Returns:
        包装后的函数
    """
    async def wrapper(bot: Bot, event: Event, *args: Any, **kwargs: Any) -> Any:
        if not await check_group(event):
            from ..helpers.formatters import format_error
            raise PermissionError("当前群组未授权使用此功能")
        return await func(bot, event, *args, **kwargs)

    return wrapper


__all__ = [
    "DSTCommand",
    "DSTPermissionChecker",
    "PermissionLevel",
    "PermissionChecker",
    "USER_PERMISSION",
    "ADMIN_PERMISSION",
    "SUPER_PERMISSION",
    "make_permission_rule",
    "require_admin",
    "require_group",
]
