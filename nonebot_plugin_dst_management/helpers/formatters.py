"""\
UI formatters (Phase A)

Centralizes emoji-enhanced string templates for:
- status badges (running/stopped/error)
- list rendering helpers (rooms/players/backups/tables)
- feedback messages (success/error/info/warning/loading)

Keep this module presentation-only: no business logic, no API calls.
"""

from __future__ import annotations

from typing import Any, Dict, List, Literal, Optional, cast

from nonebot.adapters.onebot.v11 import Message

# =========================
# Dynamic Rendering (Phase A)
# =========================

UIMode = Literal["text", "markdown"]
BotFamily = Literal["onebot_v11", "qq", "unknown"]


def detect_bot_family(bot: Any = None, event: Any = None) -> BotFamily:
    """
    Return adapter family key based on Bot/Event type.

    Keep this implementation import-free so it works even when optional adapters
    are not installed in the environment.
    """

    def _family(obj: Any) -> Optional[BotFamily]:
        if obj is None:
            return None
        cls = getattr(obj, "__class__", None)
        module = getattr(cls, "__module__", "") if cls else ""
        if module.startswith("nonebot.adapters.qq"):
            return "qq"
        if module.startswith("nonebot.adapters.onebot.v11"):
            return "onebot_v11"
        return None

    return _family(bot) or _family(event) or "unknown"


def _extract_user_id(event: Any) -> Optional[str]:
    if event is None:
        return None
    get_user_id = getattr(event, "get_user_id", None)
    if callable(get_user_id):
        try:
            user_id = get_user_id()
            return str(user_id) if user_id else None
        except Exception:
            pass
    user_id = getattr(event, "user_id", None)
    return str(user_id) if user_id is not None else None


async def _get_user_ui_pref(user_id: Optional[str]) -> Optional[UIMode]:
    if not user_id:
        return None
    try:
        from ..database import get_user_ui_mode

        value = await get_user_ui_mode(user_id)
    except Exception:
        return None
    if value in {"text", "markdown"}:
        return cast(UIMode, value)
    return None


async def resolve_ui_mode(
    *,
    bot: Any = None,
    event: Any = None,
    user_id: Optional[str] = None,
    preferred_mode: Optional[UIMode] = None,
) -> UIMode:
    """
    Resolve the effective UI mode considering:
    - platform capability (OneBot forced text)
    - per-user preference (QQ only)
    - platform default (QQ markdown; others text)
    """

    family = detect_bot_family(bot, event)
    if family == "onebot_v11":
        return "text"
    if family == "qq":
        if preferred_mode:
            return preferred_mode
        stored = await _get_user_ui_pref(user_id)
        return stored or "markdown"
    return "text"


def build_qq_markdown_message(markdown: str) -> Any:
    """
    Best-effort builder for QQ Markdown message.

    If the QQ adapter isn't installed (common in tests), fall back to raw text.
    """

    try:
        import importlib

        qq_message = importlib.import_module("nonebot.adapters.qq.message")
        qq_segment = getattr(qq_message, "MessageSegment", None)
        if qq_segment is None:
            return markdown

        # Try common segment factories; fall back to raw markdown string.
        for factory_name in ("markdown", "Markdown", "md"):
            factory = getattr(qq_segment, factory_name, None)
            if callable(factory):
                try:
                    return factory(markdown)
                except Exception:
                    continue

        return markdown
    except Exception:
        return markdown


def _plain_text(message: Any) -> str:
    if hasattr(message, "extract_plain_text"):
        try:
            return str(message.extract_plain_text())
        except Exception:
            pass
    return str(message)

# =========================
# Emoji / Icons (single source of truth)
# =========================

ICON_SUCCESS = "✅"
ICON_ERROR = "❌"
ICON_INFO = "ℹ️"
ICON_WARNING = "⚠️"
ICON_LOADING = "⏳"

ICON_RUNNING = "🟢"
ICON_STOPPED = "🔴"

ICON_EMPTY = "🈳"
ICON_TIP = "💡"

ICON_ROOM = "🏕️"
ICON_PLAYER = "👥"
ICON_BACKUP = "💾"
ICON_MOD = "🧩"

# Backward-compatible mapping (handy for templates)
EMOJI: Dict[str, str] = {
    "success": ICON_SUCCESS,
    "error": ICON_ERROR,
    "info": ICON_INFO,
    "warning": ICON_WARNING,
    "loading": ICON_LOADING,
    "running": ICON_RUNNING,
    "stopped": ICON_STOPPED,
    "empty": ICON_EMPTY,
    "tip": ICON_TIP,
    "room": ICON_ROOM,
    "player": ICON_PLAYER,
    "backup": ICON_BACKUP,
    "mod": ICON_MOD,
}


