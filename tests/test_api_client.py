"""
API 客户端单元测试

测试 DST API 客户端的各种方法
"""

import pytest
import asyncio
from nonebot_plugin_dst_management.client.api_client import DSTApiClient


@pytest.fixture
def api_client():
    """创建 API 客户端测试实例"""
    client = DSTApiClient(
        base_url="http://mock-api.local",
        token="test_token_123"
    )
    
    # Mock _request method
    async def mock_request(method, endpoint, **kwargs):
        if endpoint == "/room/list":
            return {"success": True, "data": {"rows": [{"id": 1, "gameName": "测试服务器1"}], "total": 1}}
        elif endpoint == "/room/player/online":
            return {"success": True, "data": [{"id": "KU_123", "name": "Player1"}]}
        elif endpoint.startswith("/room/"):
            return {"success": True, "data": {"id": 1, "gameName": "测试服务器1"}}
        elif endpoint == "/dashboard/startup":
            return {"success": True, "data": {"roomID": 1}}
        elif endpoint == "/dashboard/shutdown":
            return {"success": True, "data": {"roomID": 1}}
        elif endpoint == "/dashboard/restart":
            return {"success": True, "data": {"roomID": 1}}
        elif endpoint == "/tools/backup/create":
            return {"success": True, "data": {"filename": "backup.zip"}}
        elif endpoint == "/tools/backup/list":
            return {"success": True, "data": ["backup1.zip", "backup2.zip"]}
        elif endpoint == "/dashboard/console":
            return {"success": True, "data": "OK"}
        elif endpoint == "/mod/search":
            return {"success": True, "data": [{"id": 123, "name": "健康显示"}]}
            
        return {"success": False, "error": "Unknown endpoint"}

    client._request = mock_request
    return client


@pytest.mark.asyncio
async def test_get_room_list(api_client):
    """测试获取房间列表"""
    result = await api_client.get_room_list(page=1, page_size=10)
    
    assert result["success"] is True
    assert "data" in result
    assert "rows" in result["data"]
    assert isinstance(result["data"]["rows"], list)


@pytest.mark.asyncio
async def test_get_room_info(api_client):
    """测试获取房间详情"""
    result = await api_client.get_room_info(1)
    
    assert result["success"] is True
    assert result["data"]["id"] == 1
    assert result["data"]["gameName"] == "测试服务器1"


@pytest.mark.asyncio
async def test_activate_room(api_client):
    """测试启动房间"""
    result = await api_client.activate_room(1)
    
    assert result["success"] is True
    assert result["data"]["roomID"] == 1


@pytest.mark.asyncio
async def test_deactivate_room(api_client):
    """测试关闭房间"""
    result = await api_client.deactivate_room(1)
    
    assert result["success"] is True
    assert result["data"]["roomID"] == 1


@pytest.mark.asyncio
async def test_restart_room(api_client):
    """测试重启房间"""
    result = await api_client.restart_room(1)
    
    assert result["success"] is True
    assert result["data"]["roomID"] == 1


@pytest.mark.asyncio
async def test_get_online_players(api_client):
    """测试获取在线玩家"""
    result = await api_client.get_online_players(1)
    
    assert result["success"] is True
    assert isinstance(result["data"], list)


@pytest.mark.asyncio
async def test_create_backup(api_client):
    """测试创建备份"""
    result = await api_client.create_backup(1)
    
    assert result["success"] is True
    assert "filename" in result["data"]


@pytest.mark.asyncio
async def test_list_backups(api_client):
    """测试获取备份列表"""
    result = await api_client.list_backups(1)
    
    assert result["success"] is True
    assert isinstance(result["data"], list)


@pytest.mark.asyncio
async def test_execute_console_command(api_client):
    """测试执行控制台命令"""
    result = await api_client.execute_console_command(1, None, 'c_announce("test")')
    
    assert result["success"] is True


@pytest.mark.asyncio
async def test_announce(api_client):
    """测试发送公告"""
    result = await api_client.announce(1, "测试公告")
    
    assert result["success"] is True


@pytest.mark.asyncio
async def test_search_mod(api_client):
    """测试搜索模组"""
    result = await api_client.search_mod("text", "健康")
    
    assert result["success"] is True
    assert isinstance(result["data"], list)


# 运行测试
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
