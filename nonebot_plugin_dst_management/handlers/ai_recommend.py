"""
AI 模组推荐命令处理器

提供 /dst mod recommend <房间ID> [类型] 命令。
"""

from __future__ import annotations

from nonebot import on_command
from nonebot.adapters.onebot.v11 import MessageEvent, Message
from nonebot.params import CommandArg

from ..ai.recommender import ModRecommender
from ..ai.base import AIError, format_ai_error
from ..ai.client import AIClient
from ..client.api_client import DSTApiClient
from ..utils.permission import check_group
from ..utils.formatter import format_error, format_info


def init(api_client: DSTApiClient, ai_client: AIClient) -> None:
    """
    初始化 AI 模组推荐命令

    Args:
        api_client: DMP API 客户端实例
        ai_client: AI 客户端实例
    """

    recommender = ModRecommender(api_client, ai_client)

    recommend_cmd = on_command("dst mod recommend", priority=10, block=True)

    @recommend_cmd.handle()
    async def handle_recommend(event: MessageEvent, args: Message = CommandArg()):
        if not await check_group(event):
            await recommend_cmd.finish(format_error("当前群组未授权使用此功能"))
            return

        raw = args.extract_plain_text().strip()
        if not raw:
            await recommend_cmd.finish(format_error("用法：/dst mod recommend <房间ID> [类型]"))
            return

        parts = raw.split()
        room_id_str = parts[0]
        mod_type = parts[1] if len(parts) > 1 else None

        if not room_id_str.isdigit():
            await recommend_cmd.finish(format_error("请提供有效的房间ID"))
            return

        room_id = int(room_id_str)
        await recommend_cmd.send(format_info(f"正在生成房间 {room_id} 的模组推荐..."))

        try:
            result = await recommender.recommend_mods(room_id, mod_type)
        except AIError as exc:
            await recommend_cmd.finish(format_error(format_ai_error(exc)))
            return
        except Exception as exc:
            await recommend_cmd.finish(format_error(f"推荐失败：{exc}"))
            return

        report = result.get("report", "")
        await recommend_cmd.finish(Message(report))
