"""
消息格式化工具

提供统一的消息格式化功能。
"""

from typing import List, Dict, Any
from nonebot.adapters.onebot.v11 import Message, MessageSegment


def format_room_list(
    rooms: List[Dict[str, Any]],
    page: int,
    total_pages: int,
    total: int
) -> Message:
    """
    格式化房间列表
    
    Args:
        rooms: 房间列表
        page: 当前页码
        total_pages: 总页数
        total: 总数量
        
    Returns:
        Message: 格式化的消息
    """
    lines = [
        "🏕️ DST 房间列表",
        f"第 {page}/{total_pages} 页 | 共 {total} 个房间",
        ""
    ]
    
    if not rooms:
        lines.append("🈳 暂无房间")
    else:
        for idx, room in enumerate(rooms, 1):
            status = "🟢 运行中" if room.get("status") else "🔴 已停止"
            lines.append(f"{idx}. {room.get('gameName', '未知')}")
            lines.append(f"   状态：{status}")
            lines.append(f"   模式：{room.get('gameMode', '未知')}")
            lines.append(f"   ID：{room.get('id')}")
            lines.append("")
    
    lines.append("💡 使用 /dst info <房间ID> 查看详情")
    if page < total_pages:
        lines.append(f"💡 使用 /dst list {page + 1} 查看下一页")
    
    return Message("\n".join(lines))


def format_room_detail(
    room: Dict[str, Any],
    worlds: List[Dict[str, Any]],
    players: List[Dict[str, Any]]
) -> Message:
    """
    格式化房间详情
    
    Args:
        room: 房间信息
        worlds: 世界列表
        players: 在线玩家列表
        
    Returns:
        Message: 格式化的消息
    """
    lines = [
        f"🏕️ {room.get('gameName', '未知房间')}",
        "",
        "📋 基本信息",
        f"- 房间ID：{room.get('id')}",
        f"- 状态：{'🟢 运行中' if room.get('status') else '🔴 已停止'}",
        f"- 模式：{room.get('gameMode', '未知')}",
        f"- 玩家限制：{room.get('maxPlayer', 0)}人",
        f"- 密码：{'已设置' if room.get('password') else '无'}",
        f"- PVP：{'开启' if room.get('pvp') else '关闭'}",
        f"- 描述：{room.get('description', '无')}",
        ""
    ]
    
    # 世界信息
    if worlds:
        lines.append("🌍 世界列表")
        for world in worlds:
            status = "🟢 在线" if world.get("lastAliveTime") else "🔴 离线"
            lines.append(f"- {world.get('worldName', '未知')}：{status} (端口 {world.get('serverPort')})")
        lines.append("")
    
    # 在线玩家
    if players:
        lines.append(f"👥 在线玩家 ({len(players)}人)")
        for player in players[:10]:  # 最多显示10个
            nickname = player.get('nickname') or player.get('uid', '未知')
            prefab = player.get('prefab', '未知')
            lines.append(f"- {nickname} ({prefab})")
        if len(players) > 10:
            lines.append(f"... 还有 {len(players) - 10} 名玩家")
        lines.append("")
    
    # 已安装模组
    mod_data = room.get('modData', '')
    if mod_data:
        mod_count = mod_data.count('["workshop-')
        if mod_count > 0:
            lines.append(f"🧩 已安装模组：{mod_count}个")
    
    return Message("\n".join(lines))


def format_players(room_name: str, players: List[Dict[str, Any]]) -> Message:
    """
    格式化玩家列表
    
    Args:
        room_name: 房间名称
        players: 玩家列表
        
    Returns:
        Message: 格式化的消息
    """
    lines = [
        f"👥 在线玩家 ({room_name})",
        ""
    ]
    
    if not players:
        lines.append("🈳 当前没有玩家在线")
    else:
        for idx, player in enumerate(players, 1):
            nickname = player.get('nickname') or player.get('uid', '未知')
            uid = player.get('uid', '未知')
            prefab = player.get('prefab', '未知')
            lines.append(f"{idx}. {nickname}")
            lines.append(f"   - KU_ID: `{uid}`")
            lines.append(f"   - 角色: {prefab}")
            lines.append("")
        
        lines.append(f"共 {len(players)} 名玩家在线")
    
    return Message("\n".join(lines))


def format_backups(room_name: str, backups: List[Dict[str, Any]]) -> Message:
    """
    格式化备份列表
    
    Args:
        room_name: 房间名称
        backups: 备份列表
        
    Returns:
        Message: 格式化的消息
    """
    lines = [
        f"💾 备份列表 ({room_name})",
        ""
    ]
    
    if not backups:
        lines.append("🈳 暂无备份")
    else:
        for idx, backup in enumerate(backups[:20], 1):  # 最多显示20个
            filename = backup.get('filename', '未知')
            size = backup.get('size', 0)
            size_mb = f"{size / 1024 / 1024:.2f}MB" if size > 0 else "未知"
            
            # 尝试解析时间戳
            created_at = backup.get('created_at', '')
            if created_at:
                try:
                    from datetime import datetime
                    dt = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                    time_str = dt.strftime("%Y-%m-%d %H:%M:%S")
                except:
                    time_str = created_at
            else:
                time_str = "未知"
            
            lines.append(f"{idx}. {filename}")
            lines.append(f"   - 大小: {size_mb}")
            lines.append(f"   - 时间: {time_str}")
            lines.append("")
        
        if len(backups) > 20:
            lines.append(f"... 还有 {len(backups) - 20} 个备份")
        
        lines.append("💡 使用 /dst backup restore <房间ID> <序号> 恢复备份")
    
    return Message("\n".join(lines))


def format_error(message: str) -> Message:
    """
    格式化错误消息
    
    Args:
        message: 错误信息
        
    Returns:
        Message: 格式化的错误消息
    """
    return Message(f"❌ {message}")


def format_success(message: str) -> Message:
    """
    格式化成功消息
    
    Args:
        message: 成功信息
        
    Returns:
        Message: 格式化的成功消息
    """
    return Message(f"✅ {message}")


def format_info(message: str) -> Message:
    """
    格式化信息消息
    
    Args:
        message: 信息
        
    Returns:
        Message: 格式化的信息消息
    """
    return Message(f"ℹ️ {message}")


def format_warning(message: str) -> Message:
    """
    格式化警告消息
    
    Args:
        message: 警告信息
        
    Returns:
        Message: 格式化的警告消息
    """
    return Message(f"⚠️ {message}")


__all__ = [
    "format_room_list",
    "format_room_detail",
    "format_players",
    "format_backups",
    "format_error",
    "format_success",
    "format_info",
    "format_warning",
]
