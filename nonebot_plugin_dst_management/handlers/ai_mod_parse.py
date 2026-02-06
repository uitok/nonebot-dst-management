"""
AI 模组配置解析命令处理器

提供 /dst mod parse <房间ID> <世界ID> 命令。
"""

from __future__ import annotations

from nonebot import on_command
from nonebot.adapters.onebot.v11 import MessageEvent, Message
from nonebot.params import CommandArg

from ..ai.mod_parser import ModConfigParser
from ..ai.base import AIError, format_ai_error
from ..ai.client import AIClient
from ..client.api_client import DSTApiClient
from ..utils.permission import check_group
from ..utils.formatter import format_error, format_info


def init(api_client: DSTApiClient, ai_client: AIClient) -> None:
    """
    初始化 AI 模组配置解析命令

    Args:
        api_client: DMP API 客户端实例
        ai_client: AI 客户端实例
    """

    parser = ModConfigParser(api_client, ai_client)

    parse_cmd = on_command("dst mod parse", priority=10, block=True)

    @parse_cmd.handle()
    async def handle_parse(event: MessageEvent, args: Message = CommandArg()):
        if not await check_group(event):
            await parse_cmd.finish(format_error("当前群组未授权使用此功能"))
            return

        raw = args.extract_plain_text().strip()
        if not raw:
            await parse_cmd.finish(format_error("用法：/dst mod parse <房间ID> <世界ID>"))
            return

        parts = raw.split()
        if len(parts) < 2:
            await parse_cmd.finish(format_error("用法：/dst mod parse <房间ID> <世界ID>"))
            return

        room_id_str, world_id = parts[0], parts[1]
        if not room_id_str.isdigit():
            await parse_cmd.finish(format_error("请提供有效的房间ID"))
            return

        room_id = int(room_id_str)
        await parse_cmd.send(format_info(f"正在解析房间 {room_id} - 世界 {world_id} 配置..."))

        try:
            result = await parser.parse_mod_config(room_id, world_id)
        except AIError as exc:
            await parse_cmd.finish(format_error(format_ai_error(exc)))
            return
        except Exception as exc:
            await parse_cmd.finish(format_error(f"解析失败：{exc}"))
            return

        report = result.get("report", "")
        await parse_cmd.finish(Message(report))
