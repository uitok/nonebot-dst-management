"""
UI preference command (on_alconna)

Command:
  /dst config ui [text|markdown]

Rules:
- OneBot v11: forced text; markdown is not supported.
- Official QQ: default markdown; user can switch between text/markdown.
"""

from __future__ import annotations

from typing import Any, Optional

from arclet.alconna import Alconna, Args, CommandMeta
from nonebot.internal.adapter import Event

from nonebot_plugin_alconna import Match, AlconnaMatch, on_alconna

from ..database import get_user_ui_mode, init_db, set_user_ui_mode
from ..helpers.formatters import detect_bot_family, resolve_ui_mode
from ..utils.permission import USER_PERMISSION


def _label_mode(mode: str) -> str:
    return "Markdown" if mode == "markdown" else "Text"


def _label_family(family: str) -> str:
    if family == "qq":
        return "QQ"
    if family == "onebot_v11":
        return "OneBot v11"
    return "Unknown"


def _extract_user_id(event: Any) -> Optional[str]:
    get_user_id = getattr(event, "get_user_id", None)
    if callable(get_user_id):
        try:
            value = get_user_id()
            return str(value) if value else None
        except Exception:
            pass
    user_id = getattr(event, "user_id", None)
    return str(user_id) if user_id is not None else None


# ========== Alconna 命令定义 ==========

config_ui_command = Alconna(
    "dst config ui",
    Args["mode", str, None],
    meta=CommandMeta(
        description="设置UI展示模式",
        usage="/dst config ui [text|markdown]",
        example="/dst config ui markdown",
    ),
)

config_ui_matcher = on_alconna(config_ui_command, permission=USER_PERMISSION, priority=5, block=True)


# ========== 命令处理 ==========

@config_ui_matcher.handle()
async def handle_config_ui(
    event: Event,
    mode: Match[str] = AlconnaMatch("mode"),
) -> None:
    """处理 UI 配置命令"""
    await init_db()

    mode_val = mode.result.strip().lower() if mode.available and mode.result else None

    # Detect bot family
    bot = None
    try:
        from nonebot import get_bot
        bot = get_bot()
    except Exception:
        pass

    family = detect_bot_family(bot, event) if bot else "unknown"
    user_id = _extract_user_id(event)

    if not mode_val:
        resolved = await resolve_ui_mode(bot=bot, event=event, user_id=user_id)
        stored = await get_user_ui_mode(user_id) if user_id else None
        stored_text = _label_mode(stored) if stored in {"text", "markdown"} else "未设置"
        await config_ui_matcher.finish(
            "\n".join(
                [
                    "⚙️ UI 展示模式",
                    f"- 平台：{_label_family(family)}",
                    f"- 当前生效：{_label_mode(resolved)}",
                    f"- 已保存偏好：{stored_text}",
                    "",
                    "用法：/dst config ui <text|markdown>",
                ]
            ).strip()
        )
        return

    if mode_val not in {"text", "markdown"}:
        await config_ui_matcher.finish("❌ 用法：/dst config ui <text|markdown>")
        return

    if family != "qq" and mode_val == "markdown":
        await config_ui_matcher.finish("当前平台不支持 Markdown，已锁定为文本模式 ⚠️")
        return

    if not user_id:
        await config_ui_matcher.finish("❌ 无法识别用户ID，无法保存 UI 偏好设置")
        return

    if family == "qq":
        await set_user_ui_mode(user_id, mode_val)
        await config_ui_matcher.finish(f"✅ 已设置 UI 展示模式为 {_label_mode(mode_val)}")
        return

    await config_ui_matcher.finish("当前平台已锁定为文本模式 ⚠️")


def init() -> None:
    """No-op init for compatibility. Matcher is registered at import time."""
    pass


__all__ = [
    "config_ui_command",
    "config_ui_matcher",
    "handle_config_ui",
    "init",
]
