"""
Alconna 命令注册器

提供命令注册和分发功能，将 Alconna 命令与 NoneBot 事件处理连接。
"""

from __future__ import annotations

from typing import Any, Callable, Dict, List, Optional, Tuple

from arclet.alconna import Alconna
from nonebot import on_command
from nonebot.plugin import Plugin
from nonebot.rule import Rule
from nonebot.internal.adapter import Event
from nonebot.internal.adapter.bot import Bot

from ..utils.permission import check_permission
from .base import DSTPermissionChecker


class CommandRegistry:
    """
    ��令注册器

    管理所有 Alconna 命令的注册和分发
    """

    def __init__(self) -> None:
        """初始化命令注册器"""
        self._commands: Dict[str, Alconna] = {}
        self._handlers: Dict[str, Callable] = {}
        self._permissions: Dict[str, str] = {}

    def register(
        self,
        command: Alconna,
        handler: Callable,
        permission_level: str = "user",
    ) -> None:
        """
        注册命令

        Args:
            command: Alconna 命令实例
            handler: 命令处理函数
            permission_level: 权限等级
        """
        command_path = str(command.path)
        self._commands[command_path] = command
        self._handlers[command_path] = handler
        self._permissions[command_path] = permission_level

    def get_command(self, path: str) -> Optional[Alconna]:
        """获取命令"""
        return self._commands.get(path)

    def get_handler(self, path: str) -> Optional[Callable]:
        """获取处理函数"""
        return self._handlers.get(path)

    def get_permission(self, path: str) -> str:
        """获取权限等级"""
        return self._permissions.get(path, "user")

    def list_commands(self) -> List[Tuple[str, Alconna, str]]:
        """列出所有命令"""
        return [
            (path, cmd, self._permissions[path])
            for path, cmd in self._commands.items()
        ]


# 全局注册器实例
_registry: Optional[CommandRegistry] = None


def get_registry() -> CommandRegistry:
    """获取全局命令注册器"""
    global _registry
    if _registry is None:
        _registry = CommandRegistry()
    return _registry


def register_alconna_command(
    command: Alconna,
    handler: Callable,
    permission_level: str = "user",
) -> None:
    """
    注册 Alconna 命令到 NoneBot

    Args:
        command: Alconna 命令实例
        handler: 命令处理函数
        permission_level: 权限等级
    """
    registry = get_registry()
    registry.register(command, handler, permission_level)

    # 创建权限检查规则
    async def permission_rule(bot: Bot, event: Event) -> bool:
        return await check_permission(bot, event, permission_level)

    # 注册到 NoneBot
    cmd_name = str(command.path).split()[0] if command.path else str(command.path)
    nonebot_cmd = on_command(
        cmd_name,
        rule=Rule(permission_rule),
        priority=10,
        block=True,
    )

    # 设置命令处理
    @nonebot_cmd.handle()
    async def handle_command(bot: Bot, event: Event) -> None:
        # 解析命令参数
        result = command.parse(str(event.get_message()))
        if result.matched:
            # 调用处理函数
            response = await handler(bot, event, **result.result)
            if response:
                await nonebot_cmd.finish(response)
        else:
            await nonebot_cmd.finish(f"命令格式错误\n用法: {command.meta.usage}")


def create_command_matcher(
    command_prefix: str,
    handler: Callable,
    permission_level: str = "user",
) -> Any:
    """
    创建命令匹配器

    Args:
        command_prefix: 命令前缀
        handler: 处理函数
        permission_level: 权限等级

    Returns:
        NoneBot 命令匹配器
    """
    async def permission_rule(bot: Bot, event: Event) -> bool:
        return await check_permission(bot, event, permission_level)

    cmd = on_command(
        command_prefix,
        rule=Rule(permission_rule),
        priority=10,
        block=True,
    )

    @cmd.handle()
    async def handle(bot: Bot, event: Event) -> None:
        response = await handler(bot, event)
        if response:
            await cmd.finish(response)

    return cmd


__all__ = [
    "CommandRegistry",
    "get_registry",
    "register_alconna_command",
    "create_command_matcher",
]
