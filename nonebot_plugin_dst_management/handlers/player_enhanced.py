"""
玩家管理命令处理器（增强版：触发签到奖励检查）
"""

from __future__ import annotations

from typing import Optional

from nonebot import on_command
from nonebot.adapters.onebot.v11 import MessageEvent, Message
from nonebot.params import CommandArg

from ..client.api_client import DSTApiClient
from ..helpers.commands import escape_console_string, parse_room_id
from ..services.monitors.sign_monitor import get_sign_monitor
from ..helpers.formatters import render_auto
from ..utils.formatter import format_error, format_info
from ..utils.permission import check_group
from . import default_room


async def _resolve_room_id(event: MessageEvent, room_arg: Optional[str]) -> Optional[int]:
    """解析房间ID"""
    qq_id = str(event.user_id)
    return await default_room.resolve_room_id(qq_id, room_arg)


def init(api_client: DSTApiClient):
    """初始化玩家管理命令"""

    player_online_cmd = on_command(
        "dst player online",
        aliases={"dst players"},
        priority=10,
        block=True,
    )

    @player_online_cmd.handle()
    async def handle_player_online(event: MessageEvent, args: Message = CommandArg()):
        """查看在线玩家"""
        if not await check_group(event):
            await player_online_cmd.finish(format_error("当前群组未授权使用此功能"))
            return

        room_arg = args.extract_plain_text().strip()
        room_id = parse_room_id(room_arg) if room_arg else None

        if room_id is None:
            room_id = await _resolve_room_id(event, None)

        if room_id is None:
            await player_online_cmd.finish(format_error("请提供房间ID或先设置默认房间"))
            return

        result = await api_client.get_online_players(room_id)
        if not result.get("success"):
            await player_online_cmd.finish(format_error(f"获取失败：{result.get('error')}"))
            return

        players = result.get("data") or []
        if not players:
            await player_online_cmd.finish(format_info("当前没有玩家在线"))
            return

        # ✨ 触发签到奖励检查
        monitor = get_sign_monitor()
        if monitor:
            try:
                await monitor.check_room_pending_rewards(room_id)
            except Exception as e:
                # 检查失败不影响主流程
                pass

        # 格式化玩家列表
        headers = ["KU_ID", "昵称", "在线时长"]
        rows = []
        for p in players:
            ku_id = p.get("uid", "未知")
            name = escape_console_string(p.get("name", "未知"))
            duration = p.get("duration", 0)
            hours = duration // 3600
            minutes = (duration % 3600) // 60
            duration_text = f"{hours}h {minutes}m"
            rows.append([ku_id, name, duration_text])

        message = await render_auto("table", event=event, headers=headers, rows=rows)
        await player_online_cmd.finish(message)


__all__ = ["init"]
