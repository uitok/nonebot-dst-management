"""
AI 智能问答命令处理器

提供 /dst ask <问题> 命令。
"""

from __future__ import annotations

from nonebot import on_command
from nonebot.adapters.onebot.v11 import MessageEvent, Message
from nonebot.params import CommandArg

from ..ai.qa import QASystem
from ..ai.base import AIError, format_ai_error
from ..ai.client import AIClient
from ..utils.permission import check_group
from ..utils.formatter import format_error, format_info


def _build_session_id(event: MessageEvent) -> str:
    user_id = getattr(event, "user_id", "unknown")
    group_id = getattr(event, "group_id", None)
    if group_id is not None:
        return f"group:{group_id}:user:{user_id}"
    return f"user:{user_id}"


def init(ai_client: AIClient) -> None:
    """
    初始化 AI 问答命令

    Args:
        ai_client: AI 客户端实例
    """

    qa_system = QASystem(ai_client)

    ask_cmd = on_command("dst ask", priority=10, block=True)

    @ask_cmd.handle()
    async def handle_ask(event: MessageEvent, args: Message = CommandArg()):
        if not await check_group(event):
            await ask_cmd.finish(format_error("当前群组未授权使用此功能"))
            return

        raw = args.extract_plain_text().strip()
        if not raw:
            await ask_cmd.finish(format_error("用法：/dst ask <问题>"))
            return

        stream = False
        if raw.startswith("--stream"):
            stream = True
            raw = raw[len("--stream"):].strip()
        elif raw.startswith("-s"):
            stream = True
            raw = raw[2:].strip()

        question = raw.strip()
        if not question:
            await ask_cmd.finish(format_error("用法：/dst ask <问题>"))
            return

        session_id = _build_session_id(event)

        if question in {"reset", "清除", "重置"}:
            qa_system.reset_session(session_id)
            await ask_cmd.finish(format_info("已清空当前会话上下文"))
            return

        await ask_cmd.send(format_info("正在生成回答..."))
        try:
            if stream:
                buffer = ""
                chunk_size = max(1, ai_client.config.stream_chunk_size)
                async for chunk in qa_system.ask_stream(question, session_id=session_id):
                    buffer += chunk
                    if len(buffer) >= chunk_size:
                        await ask_cmd.send(Message(buffer))
                        buffer = ""
                if buffer:
                    await ask_cmd.finish(Message(buffer))
                    return
                await ask_cmd.finish(format_info("回答完成"))
                return
            answer = await qa_system.ask(question, session_id=session_id)
        except AIError as exc:
            await ask_cmd.finish(format_error(format_ai_error(exc)))
            return
        except Exception as exc:
            await ask_cmd.finish(format_error(f"问答失败：{exc}"))
            return

        await ask_cmd.finish(Message(answer))
