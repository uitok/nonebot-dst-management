"""
AI 存档分析命令处理器

提供 /dst archive analyze <文件> 命令。
"""

from __future__ import annotations

from nonebot import on_command
from nonebot.adapters.onebot.v11 import MessageEvent, Message
from nonebot.params import CommandArg

from ..ai.archive_analyzer import ArchiveAnalyzer
from ..ai.base import AIError, format_ai_error
from ..ai.client import AIClient
from ..services.archive_service import ArchiveService
from ..utils.permission import check_group
from ..utils.formatter import format_error, format_info


def init(ai_client: AIClient) -> None:
    """
    初始化 AI 存档分析命令

    Args:
        ai_client: AI 客户端实例
    """

    analyzer = ArchiveAnalyzer(ai_client)
    service = ArchiveService()

    analyze_cmd = on_command("dst archive analyze", priority=10, block=True)

    @analyze_cmd.handle()
    async def handle_archive_analyze(event: MessageEvent, args: Message = CommandArg()):
        if not await check_group(event):
            await analyze_cmd.finish(format_error("当前群组未授权使用此功能"))
            return

        source = args.extract_plain_text().strip()
        if not source:
            await analyze_cmd.finish(format_error("用法：/dst archive analyze <文件URL或文件路径>"))
            return

        await analyze_cmd.send(format_info("正在准备存档文件..."))
        prepared = await service.prepare_archive(source)
        if not prepared.get("success"):
            await analyze_cmd.finish(format_error(prepared.get("error", "文件处理失败")))
            return

        archive_path = prepared["path"]
        cleanup = prepared.get("cleanup", False)

        try:
            with open(archive_path, "rb") as f:
                content = f.read()

            await analyze_cmd.send(format_info("正在分析存档..."))
            report = await analyzer.analyze_archive(content)
            await analyze_cmd.finish(Message(report))
        except AIError as exc:
            await analyze_cmd.finish(format_error(format_ai_error(exc)))
        except Exception as exc:
            await analyze_cmd.finish(format_error(f"分析失败：{exc}"))
        finally:
            if cleanup:
                service.cleanup_file(archive_path)