def status_badge(status: object) -> str:
    """Format a consistent running/stopped/unknown badge.

    Phase A standard:
    - running:  🟢 [运行中] 🌟
    - stopped:  🔴 [已停止] 💤
    - unknown:  ⚠️ [异常]

    Accepts common API variants: bool or 0/1 integers.
    """

    if status is True or status == 1:
        return f"{ICON_RUNNING} [运行中] 🌟"
    if status is False or status == 0:
        return f"{ICON_STOPPED} [已停止] 💤"
    return f"{ICON_WARNING} [异常]"


def format_status(running: bool) -> str:
    """
    Phase A (UI) public API.

    Keep key phrases like "运行中/已停止" for backward compatibility.
    """
    return status_badge(bool(running))


def online_badge(is_online: bool) -> str:
    """Format a consistent online/offline badge for worlds/players."""

    return f"{ICON_RUNNING} 在线" if is_online else f"{ICON_STOPPED} 离线"


def progress_bar(current: int, total: int, width: int = 5) -> str:
    """Simple textual progress bar.

    Example: [■■■□□] 60%
    """

    if total <= 0:
        return "[□□□□□] 0%"
    ratio = max(0.0, min(1.0, current / total))
    filled = int(round(ratio * width))
    return f"[{'■' * filled}{'□' * (width - filled)}] {int(ratio * 100)}%"


def format_progress(current: int, total: int, width: int = 10) -> str:
    """
    Phase A (UI) public API.

    Example: ▰▰▰▱▱▱▱▱▱▱ 3/10
    """
    if width <= 0:
        width = 10
    if total <= 0:
        return f"{'▱' * width} {current}/{total}"

    cur = max(0, min(int(current), int(total)))
    ratio = cur / int(total)
    filled = int(round(ratio * width))
    filled = max(0, min(filled, width))
    return f"{'▰' * filled}{'▱' * (width - filled)} {cur}/{int(total)}"


# =========================
# Feedback message helpers
# =========================
# NOTE: These functions return str for multi-adapter compatibility.
# For OneBot v11, wrap with Message() if needed by the caller.


def format_loading(message: str = "处理中...") -> str:
    return f"{ICON_LOADING} {message}"


def format_error(message: str) -> str:
    return f"{ICON_ERROR} {message}"


def format_success(message: str) -> str:
    return f"{ICON_SUCCESS} {message}"


def format_info(message: str) -> str:
    return f"{ICON_INFO} {message}"


def format_warning(message: str) -> str:
    return f"{ICON_WARNING} {message}"


# =========================
# List renderers
# =========================


def _tree_prefix(idx: int, total: int) -> tuple[str, str]:
    """Return (head, pad) for tree-like list layout."""

    is_last = idx == total
    if is_last:
        return "└─", "  "
    return "├─", "│ "


def format_room_list(
    rooms: List[Dict[str, Any]],
    page: int,
    total_pages: int,
    total: int,
) -> str:
    lines: List[str] = [
        f"{ICON_ROOM} DST 房间列表",
        f"第 {page}/{total_pages} 页 | 共 {total} 个房间",
        "",
    ]

    if not rooms:
        lines.append(f"{ICON_EMPTY} 暂无房间")
    else:
        for i, room in enumerate(rooms, 1):
            head, pad = _tree_prefix(i, len(rooms))
            name = room.get("gameName", "未知")
            status = status_badge(room.get("status"))
            game_mode = room.get("gameMode", "未知")
            room_id = room.get("id")

            lines.append(f"{head} {name}")
            lines.append(f"{pad}状态：{status}")
            lines.append(f"{pad}模式：{game_mode}")
            lines.append(f"{pad}ID：{room_id}")

            if i != len(rooms):
                lines.append("")

    lines.append("")
    lines.append(f"{ICON_TIP} 使用 /dst info <房间ID> 查看详情")
    if page < total_pages:
        lines.append(f"{ICON_TIP} 使用 /dst list {page + 1} 查看下一页")
    return "\n".join(lines).strip()


