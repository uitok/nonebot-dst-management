"""
AI Prompt 模板管理

提供默认模板、自定义模板与变量替换。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Iterable, Mapping

from .base import ChatMessage


DEFAULT_PROMPT_TEMPLATE = (
    "你是 DST 管理插件的智能助手，请根据已知资料回答用户问题。\n\n"
    "问题：{question}\n"
    "{context}\n"
    "{sources}\n"
    "{history}\n"
    "要求：\n"
    "1. 使用 Markdown 输出回答。\n"
    "2. 给出清晰结论与可执行步骤。\n"
    "3. 如引用资料，请在末尾列出来源名称。\n"
)


class _SafeDict(dict):
    def __missing__(self, key: str) -> str:  # pragma: no cover - 极少触发
        return "{" + key + "}"


def format_sources(sources: Iterable[tuple[str, str]]) -> str:
    items = []
    for name, content in sources:
        items.append(f"来源：{name}\n{content}")
    if not items:
        return ""
    return "资料：\n" + "\n\n".join(items) + "\n"


def format_history(history: Iterable[ChatMessage]) -> str:
    lines = []
    for msg in history:
        role = msg.get("role", "user")
        label = "用户" if role == "user" else "助手"
        lines.append(f"{label}：{msg.get('content', '')}")
    if not lines:
        return ""
    return "对话历史：\n" + "\n".join(lines) + "\n"


@dataclass
class TemplateManager:
    """Prompt 模板管理器"""

    templates: Dict[str, str] = field(default_factory=dict)
    active: str = "default"
    fallback: str = DEFAULT_PROMPT_TEMPLATE

    def get_template(self) -> str:
        if self.active and self.active in self.templates:
            return self.templates[self.active]
        if self.templates.get("default"):
            return self.templates["default"]
        return self.fallback

    def render(self, variables: Mapping[str, str]) -> str:
        template = self.get_template()
        return template.format_map(_SafeDict(variables))
