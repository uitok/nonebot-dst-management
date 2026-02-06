"""
DST AI 智能问答系统

基于项目文档与 DST 基础知识生成问答。
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Sequence

from loguru import logger

from .base import AIError, format_ai_error
from .client import AIClient
from .prompt import TemplateManager, format_history, format_sources
from .session import SessionManager


@dataclass(frozen=True)
class KnowledgeSource:
    """知识库来源"""

    name: str
    content: str


class QASystem:
    """AI 问答系统"""

    def __init__(
        self,
        ai_client: AIClient,
        docs_root: Optional[Path] = None,
        session_manager: Optional[SessionManager] = None,
        template_manager: Optional[TemplateManager] = None,
    ) -> None:
        self.ai_client = ai_client
        self.docs_root = docs_root or Path(__file__).resolve().parents[2]
        self.session_manager = session_manager or SessionManager(
            max_rounds=ai_client.config.session_max_rounds,
            ttl_seconds=ai_client.config.session_ttl,
        )
        self.template_manager = template_manager or self._build_template_manager()

    async def ask(
        self,
        question: str,
        context: Optional[str] = None,
        session_id: Optional[str] = None,
    ) -> str:
        """
        执行问答

        Args:
            question: 用户问题
            context: 可选上下文
            session_id: 会话 ID

        Returns:
            str: Markdown 格式回答
        """
        sources = self._build_knowledge_base(context)
        history = self.session_manager.list_history(session_id) if session_id else []
        prompt = self._build_prompt(question, sources, history, context)
        system_prompt = self._system_prompt()

        try:
            response = await self.ai_client.chat(
                [{"role": "user", "content": prompt}],
                system_prompt=system_prompt,
            )
            if response and response.strip():
                answer = response.strip()
                if session_id:
                    self.session_manager.append_turn(session_id, question, answer)
                return answer
        except AIError as exc:
            logger.warning("AI 问答失败，回退本地回答：{err}", err=exc)
            return self._fallback_answer(question, sources, exc)
        except Exception as exc:
            logger.exception("AI 问答发生未知错误：{err}", err=exc)
            return self._fallback_answer(question, sources, exc)

        return self._fallback_answer(question, sources, None)

    async def ask_stream(
        self,
        question: str,
        context: Optional[str] = None,
        session_id: Optional[str] = None,
    ):
        sources = self._build_knowledge_base(context)
        history = self.session_manager.list_history(session_id) if session_id else []
        prompt = self._build_prompt(question, sources, history, context)
        system_prompt = self._system_prompt()

        response_parts: List[str] = []
        try:
            async for chunk in self.ai_client.stream_chat(
                [{"role": "user", "content": prompt}],
                system_prompt=system_prompt,
            ):
                if chunk:
                    response_parts.append(chunk)
                    yield chunk
        except AIError as exc:
            logger.warning("AI 流式问答失败，回退本地回答：{err}", err=exc)
            yield self._fallback_answer(question, sources, exc)
            return
        except Exception as exc:
            logger.exception("AI 流式问答发生未知错误：{err}", err=exc)
            yield self._fallback_answer(question, sources, exc)
            return

        answer = "".join(response_parts).strip()
        if not answer:
            yield self._fallback_answer(question, sources, None)
            return
        if session_id:
            self.session_manager.append_turn(session_id, question, answer)

    def reset_session(self, session_id: str) -> None:
        self.session_manager.reset_session(session_id)

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

    def _build_prompt(
        self,
        question: str,
        sources: Sequence[KnowledgeSource],
        history: Sequence[dict[str, str]],
        context: Optional[str],
    ) -> str:
        sources_text = format_sources([(source.name, source.content) for source in sources])
        history_text = format_history(history)
        context_text = f"补充上下文：\n{context}\n" if context else ""
        variables = {
            "question": question,
            "sources": sources_text,
            "history": history_text,
            "context": context_text,
        }
        return self.template_manager.render(variables)

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

    def _build_template_manager(self) -> TemplateManager:
        config = self.ai_client.config
        templates = dict(config.prompt_templates)
        if config.prompt_template:
            templates["custom"] = config.prompt_template
        if config.prompt_template and config.prompt_active == "default":
            active = "custom"
        else:
            active = config.prompt_active or ("custom" if config.prompt_template else "default")
        return TemplateManager(templates=templates, active=active)


_DST_BASICS = (
    "DST 基础知识：\n"
    "- Master 为主世界，Caves 为洞穴世界。\n"
    "- modoverrides.lua 用于配置服务器模组。\n"
    "- 修改配置后通常需要重启房间才能生效。\n"
)