def format_room_detail(
    room: Dict[str, Any],
    worlds: List[Dict[str, Any]],
    players: List[Dict[str, Any]],
) -> Message:
    lines: List[str] = [
        f"{ICON_ROOM} {room.get('gameName', '未知房间')}",
        "",
        "📋 基本信息",
        f"- 房间ID：{room.get('id')}",
        f"- 状态：{status_badge(room.get('status'))}",
        f"- 模式：{room.get('gameMode', '未知')}",
        f"- 玩家限制：{room.get('maxPlayer', 0)}人",
        f"- 密码：{'已设置' if room.get('password') else '无'}",
        f"- PVP：{'开启' if room.get('pvp') else '关闭'}",
        f"- 描述：{room.get('description', '无')}",
        "",
    ]

    if worlds:
        lines.append("🌍 世界列表")
        for world in worlds:
            is_online = bool(world.get("lastAliveTime"))
            status = online_badge(is_online)
            lines.append(
                f"- {world.get('worldName', '未知')}：{status} (端口 {world.get('serverPort')})"
            )
        lines.append("")

    if players:
        lines.append(f"{ICON_PLAYER} 在线玩家 ({len(players)}人)")
        for player in players[:10]:
            nickname = player.get("nickname") or player.get("uid", "未知")
            prefab = player.get("prefab", "未知")
            lines.append(f"- {nickname} ({prefab})")
        if len(players) > 10:
            lines.append(f"... 还有 {len(players) - 10} 名玩家")
        lines.append("")

    mod_data = room.get("modData", "")
    if mod_data:
        mod_count = mod_data.count('["workshop-')
        if mod_count > 0:
            lines.append(f"{ICON_MOD} 已安装模组：{mod_count}个")

    return "\n".join(lines).strip()


def format_players(room_name: str, players: List[Dict[str, Any]]) -> str:
    lines: List[str] = [f"{ICON_PLAYER} 在线玩家 ({room_name})", ""]

    if not players:
        lines.append(f"{ICON_EMPTY} 当前没有玩家在线")
        return "\n".join(lines).strip()

    for idx, player in enumerate(players, 1):
        head, pad = _tree_prefix(idx, len(players))
        nickname = player.get("nickname") or player.get("uid", "未知")
        uid = player.get("uid", "未知")
        prefab = player.get("prefab", "未知")
        lines.append(f"{head} {nickname}")
        lines.append(f"{pad}KU_ID: `{uid}`")
        lines.append(f"{pad}角色: {prefab}")
        if idx != len(players):
            lines.append("")

    lines.append("")
    lines.append(f"共 {len(players)} 名玩家在线")
    return "\n".join(lines).strip()


def format_player_list(room_name: str, players: List[Dict[str, Any]]) -> str:
    """Compatibility wrapper."""

    return format_players(room_name, players)


def format_backups(room_name: str, backups: List[Dict[str, Any]]) -> str:
    lines: List[str] = [f"{ICON_BACKUP} 备份列表 ({room_name})", ""]

    if not backups:
        lines.append(f"{ICON_EMPTY} 暂无备份")
        return "\n".join(lines).strip()

    for idx, backup in enumerate(backups[:20], 1):
        head, pad = _tree_prefix(idx, min(len(backups), 20))
        filename = backup.get("filename", "未知")
        size = backup.get("size", 0)
        size_mb = f"{size / 1024 / 1024:.2f}MB" if size > 0 else "未知"

        created_at = backup.get("created_at", "")
        if created_at:
            try:
                from datetime import datetime

                dt = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
                time_str = dt.strftime("%Y-%m-%d %H:%M:%S")
            except Exception:
                time_str = created_at
        else:
            time_str = "未知"

        lines.append(f"{head} {filename}")
        lines.append(f"{pad}大小: {size_mb}")
        lines.append(f"{pad}时间: {time_str}")
        if idx != min(len(backups), 20):
            lines.append("")

    if len(backups) > 20:
        lines.append("")
        lines.append(f"... 还有 {len(backups) - 20} 个备份")

    lines.append("")
    lines.append(f"{ICON_TIP} 使用 /dst backup restore <房间ID> <文件名> 恢复备份")
    return "\n".join(lines).strip()


def format_backup_list(room_name: str, backups: List[Dict[str, Any]]) -> str:
    """Compatibility wrapper."""

    return format_backups(room_name, backups)


