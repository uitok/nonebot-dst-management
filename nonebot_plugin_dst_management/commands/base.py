"""
Alconna 命令基础框架

提供权限管理的便捷导出和命令辅助工具。
"""

from __future__ import annotations

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


__all__ = [
    "PermissionLevel",
    "PermissionChecker",
    "USER_PERMISSION",
    "ADMIN_PERMISSION",
    "SUPER_PERMISSION",
    "make_permission_rule",
    "check_admin",
    "check_group",
    "check_permission",
]
