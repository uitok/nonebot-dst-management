"""
默认房间命令处理器

处理用户默认房间设置：设置、清除、查看
"""

from typing import Optional

from loguru import logger
from nonebot import on_command
from nonebot.adapters.onebot.v11 import Bot, MessageEvent, Message
from nonebot.params import CommandArg

from ..client.api_client import DSTApiClient
from ..utils.permission import check_group
from ..utils.formatter import format_success, format_error, format_info


# 存储 key 前缀
STORAGE_KEY_PREFIX = "dst_default_room"


def get_storage_key(session_id: str) -> str:
    """
    获取用户存储 key

    Args:
        session_id: 会话 ID（包含用户 ID 和群 ID）

    Returns:
        str: 存储 key
    """
    return f"{STORAGE_KEY_PREFIX}:{session_id}"


def get_default_room(storage_data: dict, session_id: str) -> Optional[int]:
    """
    获取用户默认房间

    Args:
        storage_data: 存储数据字典
        session_id: 会话 ID

    Returns:
        Optional[int]: 默认房间 ID，未设置返回 None
    """
    key = get_storage_key(session_id)
    return storage_data.get(key)


def set_default_room(storage_data: dict, session_id: str, room_id: int) -> None:
    """
    设置用户默认房间

    Args:
        storage_data: 存储数据字典
        session_id: 会话 ID
        room_id: 房间 ID
    """
    key = get_storage_key(session_id)
    storage_data[key] = room_id
    logger.debug(f"设置默认房间: session={session_id}, room_id={room_id}")


def clear_default_room(storage_data: dict, session_id: str) -> None:
    """
    清除用户默认房间

    Args:
        storage_data: 存储数据字典
        session_id: 会话 ID
    """
    key = get_storage_key(session_id)
    room_id = storage_data.pop(key, None)
    logger.debug(f"清除默认房间: session={session_id}, room_id={room_id}")


def resolve_room_id(
    storage_data: dict,
    session_id: str,
    room_id_arg: Optional[str],
) -> Optional[int]:
    """
    解析房间 ID（支持默认房间）

    如果 room_id_arg 为 None，则使用默认房间

    Args:
        storage_data: 存储数据字典
        session_id: 会话 ID
        room_id_arg: 房间 ID 参数

    Returns:
        Optional[int]: 房间 ID，解析失败返回 None
    """
    if room_id_arg is not None:
        try:
            room_id = int(room_id_arg)
            if room_id <= 0:
                logger.warning(f"无效的房间 ID: {room_id_arg}")
                return None
            return room_id
        except (ValueError, TypeError):
            logger.warning(f"房间 ID 解析失败: {room_id_arg}")
            return None

    # 使用默认房间
    return get_default_room(storage_data, session_id)


# 全局存储（简单实现，后续可替换为 localstore）
_storage: dict = {}


def get_storage() -> dict:
    """获取存储字典"""
    return _storage


# 全局 API 客户端（用于房间验证）
_api_client: Optional[DSTApiClient] = None


def get_api_client() -> Optional[DSTApiClient]:
    """获取 API 客户端"""
    return _api_client


# 命令注册
cmd_set = on_command("dst 默认房间", priority=5, block=True)
cmd_clear = on_command("dst 清除默认", priority=5, block=True)
cmd_show = on_command("dst 查看默认", priority=5, block=True)


@cmd_set.handle()
async def handle_set_default(
    bot: Bot,
    event: MessageEvent,
    args: Message = CommandArg(),
):
    """设置默认房间"""
    if not await check_group(event):
        await cmd_set.finish(format_error("权限不足"))

    room_id_str = args.extract_plain_text().strip()

    if not room_id_str:
        await cmd_set.finish(format_error("用法：/dst 默认房间 <房间ID>"))

    try:
        room_id = int(room_id_str)
        if room_id <= 0:
            await cmd_set.finish(format_error("房间 ID 必须是正整数"))
    except ValueError:
        await cmd_set.finish(format_error("房间 ID 必须是数字"))

    # 验证房间是否存在
    api_client = get_api_client()
    if api_client:
        try:
            room_info = await api_client.get_room_info(room_id)
            if not room_info or not room_info.get("success"):
                await cmd_set.finish(format_error(f"房间 {room_id} 不存在"))
        except Exception as e:
            logger.error(f"验证房间失败: {e}")
            await cmd_set.finish(format_error(f"验证房间失败: {e}"))

    # 获取会话 ID（包含用户 ID 和群 ID）
    session_id = event.get_session_id()

    # 设置默认房间
    storage = get_storage()
    set_default_room(storage, session_id, room_id)

    logger.info(f"用户 {session_id} 设置默认房间为 {room_id}")
    await cmd_set.finish(format_success(f"已设置默认房间为 {room_id}"))


@cmd_clear.handle()
async def handle_clear_default(
    bot: Bot,
    event: MessageEvent,
):
    """清除默认房间"""
    if not await check_group(event):
        await cmd_clear.finish(format_error("权限不足"))

    # 获取会话 ID
    session_id = event.get_session_id()

    # 清除默认房间
    storage = get_storage()
    default_room = get_default_room(storage, session_id)

    if default_room is None:
        await cmd_clear.finish(format_info("未设置默认房间"))

    clear_default_room(storage, session_id)

    logger.info(f"用户 {session_id} 清除默认房间（原房间：{default_room}）")
    await cmd_clear.finish(format_success(f"已清除默认房间（原房间：{default_room}）"))


@cmd_show.handle()
async def handle_show_default(
    bot: Bot,
    event: MessageEvent,
):
    """查看默认房间"""
    if not await check_group(event):
        await cmd_show.finish(format_error("权限不足"))

    # 获取会话 ID
    session_id = event.get_session_id()

    # 获取默认房间
    storage = get_storage()
    default_room = get_default_room(storage, session_id)

    if default_room is None:
        await cmd_show.finish(format_info("未设置默认房间\n使用 /dst 默认房间 <房间ID> 设置"))

    await cmd_show.finish(format_info(f"当前默认房间：{default_room}"))


def init(api_client: DSTApiClient):
    """
    初始化 handler

    Args:
        api_client: DST API 客户端
    """
    global _api_client
    _api_client = api_client
    logger.info("默认房间 handler 已初始化")