def format_table(headers: List[str], rows: List[List[Any]]) -> str:
    """Render a simple fixed-width table for text messages."""

    if not headers:
        return ""

    str_headers = [str(h) for h in headers]
    str_rows = [[str(cell) for cell in row] for row in (rows or [])]

    widths = [len(h) for h in str_headers]
    for row in str_rows:
        for i in range(min(len(widths), len(row))):
            widths[i] = max(widths[i], len(row[i]))

    def fmt_row(cells: List[str]) -> str:
        padded: List[str] = []
        for i, w in enumerate(widths):
            val = cells[i] if i < len(cells) else ""
            padded.append(val.ljust(w))
        return " | ".join(padded)

    lines = [fmt_row(str_headers), "-+-".join("-" * w for w in widths)]
    for row in str_rows:
        lines.append(fmt_row(row))
    return "\n".join(lines)


# =========================
# Markdown renderers (QQ)
# =========================


def status_badge_markdown(status: object) -> str:
    """Compact status badge suitable for Markdown."""

    if status is True or status == 1:
        return f"{ICON_RUNNING} 运行中"
    if status is False or status == 0:
        return f"{ICON_STOPPED} 已停止"
    return f"{ICON_WARNING} 异常"


def format_room_list_markdown(
    rooms: List[Dict[str, Any]],
    page: int,
    total_pages: int,
    total: int,
) -> str:
    lines: List[str] = [
        f"# {ICON_ROOM} DST 房间列表",
        f"**第 {page}/{total_pages} 页** | 共 **{total}** 个房间",
        "",
    ]

    if not rooms:
        lines.append(f"{ICON_EMPTY} 暂无房间")
    else:
        for idx, room in enumerate(rooms, 1):
            name = room.get("gameName", "未知")
            status = status_badge_markdown(room.get("status"))
            game_mode = room.get("gameMode", "未知")
            room_id = room.get("id")

            lines.append(f"## {idx}. {name}")
            lines.append(f"- **状态**：{status}")
            lines.append(f"- **模式**：`{game_mode}`")
            lines.append(f"- **ID**：`{room_id}`")
            lines.append("")

    lines.append(f"{ICON_TIP} 使用 `/dst info <房间ID>` 查看详情")
    if page < total_pages:
        lines.append(f"{ICON_TIP} 使用 `/dst list {page + 1}` 查看下一页")
    return "\n".join(lines).strip()


def format_room_detail_markdown(
    room: Dict[str, Any],
    worlds: List[Dict[str, Any]],
    players: List[Dict[str, Any]],
) -> str:
    lines: List[str] = [
        f"# {ICON_ROOM} {room.get('gameName', '未知房间')}",
        "",
        "## 📋 基本信息",
        f"- **房间ID**：`{room.get('id')}`",
        f"- **状态**：{status_badge_markdown(room.get('status'))}",
        f"- **模式**：`{room.get('gameMode', '未知')}`",
        f"- **玩家限制**：{room.get('maxPlayer', 0)} 人",
        f"- **密码**：{'已设置' if room.get('password') else '无'}",
        f"- **PVP**：{'开启' if room.get('pvp') else '关闭'}",
        f"- **描述**：{room.get('description', '无')}",
        "",
    ]

    if worlds:
        lines.append("## 🌍 世界列表")
        for world in worlds:
            is_online = bool(world.get("lastAliveTime"))
            status = online_badge(is_online)
            port = world.get("serverPort")
            lines.append(f"- {world.get('worldName', '未知')}：{status} (端口 `{port}`)")
        lines.append("")

    if players:
        lines.append(f"## {ICON_PLAYER} 在线玩家 ({len(players)} 人)")
        for player in players[:10]:
            nickname = player.get("nickname") or player.get("uid", "未知")
            prefab = player.get("prefab", "未知")
            lines.append(f"- {nickname} (`{prefab}`)")
        if len(players) > 10:
            lines.append(f"- ... 还有 {len(players) - 10} 名玩家")
        lines.append("")

    mod_data = room.get("modData", "")
    if mod_data:
        mod_count = mod_data.count('["workshop-')
        if mod_count > 0:
            lines.append("## 🧩 模组")
            lines.append(f"- 已安装：**{mod_count}** 个")

    return "\n".join(lines).strip()


def format_players_markdown(room_name: str, players: List[Dict[str, Any]]) -> str:
    lines: List[str] = [
        f"# {ICON_PLAYER} 在线玩家",
        f"- **房间**：{room_name}",
        f"- **人数**：{len(players)}",
        "",
    ]

    if not players:
        lines.append(f"{ICON_EMPTY} 当前没有玩家在线")
        return "\n".join(lines).strip()

    for idx, player in enumerate(players, 1):
        nickname = player.get("nickname") or player.get("uid", "未知")
        uid = player.get("uid", "未知")
        prefab = player.get("prefab", "未知")
        lines.append(f"- {idx}. **{nickname}** | `{uid}` | `{prefab}`")

    return "\n".join(lines).strip()


