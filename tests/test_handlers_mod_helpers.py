from nonebot.adapters.onebot.v11 import Message

from nonebot_plugin_dst_management.handlers.mod import (
    _normalize_mod_id,
    _parse_mod_data,
    _format_mod_list,
    _format_mod_search_results,
)


def _message_text(msg: Message) -> str:
    if hasattr(msg, "extract_plain_text"):
        return msg.extract_plain_text()
    return str(msg)


def test_normalize_mod_id():
    assert _normalize_mod_id("123") == ("123", "workshop-123")
    assert _normalize_mod_id("workshop-456") == ("456", "workshop-456")


def test_parse_mod_data_json_dict():
    mod_data = '{"workshop-123": {"enabled": false}, "workshop-456": {"enabled": true}}'
    enabled, disabled = _parse_mod_data(mod_data)
    assert enabled == ["workshop-456"]
    assert disabled == ["workshop-123"]


def test_parse_mod_data_json_list():
    mod_data = '[{"id": "999", "enabled": false}, {"mod_id": "workshop-888"}]'
    enabled, disabled = _parse_mod_data(mod_data)
    assert enabled == ["workshop-888"]
    assert disabled == ["workshop-999"]


def test_parse_mod_data_lua_and_fallback():
    mod_data = 'return { ["workshop-111"] = { enabled = true }, ["workshop-222"] = { enabled = false } }'
    enabled, disabled = _parse_mod_data(mod_data)
    assert enabled == ["workshop-111"]
    assert disabled == ["workshop-222"]

    enabled, disabled = _parse_mod_data("workshop-333 workshop-444")
    assert enabled == ["workshop-333", "workshop-444"]
    assert disabled == []


def test_format_mod_search_results():
    empty_msg = _format_mod_search_results([], "test")
    assert "未找到" in _message_text(empty_msg)

    mods = [
        {"name": "Mod A", "id": "123", "author": "Alice", "subscriptions": 10},
        {"title": "Mod B", "modId": "456", "creator": "Bob", "subs": 20},
    ]
    msg = _format_mod_search_results(mods, "test")
    text = _message_text(msg)
    assert "模组搜索结果" in text
    assert "Mod A" in text
    assert "ID: 123" in text
    assert "作者: Alice" in text
    assert "订阅: 10" in text
    assert "Mod B" in text
    assert "ID: 456" in text
    assert "作者: Bob" in text


def test_format_mod_list():
    msg = _format_mod_list(1, [], [])
    assert "暂无模组" in _message_text(msg)

    msg = _format_mod_list(2, ["workshop-1"], ["workshop-2", "workshop-3"])
    text = _message_text(msg)
    assert "房间 2" in text
    assert "已启用 (1 个)" in text
    assert "workshop-1" in text
    assert "已禁用 (2 个)" in text
    assert "workshop-2" in text
    assert "workshop-3" in text
