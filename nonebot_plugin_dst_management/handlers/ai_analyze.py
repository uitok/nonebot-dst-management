"""
AI 配置分析命令处理器

提供 /dst analyze <房间ID> 命令。
"""

from __future__ import annotations

from nonebot import on_command
from nonebot.adapters.onebot.v11 import MessageEvent, Message
from nonebot.params import CommandArg

from ..ai.analyzer import ServerConfigAnalyzer
from ..ai.base import AIError, format_ai_error
from ..ai.client import AIClient
from ..client.api_client import DSTApiClient
from ..utils.formatter import format_error, format_info


def init(api_client: DSTApiClient, ai_client: AIClient) -> None:
    """
    初始化 AI 配置分析命令

    Args:
        api_client: DMP API 客户端实例
        ai_client: AI 客户端实例
    """

    analyzer = ServerConfigAnalyzer(api_client, ai_client)

    analyze_cmd = on_command("dst analyze", priority=10, block=True)

    @analyze_cmd.handle()
    async def handle_analyze(event: MessageEvent, args: Message = CommandArg()):
        room_id_str = args.extract_plain_text().strip()
        if not room_id_str.isdigit():
            await analyze_cmd.finish(format_error("请提供有效的房间ID：/dst analyze <房间ID>"))
            return

        room_id = int(room_id_str)
        await analyze_cmd.send(format_info(f"正在分析房间 {room_id} 配置..."))

        try:
            report = await analyzer.analyze_server(room_id)
        except AIError as exc:
            await analyze_cmd.finish(format_error(format_ai_error(exc)))
            return
        except Exception as exc:
            await analyze_cmd.finish(format_error(f"分析失败：{exc}"))
            return

        await analyze_cmd.finish(Message(report))
