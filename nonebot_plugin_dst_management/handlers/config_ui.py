"""
UI preference command handler (Phase A UI)

Command:
  /dst config ui <text|markdown>

Rules:
- OneBot v11: forced text; markdown is not supported.
- Official QQ: default markdown; user can switch between text/markdown.
"""

from __future__ import annotations

from typing import Any, Optional

from nonebot import on_command
from nonebot.adapters.onebot.v11 import Message
from nonebot.params import CommandArg

from ..database import get_user_ui_mode, init_db, set_user_ui_mode
from ..helpers.formatters import detect_bot_family, resolve_ui_mode


def _plain_args(args: Any) -> str:
    if hasattr(args, "extract_plain_text"):
        try:
            return str(args.extract_plain_text())
        except Exception:
            pass
    return str(args)


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


def init() -> None:
    cmd = on_command("dst config ui", priority=5, block=True)

    @cmd.handle()
    async def handle(bot: Any, event: Any, args: Message = CommandArg()):
        await init_db()

        raw = _plain_args(args).strip()
        family = detect_bot_family(bot, event)
        user_id = _extract_user_id(event)

        if not raw:
            resolved = await resolve_ui_mode(bot=bot, event=event, user_id=user_id)
            stored = await get_user_ui_mode(user_id) if user_id else None
            stored_text = _label_mode(stored) if stored in {"text", "markdown"} else "未设置"
            await cmd.finish(
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

        mode = raw.lower()
        if mode not in {"text", "markdown"}:
            await cmd.finish("❌ 用法：/dst config ui <text|markdown>")
            return

        if family != "qq" and mode == "markdown":
            # OneBot/unknown: markdown not supported.
            await cmd.finish("当前平台不支持 Markdown，已锁定为文本模式 ⚠️")
            return

        if not user_id:
            await cmd.finish("❌ 无法识别用户ID，无法保存 UI 偏好设置")
            return

        if family == "qq":
            await set_user_ui_mode(user_id, mode)
            await cmd.finish(f"✅ 已设置 UI 展示模式为 {_label_mode(mode)}")
            return

        # OneBot/unknown: always text.
        await cmd.finish("当前平台已锁定为文本模式 ⚠️")


__all__ = ["init"]

