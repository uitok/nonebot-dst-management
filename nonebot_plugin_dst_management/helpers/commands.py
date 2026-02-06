"""
命令解析辅助函数

提供对控制台命令与公告命令的参数解析。
"""

from typing import Optional, Tuple


def parse_room_id(room_id_str: str) -> Optional[int]:
    """
    解析房间 ID

    Args:
        room_id_str: 房间 ID 字符串

    Returns:
        Optional[int]: 房间 ID，解析失败返回 None
    """
    if not room_id_str:
        return None
    
    room_id_str = room_id_str.strip()
    
    if not room_id_str.isdigit():
        return None

    room_id = int(room_id_str)
    if room_id <= 0:
        return None

    return room_id


def parse_room_and_message(
    text: str,
    usage: str,
) -> Tuple[Optional[int], Optional[str], Optional[str]]:
    """
    解析房间 ID 与消息

    Args:
        text: 原始文本
        usage: 用法提示

    Returns:
        Tuple[room_id, message, error]
    """
    raw_text = (text or "").strip()
    if not raw_text:
        return None, None, f"用法：{usage}"

    parts = raw_text.split(maxsplit=1)
    if len(parts) < 2:
        return None, None, f"用法：{usage}"

    room_id = parse_room_id(parts[0])
    if room_id is None:
        return None, None, "请提供有效的房间ID"

    message = parts[1].strip()
    if not message:
        return None, None, "请输入消息内容"

    return room_id, message, None


def parse_console_command_args(
    text: str,
    usage: str,
) -> Tuple[Optional[int], Optional[int], Optional[str], Optional[str]]:
    """
    解析控制台命令参数

    Args:
        text: 原始文本
        usage: 用法提示

    Returns:
        Tuple[room_id, world_id, command, error]
    """
    raw_text = (text or "").strip()
    if not raw_text:
        return None, None, None, f"用法：{usage}"

    parts = raw_text.split()
    if len(parts) < 2:
        room_id = parse_room_id(parts[0]) if parts else None
        if room_id is None:
            return None, None, None, f"用法：{usage}"
        return room_id, None, None, f"用法：{usage}"

    room_id = parse_room_id(parts[0])
    if room_id is None:
        return None, None, None, "请提供有效的房间ID"

    world_id: Optional[int] = None
    command = ""

    if len(parts) == 2:
        if parts[1].isdigit():
            return None, None, None, "请提供控制台命令"
        command = parts[1]
    else:
        if parts[1].isdigit():
            world_id = int(parts[1])
            if world_id <= 0:
                return None, None, None, "请提供有效的世界ID"
            command = raw_text.split(None, 2)[2].strip()
        else:
            command = raw_text.split(None, 1)[1].strip()

    if not command:
        return None, None, None, "请提供控制台命令"

    return room_id, world_id, command, None


def escape_console_string(text: str) -> str:
    """
    转义控制台字符串参数

    Args:
        text: 原始字符串

    Returns:
        str: 转义后的字符串
    """
    return (
        text.replace("\\", "\\\\")
        .replace("\"", "\\\"")
        .replace("\r", "\\r")
        .replace("\n", "\\n")
        .replace("\t", "\\t")
    )
