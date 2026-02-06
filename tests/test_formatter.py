import pytest

from nonebot_plugin_dst_management.utils import formatter


def _text(message) -> str:
    if hasattr(message, "extract_plain_text"):
        return message.extract_plain_text()
    return str(message)


def test_format_room_list_empty():
    msg = formatter.format_room_list([], page=1, total_pages=1, total=0)
    text = _text(msg)
    assert "DST 房间列表" in text
    assert "暂无房间" in text


def test_format_room_list_with_data():
    rooms = [
        {"id": 1, "gameName": "Room A", "status": True, "gameMode": "survival"},
        {"id": 2, "gameName": "Room B", "status": False, "gameMode": "endless"},
    ]
    msg = formatter.format_room_list(rooms, page=1, total_pages=2, total=2)
    text = _text(msg)
    assert "Room A" in text
    assert "运行中" in text
    assert "Room B" in text
    assert "已停止" in text
    assert "使用 /dst list 2" in text


def test_format_room_detail_with_worlds_players_and_mods():
    room = {
        "id": 1,
        "gameName": "Test Room",
        "status": True,
        "gameMode": "survival",
        "maxPlayer": 6,
        "password": True,
        "pvp": False,
        "description": "desc",
        "modData": '["workshop-1"]["workshop-2"]',
    }
    worlds = [
        {"worldName": "Master", "lastAliveTime": "now", "serverPort": 10999},
        {"worldName": "Caves", "lastAliveTime": None, "serverPort": 11000},
    ]
    players = [
        {"nickname": "Alice", "uid": "KU_1", "prefab": "wilson"},
        {"nickname": "Bob", "uid": "KU_2", "prefab": "wendy"},
    ]
    msg = formatter.format_room_detail(room, worlds, players)
    text = _text(msg)
    assert "Test Room" in text
    assert "运行中" in text
    assert "世界列表" in text
    assert "Master" in text
    assert "Caves" in text
    assert "在线玩家" in text
    assert "Alice" in text
    assert "已安装模组：2个" in text


def test_format_players_and_wrappers():
    players = [
        {"nickname": "Alice", "uid": "KU_1", "prefab": "wilson"},
        {"nickname": None, "uid": "KU_2", "prefab": "wendy"},
    ]
    msg = formatter.format_players("Room X", players)
    text = _text(msg)
    assert "Room X" in text
    assert "KU_1" in text
    assert "KU_2" in text

    wrapper_text = _text(formatter.format_player_list("Room X", players))
    assert wrapper_text == text


def test_format_backups_and_wrappers():
    backups = [
        {"filename": "backup.zip", "size": 1024 * 1024, "created_at": "2024-01-01T12:00:00Z"},
    ]
    msg = formatter.format_backups("Room Y", backups)
    text = _text(msg)
    assert "backup.zip" in text
    assert "1.00MB" in text
    assert "2024-01-01" in text

    wrapper_text = _text(formatter.format_backup_list("Room Y", backups))
    assert wrapper_text == text


def test_format_helpers():
    assert "❌" in _text(formatter.format_error("oops"))
    assert "✅" in _text(formatter.format_success("ok"))
    assert "ℹ️" in _text(formatter.format_info("info"))
    assert "⚠️" in _text(formatter.format_warning("warn"))
    assert "⏳" in _text(formatter.format_loading("wait"))
