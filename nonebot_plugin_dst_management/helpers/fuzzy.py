"""
Fuzzy command normalization (Phase B Smart).

Goals:
- Allow light natural-language prefixes like "帮我" / "请帮我" / "小安" before commands.
- Optionally rewrite a few high-frequency colloquial phrases into canonical `dst ...` commands.

This is intentionally conservative: it only rewrites when the message is likely a bot command
(usually when a command start like "/" is present) and when it matches a known prefix/phrase.
"""

from __future__ import annotations

from typing import Dict, Iterable


_COMMAND_START_CHARS = {"/", "!", "！", ".", "。"}

# Common polite prefixes / bot nicknames.
_NATURAL_PREFIXES: tuple[str, ...] = (
    "请帮我",
    "帮我",
    "麻烦",
    "拜托",
    "小安同学",
    "小安",
    "安安",
)

_STRIP_SEPARATORS = " \t,，。.!！:：;；\n\r"

# Minimal rewrite map for frequently used natural commands.
# Keep keys short and stable; match longest key first.
_REWRITE: Dict[str, str] = {
    # room lifecycle
    "开服": "dst start",
    "开房": "dst start",
    "启动": "dst start",
    "启动房间": "dst start",
    "关服": "dst stop",
    "关房": "dst stop",
    "停止": "dst stop",
    "停服": "dst stop",
    "重启": "dst restart",
    "维护": "dst restart",
    # queries
    "谁在玩": "dst players",
    "谁在线": "dst players",
    "在线玩家": "dst players",
    "玩家列表": "dst players",
    # moderation
    "踢人": "dst kick",
    "踢出": "dst kick",
}


def _strip_prefixes(text: str, prefixes: Iterable[str]) -> str:
    s = (text or "").strip()
    if not s:
        return s
    while True:
        matched = False
        for p in prefixes:
            if s.startswith(p):
                s = s[len(p) :].lstrip(_STRIP_SEPARATORS)
                matched = True
                break
        if not matched:
            break
    return s


def _rewrite_colloquial(text: str) -> str:
    s = (text or "").strip()
    if not s:
        return s

    # If already a dst command, don't touch.
    if s.lower().startswith("dst "):
        return s
    if s.lower() == "dst":
        return s

    # Longest key wins to avoid partial matches (e.g. "启动房间" vs "启动").
    for key in sorted(_REWRITE.keys(), key=len, reverse=True):
        if not s.startswith(key):
            continue
        rest = s[len(key) :].lstrip(_STRIP_SEPARATORS)
        if rest:
            return f"{_REWRITE[key]} {rest}".strip()
        return _REWRITE[key]

    return s


def normalize_command_text(raw_message: str) -> str:
    """Normalize a raw message string for command matching."""

    raw = str(raw_message or "")
    if not raw.strip():
        return raw

    s = raw.lstrip()
    prefix = ""
    if s and s[0] in _COMMAND_START_CHARS:
        prefix = s[0]
        s = s[1:].lstrip()

    s = _strip_prefixes(s, _NATURAL_PREFIXES)
    s = _rewrite_colloquial(s)

    # If there was no explicit command start, only normalize when it becomes a dst command.
    if not prefix and not s.lower().startswith("dst "):
        return raw

    return f"{prefix}{s}".strip()


__all__ = ["normalize_command_text"]
