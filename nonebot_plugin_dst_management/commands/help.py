"""\
Help command (on_alconna)

Hierarchical help menu with 4 categories:
- 🏠 基础管理
- 👥 玩家管理
- 📦 备份与模组
- ⚙️ 系统设置

Keep this file UI-only (no API calls).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable, Optional

from arclet.alconna import Alconna, Args, CommandMeta
from nonebot.internal.adapter import Event

from nonebot_plugin_alconna import Match, AlconnaMatch, on_alconna

from ..helpers.formatters import ICON_TIP, detect_bot_family, format_info
from ..utils.permission import USER_PERMISSION


@dataclass(frozen=True)
class HelpItem:
    icon: str
    title: str
    usage: str
    desc: str
    admin_only: bool = False
    aliases: tuple[str, ...] = ()


def _tree_lines(items: Iterable[str]) -> list[str]:
    items = list(items)
    lines: list[str] = []
    for idx, item in enumerate(items, 1):
        head = "└─" if idx == len(items) else "├─"
        lines.append(f"{head} {item}")
    return lines


def _render_items(items: list[HelpItem]) -> list[str]:
    lines: list[str] = []
    for idx, item in enumerate(items, 1):
        head = "└─" if idx == len(items) else "├─"
        pad = "  " if idx == len(items) else "│ "
        lock = " 🔒" if item.admin_only else ""

        lines.append(f"{head} {item.icon} {item.title}{lock}")
        lines.append(f"{pad}用法: {item.usage}")
        if item.aliases:
            lines.append(f"{pad}别名: {', '.join(item.aliases)}")
        lines.append(f"{pad}说明: {item.desc}")
        if idx != len(items):
            lines.append("")
    return lines


def _normalize_key(raw: str) -> str:
    return (raw or "").strip().lower().replace("/", "")


def _resolve_category(raw: str) -> Optional[str]:
    key = _normalize_key(raw)
    if not key:
        return None

    if key in {"base", "基础", "基础管理", "房间", "房间管理", "room"}:
        return "base"

    if key in {"player", "玩家", "玩家管理", "人", "players"}:
        return "player"

    if key in {
        "backup",
        "mod",
        "备份",
        "模组",
        "备份与模组",
        "备份模组",
        "backup/mod",
        "backupmod",
        "mods",
    }:
        return "backup_mod"

    if key in {"settings", "setting", "设置", "系统设置", "默认房间"}:
        return "settings"

    return None


def _help_main_menu() -> str:
    lines: list[str] = [
        "📖 DST 管理帮助",
        "",
        "🏠 基础管理",
        *_tree_lines(
            [
                "📋 房间列表: /dst list",
                "🔎 房间详情: /dst info",
                "🚀 启动 / 🛑 关闭 / 🔄 重启: /dst start|stop|restart 🔒",
            ]
        ),
        "",
        "👥 玩家管理",
        *_tree_lines(["👥 在线玩家: /dst players", "🦶 踢出玩家: /dst kick 🔒"]),
        "",
        "📦 备份与模组",
        *_tree_lines(
            [
                "💾 备份: /dst backup list|create|restore 🔒",
                "🧩 模组: /dst mod search|list|add|remove|check 🔒",
            ]
        ),
        "",
        "⚙️ 系统设置",
        *_tree_lines(
            [
                "📌 默认房间: /dst 默认房间 / 查看默认 / 清除默认",
                "🔍 自动发现: /dst room scan 🔒",
                "📥 导入发现: /dst room import --select ... 🔒",
            ]
        ),
        "",
        f"{ICON_TIP} 发送 /dst help 基础 | 玩家 | 备份 | 设置 查看完整用法",
    ]
    return "\n".join(lines).strip()


def _help_main_menu_markdown() -> str:
    lines: list[str] = [
        "# DST 管理帮助",
        "",
        "## 🏠 基础管理",
        "- 📋 房间列表: `/dst list`",
        "- 🔎 房间详情: `/dst info`",
        "- 🚀 启动 / 🛑 关闭 / 🔄 重启: `/dst start|stop|restart` (🔒)",
        "",
        "## 👥 玩家管理",
        "- 👥 在线玩家: `/dst players`",
        "- 🦶 踢出玩家: `/dst kick` (🔒)",
        "",
        "## 📦 备份与模组",
        "- 💾 备份: `/dst backup list|create|restore` (🔒)",
        "- 🧩 模组: `/dst mod search|list|add|remove|check` (🔒)",
        "",
        "## ⚙️ 系统设置",
        "- 📌 默认房间: `/dst 默认房间` / `/dst 查看默认` / `/dst ���除默认`",
        "- 🔍 自动发现: `/dst room scan` (🔒)",
        "- 📥 导入发现: `/dst room import ...` (🔒)",
        "",
        f"{ICON_TIP} 发送 `/dst help 基础|玩家|备份|设置` 查看完整用法",
    ]
    return "\n".join(lines).strip()


def _help_base() -> str:
    items = [
        HelpItem(
            "📋",
            "房间列表",
            "/dst list [页码]",
            "查看房间列表",
            aliases=("dst 房间列表", "dst 列表", "dst 查房", "dst 查看房间", "dst 查房间"),
        ),
        HelpItem(
            "🔎",
            "房间详情",
            "/dst info <房间ID>",
            "查看房间详细信息",
            aliases=("dst 房间详情", "dst 详情", "dst 房间信息", "dst 查房间详情", "dst 查详情"),
        ),
        HelpItem(
            "🚀",
            "启动房间",
            "/dst start <房间ID>",
            "启动指定房间",
            admin_only=True,
            aliases=("dst 启动", "dst 启动房间", "dst 开房", "dst 开启房间"),
        ),
        HelpItem(
            "🛑",
            "关闭房间",
            "/dst stop <房间ID>",
            "关闭指定房间",
            admin_only=True,
            aliases=("dst 停止", "dst 停止房间", "dst 关闭", "dst 关闭房间", "dst 关房"),
        ),
        HelpItem(
            "🔄",
            "重启房间",
            "/dst restart <房间ID>",
            "重启指定房间",
            admin_only=True,
            aliases=("dst 重启", "dst 重启房间", "dst 重开房间"),
        ),
    ]
    lines = ["🏠 基础管理", ""]
    lines.extend(_render_items(items))
    lines.append("")
    lines.append("🔒 标记的命令需要管理员权限")
    return "\n".join(lines).strip()


def _help_player() -> str:
    items = [
        HelpItem(
            "👥",
            "在线玩家",
            "/dst players <房间ID>",
            "查看在线玩家列表",
            aliases=("dst 玩家列表", "dst 在线玩家", "dst 查玩家", "dst 查看玩家"),
        ),
        HelpItem(
            "🦶",
            "踢出玩家",
            "/dst kick <房间ID> <KU_ID>",
            "踢出���定玩家",
            admin_only=True,
            aliases=("dst 踢出玩家", "dst 踢人", "dst 踢出", "dst 踢玩家"),
        ),
    ]
    lines = ["👥 玩家管理", ""]
    lines.extend(_render_items(items))
    lines.append("")
    lines.append("🔒 标记的命令需要管理员权限")
    return "\n".join(lines).strip()


def _help_backup_mod() -> str:
    items = [
        HelpItem(
            "💾",
            "备份列表",
            "/dst backup list <房间ID>",
            "查看备份列表",
            aliases=("dst 备份列表", "dst 查备份", "dst 查看备份"),
        ),
        HelpItem(
            "📦",
            "创建备份",
            "/dst backup create <房间ID>",
            "创建一次备份",
            admin_only=True,
            aliases=("dst 创建备份", "dst 备份创建", "dst 立即备份", "dst 生成备份"),
        ),
        HelpItem(
            "♻️",
            "恢复备份",
            "/dst backup restore <房间ID> <文件名>",
            "恢复指定备份",
            admin_only=True,
            aliases=("dst 恢复备份", "dst 备份恢复", "dst 回档", "dst 回档备份"),
        ),
        HelpItem(
            "🔍",
            "搜索模组",
            "/dst mod search <关键词>",
            "搜索模组",
            aliases=("dst 模组搜索", "dst 搜索模组", "dst 找模组"),
        ),
        HelpItem(
            "🧩",
            "模组列表",
            "/dst mod list <房间ID>",
            "查看已安装模组",
            aliases=("dst 模组列表", "dst 已安装模组", "dst 已装模组"),
        ),
        HelpItem(
            "➕",
            "添加模组",
            "/dst mod add <房间ID> <世界ID> <模组ID>",
            "下载并启用模组",
            admin_only=True,
            aliases=("dst 添加模组", "dst 安装模组", "dst 装模组"),
        ),
        HelpItem(
            "➖",
            "移除模组",
            "/dst mod remove <房间ID> <世界ID> <模组ID>",
            "禁用模组",
            admin_only=True,
            aliases=("dst 移除模组", "dst 删除模组", "dst 卸载模组"),
        ),
        HelpItem(
            "🧪",
            "检测模组冲突",
            "/dst mod check <房间ID>",
            "检测重复条目等问题",
            aliases=("dst 检测模组", "dst 模组检测", "dst 冲突检测"),
        ),
    ]
    lines = ["📦 备份与模组", ""]
    lines.extend(_render_items(items))
    lines.append("")
    lines.append("🔒 标记的命令需要管理员权限")
    return "\n".join(lines).strip()


def _help_settings() -> str:
    items = [
        HelpItem(
            "📌",
            "设置默认房间",
            "/dst 默认房间 <房间ID>",
            "设置后大部分命令可省略房间ID",
            aliases=("dst setroom", "dst 设置默认房间", "dst 设默认房间"),
        ),
        HelpItem(
            "👀",
            "查看默认房间",
            "/dst 查看默认",
            "查看当前默认房间",
            aliases=("dst myroom", "dst 查看默认房间", "dst 我的房间"),
        ),
        HelpItem(
            "🧹",
            "清除默认房间",
            "/dst 清除默认",
            "清除默认房间设置",
            aliases=("dst unsetroom", "dst 清除默认房间", "dst 清默认", "dst 清空默认"),
        ),
        HelpItem(
            "🔍",
            "自动发现房间",
            "/dst room scan [--depth N] <路径...>",
            "扫描本地目录，自动识别包含 cluster.ini 的 DST 集群",
            admin_only=True,
            aliases=("dst 房间扫描", "dst 扫描房间", "dst room discover", "dst scan"),
        ),
        HelpItem(
            "📥",
            "导入发现结果",
            "/dst room import --select <all|1,2|1-3> [--depth N] <路径...>",
            "将扫描到的集群写入插件配置（data/dst_clusters.json），避免手动配置路径",
            admin_only=True,
            aliases=("dst 房间导入", "dst 导入房间", "dst room setup", "dst setup"),
        ),
    ]
    lines = ["⚙️ 系统设置", ""]
    lines.extend(_render_items(items))
    return "\n".join(lines).strip()


# ========== Alconna 命令定义 ==========

help_command = Alconna(
    "dst help",
    Args["category", str, None],
    meta=CommandMeta(
        description="查看帮助",
        usage="/dst help [模块名]",
        example="/dst help 基础",
    ),
)

help_matcher = on_alconna(help_command, permission=USER_PERMISSION, priority=5, block=True)


# ========== 命令处理 ==========

@help_matcher.handle()
async def handle_help(
    event: Event,
    category: Match[str] = AlconnaMatch("category"),
) -> None:
    """处理帮助命令"""
    # Detect bot family for markdown vs text rendering
    bot = None
    try:
        from nonebot import get_bot
        bot = get_bot()
    except Exception:
        pass

    family = detect_bot_family(bot, event) if bot else "unknown"

    cat_val = category.result if category.available else None

    if not cat_val:
        if family == "qq":
            await help_matcher.finish(_help_main_menu_markdown())
        else:
            await help_matcher.finish(_help_main_menu())
        return

    resolved = _resolve_category(cat_val)
    if resolved == "base":
        await help_matcher.finish(_help_base())
    elif resolved == "player":
        await help_matcher.finish(_help_player())
    elif resolved == "backup_mod":
        await help_matcher.finish(_help_backup_mod())
    elif resolved == "settings":
        await help_matcher.finish(_help_settings())
    else:
        await help_matcher.finish(
            format_info(
                f"未找到模块：{cat_val}\n{ICON_TIP} 可用：基础 / 玩家 / 备份 / 设置（或 base/player/backup/settings）"
            )
        )


def init() -> None:
    """No-op init for compatibility. Matcher is registered at import time."""
    pass


__all__ = [
    "help_command",
    "help_matcher",
    "handle_help",
    "init",
]
