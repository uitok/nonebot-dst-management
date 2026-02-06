"""
签到命令处理器

处理绑定、签到与解绑命令：
- /dst sign bind
- /dst sign
- /dst sign unbind
"""

from __future__ import annotations

from typing import Optional

from nonebot import on_command
from nonebot.adapters.onebot.v11 import MessageEvent, Message
from nonebot.params import CommandArg

from ..client.api_client import DSTApiClient
from ..helpers.commands import parse_room_id
from ..helpers.room_context import remember_room, resolve_room_id
from ..services.monitors.sign_monitor import get_sign_monitor
from ..services.sign_service import SignService
from ..utils.formatter import format_error, format_info, format_success
from ..utils.permission import check_group


async def _resolve_room_id(event: MessageEvent, room_arg: Optional[str]) -> Optional[int]:
    resolved = await resolve_room_id(event, room_arg)
    return int(resolved.room_id) if resolved is not None else None


def init(api_client: DSTApiClient):
    """
    初始化签到命令

    Args:
        api_client: DMP API 客户端实例
    """
    service = SignService(api_client)

    sign_bind_cmd = on_command(
        "dst sign bind",
        aliases={"dst 签到绑定"},
        priority=10,
        block=True,
    )

    @sign_bind_cmd.handle()
    async def handle_sign_bind(event: MessageEvent, args: Message = CommandArg()):
        if not await check_group(event):
            await sign_bind_cmd.finish(format_error("当前群组未授权使用此功能"))
            return

        text = args.extract_plain_text().strip()
        parts = text.split()
        if not parts:
            await sign_bind_cmd.finish(format_error("用法：/dst sign bind <KU_ID> [房间ID]"))
            return

        ku_id = parts[0]
        room_arg = parts[1] if len(parts) > 1 else None
        room_id = await _resolve_room_id(event, room_arg)
        if room_id is None:
            await sign_bind_cmd.finish(format_error("请提供房间ID，或先使用一次带房间ID的命令以锁定房间，或设置默认房间"))
            return

        result = await service.bind_user(str(event.user_id), ku_id, room_id)
        if not result.success:
            await sign_bind_cmd.finish(format_error(result.message))
            return

        await remember_room(event, room_id)
        await sign_bind_cmd.finish(format_success(f"{result.message}，房间ID：{room_id}"))

    sign_unbind_cmd = on_command(
        "dst sign unbind",
        aliases={"dst 签到解绑"},
        priority=10,
        block=True,
    )

    @sign_unbind_cmd.handle()
    async def handle_sign_unbind(event: MessageEvent, args: Message = CommandArg()):
        if not await check_group(event):
            await sign_unbind_cmd.finish(format_error("当前群组未授权使用此功能"))
            return

        text = args.extract_plain_text().strip()
        room_id = await _resolve_room_id(event, text if text else None)
        if room_id is None:
            await sign_unbind_cmd.finish(format_error("请提供房间ID，或先使用一次带房间ID的命令以锁定房间，或设置默认房间"))
            return

        await sign_unbind_cmd.send(format_info("正在解绑..."))
        if not hasattr(service, "unbind_user"):
            await sign_unbind_cmd.finish(format_error("当前服务不支持解绑"))
            return

        result = await service.unbind_user(str(event.user_id), room_id)
        if not result.success:
            await sign_unbind_cmd.finish(format_error(result.message))
            return

        await remember_room(event, room_id)
        await sign_unbind_cmd.finish(format_success(f"{result.message}，房间ID：{room_id}"))

    sign_cmd = on_command(
        "dst sign",
        aliases={"dst 签到"},
        priority=10,
        block=True,
    )

    @sign_cmd.handle()
    async def handle_sign(event: MessageEvent, args: Message = CommandArg()):
        if not await check_group(event):
            await sign_cmd.finish(format_error("当前群组未授权使用此功能"))
            return

        text = args.extract_plain_text().strip()
        if text.startswith("bind"):
            await sign_cmd.finish(format_info("请使用 /dst sign bind <KU_ID> [房间ID] 进行绑定"))
            return
        if text.startswith("unbind"):
            await sign_cmd.finish(format_info("请使用 /dst sign unbind [房间ID] 进行解绑"))
            return

        room_id = None
        if text:
            room_id = parse_room_id(text)
            if room_id is None:
                await sign_cmd.finish(format_error("请提供有效的房间ID"))
                return
        else:
            room_id = await _resolve_room_id(event, None)

        if room_id is None:
            await sign_cmd.finish(format_error("请提供房间ID，或先使用一次带房间ID的命令以锁定房间，或设置默认房间"))
            return

        await sign_cmd.send(format_info("正在签到..."))
        result = await service.sign_in(str(event.user_id), room_id)
        if not result.success:
            await sign_cmd.finish(format_error(result.message))
            return

        # ✨ 触发签到奖励补发检查
        monitor = get_sign_monitor()
        if monitor and result.user:
            try:
                await monitor.check_user_pending_rewards(
                    str(event.user_id),
                    result.user.ku_id,
                    room_id,
                )
            except Exception:
                pass

        await remember_room(event, room_id)
        await sign_cmd.finish(format_success(result.message))
