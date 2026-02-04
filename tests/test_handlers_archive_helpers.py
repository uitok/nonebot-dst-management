from nonebot.adapters.onebot.v11 import Message

from nonebot_plugin_dst_management.handlers.archive import _extract_room_and_source, _format_archive_info
from nonebot_plugin_dst_management.services.archive_service import ArchiveInfo


def _message_text(msg: Message) -> str:
    if hasattr(msg, "extract_plain_text"):
        return msg.extract_plain_text()
    return str(msg)


def test_extract_room_and_source_valid():
    result = _extract_room_and_source("1 /tmp/archive.zip")
    assert result == (1, "/tmp/archive.zip")


def test_extract_room_and_source_invalid():
    assert _extract_room_and_source("") is None
    assert _extract_room_and_source("1") is None
    assert _extract_room_and_source("abc path") is None


def test_format_archive_info():
    info = ArchiveInfo(
        worlds=["Master", "Caves"],
        mod_count=3,
        game_mode="survival",
        cluster_name="Test Room",
        warnings=["Master 缺少 server.ini"],
    )
    msg = _format_archive_info(info)
    text = _message_text(msg)

    assert "存档解析结果" in text
    assert "房间名称：Test Room" in text
    assert "游戏模式：survival" in text
    assert "世界数量：2 (Master + Caves)" in text
    assert "模组数量：3" in text
    assert "Master 缺少 server.ini" in text
