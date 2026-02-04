"""
DST AI 智能问答系统

基于项目文档与 DST 基础知识生成问答。
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, List, Optional, Sequence

from loguru import logger

from .base import AIError, format_ai_error
from .client import AIClient


@dataclass(frozen=True)
class KnowledgeSource:
    """知识库来源"""

    name: str
    content: str


class QASystem:
    """AI 问答系统"""

    def __init__(self, ai_client: AIClient, docs_root: Optional[Path] = None) -> None:
        self.ai_client = ai_client
        self.docs_root = docs_root or Path(__file__).resolve().parents[2]

    async def ask(self, question: str, context: Optional[str] = None) -> str:
        """
        执行问答

        Args:
            question: 用户问题
            context: 可选上下文

        Returns:
            str: Markdown 格式回答
        """
        sources = self._build_knowledge_base(context)
        prompt = self._build_prompt(question, sources)
        system_prompt = self._system_prompt()

        try:
            response = await self.ai_client.chat(
                [{"role": "user", "content": prompt}],
                system_prompt=system_prompt,
            )
            if response and response.strip():
                return response.strip()
        except AIError as exc:
            logger.warning("AI 问答失败，回退本地回答：{err}", err=exc)
            return self._fallback_answer(question, sources, exc)
        except Exception as exc:
            logger.exception("AI 问答发生未知错误：{err}", err=exc)
            return self._fallback_answer(question, sources, exc)

        return self._fallback_answer(question, sources, None)

    def _build_knowledge_base(self, extra_context: Optional[str]) -> List[KnowledgeSource]:
        sources: List[KnowledgeSource] = []
        doc_paths = [
            self.docs_root / "README.md",
            self.docs_root / "COMMANDS.md",
            self.docs_root / "AI_COMPLETE_PLAN.md",
        ]

        for path in doc_paths:
            if not path.exists():
                continue
            try:
                content = path.read_text(encoding="utf-8")
            except Exception:
                continue
            if len(content) > 6000:
                content = content[:6000] + "\n..."
            sources.append(KnowledgeSource(name=path.name, content=content))

        sources.append(KnowledgeSource(name="DST basics", content=_DST_BASICS))

        if extra_context:
            sources.append(KnowledgeSource(name="User context", content=extra_context))

        return sources

    def _build_prompt(self, question: str, sources: Sequence[KnowledgeSource]) -> str:
        payload = {
            "question": question,
            "sources": [
                {
                    "name": source.name,
                    "content": source.content,
                }
                for source in sources
            ],
        }

        return (
            "你是 DST 管理插件的智能助手，请根据知识库回答用户问题。\n\n"
            f"输入数据(JSON)：\n{json.dumps(payload, ensure_ascii=True, indent=2)}\n\n"
            "要求：\n"
            "1. 使用 Markdown 输出回答。\n"
            "2. 给出清晰的结论与可执行步骤。\n"
            "3. 在回答末尾列出引用来源（名称即可）。\n"
        )

    def _system_prompt(self) -> str:
        return "你是 DST 服务器与管理插件专家，回答时严谨且可执行。"

    def _fallback_answer(
        self,
        question: str,
        sources: Sequence[KnowledgeSource],
        error: Optional[Exception],
    ) -> str:
        lines = ["🤖 智能问答", "", f"问题：{question}", "", "当前无法获得 AI 答复。"]
        lines.append("可参考以下资料：")
        for source in sources:
            lines.append(f"- {source.name}")
        if error is not None:
            lines.append("")
            if isinstance(error, AIError):
                lines.append(f"⚠️ AI 问答失败：{format_ai_error(error)}")
            else:
                lines.append(f"⚠️ AI 问答失败：{error}")
        return "\n".join(lines)


_DST_BASICS = (
    "DST 基础知识：\n"
    "- Master 为主世界，Caves 为洞穴世界。\n"
    "- modoverrides.lua 用于配置服务器模组。\n"
    "- 修改配置后通常需要重启房间才能生效。\n"
)
