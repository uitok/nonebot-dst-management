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

        question = args.extract_plain_text().strip()
        if not question:
            await ask_cmd.finish(format_error("用法：/dst ask <问题>"))
            return

        await ask_cmd.send(format_info("正在生成回答..."))
        try:
            answer = await qa_system.ask(question)
        except AIError as exc:
            await ask_cmd.finish(format_error(format_ai_error(exc)))
            return
        except Exception as exc:
            await ask_cmd.finish(format_error(f"问答失败：{exc}"))
            return

        await ask_cmd.finish(Message(answer))
