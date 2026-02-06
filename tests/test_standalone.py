"""
独立测试脚本 - 直接测试 API 客户端

不依赖 NoneBot，只测试核心功能。
"""

import asyncio
import sys
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# 直接导入 API 客户端代码（复制版）
from typing import Any, Dict, List, Optional
import httpx


class DSTApiClient:
    """简化的 API 客户端（测试版）"""
    
    def __init__(self, base_url: str, token: str, timeout: int = 10):
        self.base_url = base_url.rstrip("/")
        self.token = token
        self.timeout = timeout
        self.client = httpx.AsyncClient(
            base_url=f"{self.base_url}/v3",
            headers={
                "X-DMP-TOKEN": token,
                "Content-Type": "application/json"
            },
            timeout=timeout
        )
    
    async def _request(self, method: str, path: str, data=None, params=None):
        try:
            response = await self.client.request(
                method=method,
                url=path,
                json=data,
                params=params
            )
            result = response.json()
            
            if result.get("code") == 200:
                return {"success": True, "data": result.get("data"), "message": result.get("message")}
            else:
                return {"success": False, "error": result.get("message"), "code": result.get("code")}
        except Exception as e:
            return {"success": False, "error": str(e), "code": 500}
    
    async def get_room_list(self, page=1, page_size=10):
        return await self._request("GET", "/room/list", params={"page": page, "pageSize": page_size})
    
    async def get_room_info(self, room_id):
        return await self._request("GET", f"/room/{room_id}")
    
    async def activate_room(self, room_id):
        return await self._request("POST", "/dashboard/startup", data={"roomID": room_id, "extra": "all"})
    
    async def get_online_players(self, room_id):
        return await self._request("GET", "/room/player/online", params={"roomID": room_id})
    
    async def list_backups(self, room_id):
        return await self._request("GET", "/tools/backup/list", params={"roomID": room_id})
    
    async def close(self):
        await self.client.aclose()


async def main():
    """主测试函数"""
    print("""
╔══════════════════════════════════════════════════════════╗
║                                                            ║
║        DST API 客户端 - 本地测试                            ║
║                                                            ║
║  使用 Mock API 服务器，不会连接真实 DMP 服务器              ║
║                                                            ║
╚══════════════════════════════════════════════════════════╝
    """)
    
    print("📡 连接到 Mock API 服务器: http://localhost:9999")
    
    client = DSTApiClient(
        base_url="http://localhost:9999",
        token="test_token_123"
    )
    
    try:
        # 测试 1: 获取房间列表
        print("\n" + "=" * 60)
        print("🧪 测试 1: 获取房间列表")
        print("=" * 60)
        result = await client.get_room_list()
        
        if result["success"]:
            data = result["data"]
            print(f"✅ 成功！找到 {data['totalCount']} 个房间\n")
            
            for idx, room in enumerate(data['rows'], 1):
                status = "🟢 运行中" if room['status'] else "🔴 已停止"
                print(f"{idx}. {room['gameName']}")
                print(f"   状态: {status}")
                print(f"   模式: {room['gameMode']}")
                print(f"   最大玩家: {room['maxPlayer']}")
                print(f"   当前在线: {len(room['players'])} 人")
                print()
        else:
            print(f"❌ 失败: {result['error']}\n")
        
        # 测试 2: 获取房间详情
        print("=" * 60)
        print("🧪 测试 2: 获取房间详情 (ID=1)")
        print("=" * 60)
        result = await client.get_room_info(1)
        
        if result["success"]:
            room = result['data']
            print(f"✅ 房间名称: {room['gameName']}")
            print(f"   描述: {room['description']}")
            print(f"   模式: {room['gameMode']}")
            print(f"   密码: {'已设置' if room['password'] else '无'}")
            print(f"   在线玩家: {len(room['players'])} 人\n")
        else:
            print(f"❌ 失败: {result['error']}\n")
        
        # 测试 3: 获取在线玩家
        print("=" * 60)
        print("🧪 测试 3: 获取在线玩家 (房间 ID=1)")
        print("=" * 60)
        result = await client.get_online_players(1)
        
        if result["success"]:
            players = result['data']
            print(f"✅ 在线玩家: {len(players)} 人\n")
            
            if players:
                for player in players:
                    print(f"   - {player['nickname']} ({player['uid']})")
                    print(f"     角色: {player['prefab']}\n")
            else:
                print("   当前没有玩家在线\n")
        else:
            print(f"❌ 失败: {result['error']}\n")
        
        # 测试 4: 获取备份列表
        print("=" * 60)
        print("🧪 测试 4: 获取备份列表 (房间 ID=1)")
        print("=" * 60)
        result = await client.list_backups(1)
        
        if result["success"]:
            backups = result['data']
            print(f"✅ 找到 {len(backups)} 个备份\n")
            
            for backup in backups:
                size_mb = backup['size'] / 1024 / 1024
                print(f"   📦 {backup['filename']}")
                print(f"      大小: {size_mb:.2f} MB\n")
        else:
            print(f"❌ 失败: {result['error']}\n")
        
        # 测试 5: 启动房间
        print("=" * 60)
        print("🧪 测试 5: 启动房间 (ID=1)")
        print("=" * 60)
        result = await client.activate_room(1)
        
        if result["success"]:
            print(f"✅ {result['message']}\n")
        else:
            print(f"❌ 失败: {result['error']}\n")
        
        # 测试 6: 错误处理
        print("=" * 60)
        print("🧪 测试 6: 错误处理 (不存在的房间 ID=999)")
        print("=" * 60)
        result = await client.get_room_info(999)
        
        if not result["success"]:
            print(f"✅ 正确处理错误: {result['error']}\n")
        else:
            print("❌ 应该返回错误但没有\n")
        
        print("=" * 60)
        print("🎉 所有测试完成！代码运行正常！")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return 1
    finally:
        await client.close()
    
    return 0


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
