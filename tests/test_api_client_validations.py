import httpx
import pytest

from nonebot_plugin_dst_management.client.api_client import DSTApiClient


@pytest.mark.parametrize(
    "mod_data,expected_enabled,expected_disabled",
    [
        (
            '{"workshop-1":{"enabled":false},"workshop-2":{}}',
            ["workshop-2"],
            ["workshop-1"],
        ),
        (
            '[{"id":123,"enabled":false},{"mod_id":"workshop-456","enabled":true}]',
            ["workshop-456"],
            ["workshop-123"],
        ),
        (
            'return { ["workshop-789"] = { enabled = true }, ["workshop-10"] = { enabled = false } }',
            ["workshop-789"],
            ["workshop-10"],
        ),
        (
            'workshop-111 workshop-222',
            ["workshop-111", "workshop-222"],
            [],
        ),
    ],
)
def test_parse_mod_data_variants(mod_data, expected_enabled, expected_disabled):
    enabled, disabled = DSTApiClient._parse_mod_data(mod_data)
    assert enabled == expected_enabled
    assert disabled == expected_disabled


@pytest.mark.asyncio
async def test_search_mod_validation():
    client = DSTApiClient("http://mock", "token")

    assert await client.search_mod("bad", "x") == {"success": False, "error": "不支持的搜索类型", "code": 400}
    assert await client.search_mod("text", " ") == {"success": False, "error": "搜索关键词不能为空", "code": 400}

    captured = {}

    async def fake_request(method, path, **kwargs):
        captured["method"] = method
        captured["path"] = path
        captured["params"] = kwargs.get("params")
        return {"success": True, "data": []}

    client._request = fake_request
    result = await client.search_mod("text", "health")

    assert result["success"] is True
    assert captured["path"] == "/mod/search"
    assert captured["params"] == {"type": "text", "keyword": "health"}


@pytest.mark.asyncio
async def test_download_mod_validation():
    client = DSTApiClient("http://mock", "token")

    assert await client.download_mod("bad-id") == {"success": False, "error": "无效的模组ID", "code": 400}

    captured = {}

    async def fake_request(method, path, **kwargs):
        captured["data"] = kwargs.get("data")
        return {"success": True}

    client._request = fake_request
    result = await client.download_mod("123")

    assert result["success"] is True
    assert captured["data"] == {"modID": "workshop-123"}


@pytest.mark.asyncio
async def test_update_mod_setting_validation():
    client = DSTApiClient("http://mock", "token")

    assert await client.update_mod_setting(1, "", "workshop-1", {}) == {
        "success": False,
        "error": "世界ID不能为空",
        "code": 400,
    }
    assert await client.update_mod_setting(1, "1", "bad", {}) == {
        "success": False,
        "error": "无效的模组ID",
        "code": 400,
    }
    assert await client.update_mod_setting(1, "1", "workshop-1", []) == {
        "success": False,
        "error": "配置数据必须是字典",
        "code": 400,
    }


@pytest.mark.asyncio
async def test_enable_mod_validation():
    client = DSTApiClient("http://mock", "token")

    assert await client.enable_mod(1, None, "workshop-1") == {
        "success": False,
        "error": "世界ID不能为空",
        "code": 400,
    }


@pytest.mark.asyncio
async def test_get_room_mods_and_stats():
    client = DSTApiClient("http://mock", "token")

    async def fake_get_room_info(room_id):
        return {
            "success": True,
            "data": {
                "modData": '{"workshop-1":{"enabled":true},"workshop-2":{"enabled":false},"workshop-1":{"enabled":true}}'
            },
        }

    client.get_room_info = fake_get_room_info

    result = await client.get_room_mods(1)
    assert result["success"] is True
    assert result["data"]["enabled"] == ["workshop-1"]
    assert result["data"]["disabled"] == ["workshop-2"]
    assert result["data"]["duplicates"] == ["workshop-1"]

    async def fake_online_players(room_id):
        return {"success": True, "data": [{"uid": "1"}, {"uid": "2"}]}

    client.get_online_players = fake_online_players

    stats = await client.get_room_stats(1)
    assert stats["success"] is True
    assert stats["data"]["online_players"] == 2


@pytest.mark.asyncio
async def test_request_error_handling(monkeypatch):
    client = DSTApiClient("http://mock", "token")

    class DummyResponse:
        def __init__(self, payload):
            self._payload = payload

        def json(self):
            return self._payload

    async def return_success(*args, **kwargs):
        return DummyResponse({"code": 200, "data": {"ok": True}, "message": "ok"})

    client.client.request = return_success
    result = await client._request("GET", "/room/list")
    assert result["success"] is True
    assert result["data"] == {"ok": True}

    async def return_error(*args, **kwargs):
        return DummyResponse({"code": 500, "message": "bad"})

    client.client.request = return_error
    result = await client._request("GET", "/room/list")
    assert result["success"] is False
    assert result["error"] == "bad"

    async def raise_timeout(*args, **kwargs):
        raise httpx.TimeoutException("timeout")

    client.client.request = raise_timeout
    result = await client._request("GET", "/room/list")
    assert result["success"] is False
    assert result["code"] == 408

    async def raise_request_error(*args, **kwargs):
        raise httpx.RequestError("boom", request=httpx.Request("GET", "http://x"))

    client.client.request = raise_request_error
    result = await client._request("GET", "/room/list")
    assert result["success"] is False
    assert result["code"] == 500

    async def raise_generic(*args, **kwargs):
        raise RuntimeError("oops")

    client.client.request = raise_generic
    result = await client._request("GET", "/room/list")
    assert result["success"] is False
    assert result["code"] == 500

    request = httpx.Request("GET", "http://x")
    response = httpx.Response(500, request=request)

    async def raise_status_error(*args, **kwargs):
        raise httpx.HTTPStatusError("bad", request=request, response=response)

    client.client.request = raise_status_error
    result = await client._request("GET", "/room/list")
    assert result["success"] is False
    assert result["code"] == 500