def format_backups_markdown(room_name: str, backups: List[Dict[str, Any]]) -> str:
    lines: List[str] = [f"# {ICON_BACKUP} 备份列表 ({room_name})", ""]

    if not backups:
        lines.append(f"{ICON_EMPTY} 暂无备份")
        return "\n".join(lines).strip()

    for idx, backup in enumerate(backups[:20], 1):
        filename = backup.get("filename", "未知")
        size = backup.get("size", 0)
        size_mb = f"{size / 1024 / 1024:.2f}MB" if size > 0 else "未知"

        created_at = backup.get("created_at", "")
        if created_at:
            try:
                from datetime import datetime

                dt = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
                time_str = dt.strftime("%Y-%m-%d %H:%M:%S")
            except Exception:
                time_str = created_at
        else:
            time_str = "未知"

        lines.append(f"## {idx}. {filename}")
        lines.append(f"- **大小**：{size_mb}")
        lines.append(f"- **时间**：{time_str}")
        lines.append("")

    if len(backups) > 20:
        lines.append(f"... 还有 {len(backups) - 20} 个备份")
        lines.append("")

    lines.append(f"{ICON_TIP} 使用 `/dst backup restore <房间ID> <文件名>` 恢复备份")
    return "\n".join(lines).strip()


def format_table_markdown(headers: List[str], rows: List[List[Any]]) -> str:
    text_table = _plain_text(format_table(headers, rows))
    if not text_table.strip():
        return ""
    return f"""```text\n{text_table}\n```"""


def render(template_name: str, mode: UIMode = "text", **kwargs: Any) -> Any:
    """Render a named template with a specified mode."""

    if mode == "markdown":
        md_map = {
            "room_list": format_room_list_markdown,
            "room_detail": format_room_detail_markdown,
            "players": format_players_markdown,
            "backups": format_backups_markdown,
            "table": format_table_markdown,
        }
        renderer = md_map.get(template_name)
        if renderer is None:
            # Best-effort fallback: show text output as a code block.
            text = _plain_text(render(template_name, mode="text", **kwargs))
            return f"""```text\n{text}\n```"""
        return renderer(**kwargs)

    text_map = {
        "room_list": format_room_list,
        "room_detail": format_room_detail,
        "players": format_players,
        "backups": format_backups,
        "table": format_table,
    }
    renderer = text_map.get(template_name)
    if renderer is None:
        raise KeyError(f"Unknown template: {template_name}")
    return renderer(**kwargs)


async def render_auto(
    template_name: str,
    *,
    bot: Any = None,
    event: Any = None,
    user_id: Optional[str] = None,
    preferred_mode: Optional[UIMode] = None,
    **kwargs: Any,
) -> Any:
    """
    Platform-aware renderer.

    - OneBot v11: always text
    - QQ: default markdown, but can be switched by user preference
    """

    family = detect_bot_family(bot, event)
    resolved_user_id = user_id or _extract_user_id(event)
    mode = await resolve_ui_mode(
        bot=bot,
        event=event,
        user_id=resolved_user_id,
        preferred_mode=preferred_mode,
    )

    # Capability enforcement
    if family != "qq":
        mode = "text"
    if family == "onebot_v11":
        mode = "text"

    content = render(template_name, mode=mode, **kwargs)

    if mode == "markdown":
        # QQ adapter prefers a dedicated Markdown segment.
        return build_qq_markdown_message(cast(str, content))

    # Text mode: OneBot uses Message; QQ uses plain text.
    if family == "qq":
        return _plain_text(content)
    return content


__all__ = [
    "EMOJI",
    "ICON_SUCCESS",
    "ICON_ERROR",
    "ICON_INFO",
    "ICON_WARNING",
    "ICON_LOADING",
    "ICON_RUNNING",
    "ICON_STOPPED",
    "ICON_EMPTY",
    "ICON_TIP",
    "ICON_ROOM",
    "ICON_PLAYER",
    "ICON_BACKUP",
    "ICON_MOD",
    "status_badge",
    "format_status",
    "online_badge",
    "progress_bar",
    "format_progress",
    "format_loading",
    "format_error",
    "format_success",
    "format_info",
    "format_warning",
    "format_room_list",
    "format_room_detail",
    "format_players",
    "format_player_list",
    "format_backups",
    "format_backup_list",
    "format_table",
]
