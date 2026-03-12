"""
签到命令 (on_alconna 版本)

使用 nonebot-plugin-alconna 的 on_alconna 匹配器。
"""

from __future__ import annotations

from typing import Any, Optional

from arclet.alconna import Alconna, Args, CommandMeta
from nonebot.internal.adapter import Event

from nonebot_plugin_alconna import Match, AlconnaMatch, on_alconna

from ..client.api_client import DSTApiClient
from ..utils.permission import ADMIN_PERMISSION, USER_PERMISSION
from ..helpers.formatters import format_error, format_info, format_success
from ..helpers.room_context import remember_room, resolve_room_id
from ..services.monitors.sign_monitor import get_sign_monitor
from ..services.sign_service import SignService


# 全局 API 客户端，由 init 函数设置
_api_client: Optional[DSTApiClient] = None


def get_api_client() -> DSTApiClient:
    """获取 API 客户端"""
    if _api_client is None:
        raise RuntimeError("API 客户端未初始化，请先调用 init() 函数")
    return _api_client


# 全局 Sign Service
_sign_service: Optional[SignService] = None


def get_sign_service() -> SignService:
    """获取签到服务"""
    if _sign_service is None:
        raise RuntimeError("签到服务未初始化，请先调用 init() 函数")
    return _sign_service


def _extract_user_id(event: Any) -> Optional[str]:
    """从事件中提取用户 ID（兼容不同适配器）"""
    if event is None:
        return None
    get_user_id = getattr(event, "get_user_id", None)
    if callable(get_user_id):
        try:
            value = get_user_id()
            return str(value) if value else None
        except Exception:
            pass
    user_id = getattr(event, "user_id", None)
    return str(user_id) if user_id is not None else None


async def _resolve_room_id(event: Event, room_arg: Optional[str]) -> Optional[int]:
    """解析房间 ID"""
    resolved = await resolve_room_id(event, room_arg)
    return int(resolved.room_id) if resolved is not None else None


# ========== 命令定义 + on_alconna 匹配器 ==========

sign_bind_command = Alconna(
    "dst sign bind",
    Args["ku_id", str]["room_id", str, None],
    meta=CommandMeta(
        description="绑定签到账号",
        usage="/dst sign bind <KU_ID> [房间ID]",
        example="/dst sign bind ku_123456 1",
    ),
)

sign_unbind_command = Alconna(
    "dst sign unbind",
    Args["room_id", str, None],
    meta=CommandMeta(
        description="解绑签到账号",
        usage="/dst sign unbind [房间ID]",
        example="/dst sign unbind 1",
    ),
)

sign_command = Alconna(
    "dst sign",
    Args["room_id", str, None],
    meta=CommandMeta(
        description="签到",
        usage="/dst sign [房间ID]",
        example="/dst sign 1",
    ),
)

# ========== on_alconna 匹配器 ==========

sign_bind_matcher = on_alconna(sign_bind_command, permission=USER_PERMISSION, priority=10, block=True)
sign_unbind_matcher = on_alconna(sign_unbind_command, permission=USER_PERMISSION, priority=10, block=True)
sign_matcher = on_alconna(sign_command, permission=USER_PERMISSION, priority=10, block=True)


# ========== 命令处理函数 ==========

@sign_bind_matcher.handle()
async def handle_sign_bind(
    event: Event,
    ku_id: Match[str] = AlconnaMatch("ku_id"),
    room_id: Match[str] = AlconnaMatch("room_id"),
) -> None:
    """处理签到绑定命令"""
    if not ku_id.available:
        await sign_bind_matcher.finish(format_error("用法：/dst sign bind <KU_ID> [房间ID]"))
        return

    room_id_val = room_id.result if room_id.available else None
    actual_room_id = await _resolve_room_id(event, room_id_val)
    if actual_room_id is None:
        await sign_bind_matcher.finish(format_error("请提供房间ID，或先使用一次带房间ID的命令以锁定房间，或设置默认房间"))
        return

    service = get_sign_service()
    result = await service.bind_user(_extract_user_id(event) or "", ku_id.result, actual_room_id)
    if not result.success:
        await sign_bind_matcher.finish(format_error(result.message))
        return

    await remember_room(event, actual_room_id)
    await sign_bind_matcher.finish(format_success(f"{result.message}，房间ID：{actual_room_id}"))


@sign_unbind_matcher.handle()
async def handle_sign_unbind(
    event: Event,
    room_id: Match[str] = AlconnaMatch("room_id"),
) -> None:
    """处理签到解绑命令"""
    room_id_val = room_id.result if room_id.available else None
    actual_room_id = await _resolve_room_id(event, room_id_val)
    if actual_room_id is None:
        await sign_unbind_matcher.finish(format_error("请提供房间ID，或先使用一次带房间ID的命令以锁定房间，或设置默认房间"))
        return

    await sign_unbind_matcher.send(format_info("正在解绑..."))
    service = get_sign_service()
    if not hasattr(service, "unbind_user"):
        await sign_unbind_matcher.finish(format_error("当前服务不支持解绑"))
        return

    result = await service.unbind_user(_extract_user_id(event) or "", actual_room_id)
    if not result.success:
        await sign_unbind_matcher.finish(format_error(result.message))
        return

    await remember_room(event, actual_room_id)
    await sign_unbind_matcher.finish(format_success(f"{result.message}，房间ID：{actual_room_id}"))


@sign_matcher.handle()
async def handle_sign(
    event: Event,
    room_id: Match[str] = AlconnaMatch("room_id"),
) -> None:
    """处理签到命令"""
    room_id_val = room_id.result if room_id.available else None
    actual_room_id = await _resolve_room_id(event, room_id_val)

    if actual_room_id is None:
        await sign_matcher.finish(format_error("请提供房间ID，或先使用一次带房间ID的命令以锁定房间，或设置默认房间"))
        return

    await sign_matcher.send(format_info("正在签到..."))
    service = get_sign_service()
    result = await service.sign_in(_extract_user_id(event) or "", actual_room_id)
    if not result.success:
        await sign_matcher.finish(format_error(result.message))
        return

    # 触发签到奖励补发检查
    monitor = get_sign_monitor()
    if monitor and result.user:
        try:
            await monitor.check_user_pending_rewards(
                _extract_user_id(event) or "",
                result.user.ku_id,
                actual_room_id,
            )
        except Exception:
            pass

    await remember_room(event, actual_room_id)
    await sign_matcher.finish(format_success(result.message))


def init(api_client: DSTApiClient) -> None:
    """初始化签到命令"""
    global _api_client, _sign_service
    _api_client = api_client
    _sign_service = SignService(api_client)


__all__ = [
    "sign_bind_command",
    "sign_unbind_command",
    "sign_command",
    "sign_bind_matcher",
    "sign_unbind_matcher",
    "sign_matcher",
    "handle_sign_bind",
    "handle_sign_unbind",
    "handle_sign",
    "init",
]
