"""
命令注册器（兼容层）

在 on_alconna 架构下，命令匹配器已在各子模块中通过 on_alconna() 自动注册，
CommandRegistry 作为命令元数据索引保留，用于帮助系统和命令枚举。
"""

from __future__ import annotations

from typing import Callable, Dict, List, Optional, Tuple

from arclet.alconna import Alconna


class CommandRegistry:
    """命令注册器 — 元数据索引"""

    def __init__(self) -> None:
        self._commands: Dict[str, Alconna] = {}
        self._permissions: Dict[str, str] = {}

    def register(self, command: Alconna, permission_level: str = "user") -> None:
        command_path = str(command.path)
        self._commands[command_path] = command
        self._permissions[command_path] = permission_level

    def get_command(self, path: str) -> Optional[Alconna]:
        return self._commands.get(path)

    def get_permission(self, path: str) -> str:
        return self._permissions.get(path, "user")

    def list_commands(self) -> List[Tuple[str, Alconna, str]]:
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


__all__ = [
    "CommandRegistry",
    "get_registry",
]
