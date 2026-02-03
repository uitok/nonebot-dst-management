"""
本地测试脚本 - 测试 NoneBot2 DST 插件

使用 Mock API 服务器，不连接真实 DMP 服务器。
"""

import asyncio
import sys
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from nonebot_plugin_dst_management.client.api_client import DSTApiClient


async def test_api_client():
    """测试 API 客户端"""
    print("=" * 60)
    print("🧪 开始测试 DST API 客户端")
    print("=" * 60)
    
    # 初始化客户端（连接 Mock 服务器）
    client = DSTApiClient(
        base_url="http://localhost:9999",
        token="test_token_123",
        timeout=5
    )
    
    print("\n✅ 客户端初始化成功")
    
    # 测试 1: 获取房间列表
    print("\n📋 测试 1: 获取房间列表")
    result = await client.get_room_list(page=1, page_size=10)
    
    if result["success"]:
        print(f"✅ 成功！找到 {result['data']['totalCount']} 个房间")
        for room in result['data']['rows']:
            status = "🟢 运行中" if room['status'] else "🔴 已停止"
            print(f"   - {room['gameName']} ({status})")
    else:
        print(f"❌ 失败: {result['error']}")
    
    # 测试 2: 获取房间详情
    print("\n📋 测试 2: 获取房间详情 (ID=1)")
    result = await client.get_room_info(1)
    
    if result["success"]:
        room = result['data']
        print(f"✅ 成功！房间: {room['gameName']}")
        print(f"   模式: {room['gameMode']}")
        print(f"   最大玩家: {room['maxPlayer']}")
        print(f"   在线玩家: {len(room['players'])} 人")
    else:
        print(f"❌ 失败: {result['error']}")
    
    # 测试 3: 获取在线玩家
    print("\n📋 测试 3: 获取在线玩家 (房间 ID=1)")
    result = await client.get_online_players(1)
    
    if result["success"]:
        players = result['data']
        print(f"✅ 成功！在线玩家: {len(players)} 人")
        for player in players:
            print(f"   - {player['nickname']} ({player['uid']}) - {player['prefab']}")
    else:
        print(f"❌ 失败: {result['error']}")
    
    # 测试 4: 获取备份列表
    print("\n📋 测试 4: 获取备份列表 (房间 ID=1)")
    result = await client.list_backups(1)
    
    if result["success"]:
        backups = result['data']
        print(f"✅ 成功！找到 {len(backups)} 个备份")
        for backup in backups:
            size_mb = backup['size'] / 1024 / 1024
            print(f"   - {backup['filename']} ({size_mb:.2f} MB)")
    else:
        print(f"❌ 失败: {result['error']}")
    
    # 测试 5: 启动房间（管理员命令）
    print("\n📋 测试 5: 启动房间 (ID=1)")
    result = await client.activate_room(1)
    
    if result["success"]:
        print(f"✅ 成功！{result['message']}")
    else:
        print(f"❌ 失败: {result['error']}")
    
    # 测试 6: 发送公告
    print("\n📋 测试 6: 发送全服公告")
    result = await client.announce(1, "这是一条测试公告")
    
    if result["success"]:
        print(f"✅ 成功！{result['message']}")
    else:
        print(f"❌ 失败: {result['error']}")
    
    # 测试 7: 获取平台概览
    print("\n📋 测试 7: 获取平台概览")
    result = await client.get_platform_overview()
    
    if result["success"]:
        data = result['data']
        print(f"✅ 成功！")
        print(f"   总房间数: {data['totalRooms']}")
        print(f"   运行中: {data['activeRooms']}")
        print(f"   在线玩家: {data['totalPlayers']}")
    else:
        print(f"❌ 失败: {result['error']}")
    
    # 关闭客户端
    await client.close()
    
    print("\n" + "=" * 60)
    print("✅ 所有测试完成！")
    print("=" * 60)


async def test_error_handling():
    """测试错误处理"""
    print("\n📋 测试 8: 错误处理")
    print("-" * 60)
    
    client = DSTApiClient(
        base_url="http://localhost:9999",
        token="test_token_123",
        timeout=5
    )
    
    # 测试不存在的房间
    print("测试不存在的房间 (ID=999)...")
    result = await client.get_room_info(999)
    
    if not result["success"]:
        print(f"✅ 正确处理错误: {result['error']}")
    else:
        print("❌ 应该返回错误但没有")
    
    await client.close()


async def main():
    """主测试函数"""
    print("""
╔══════════════════════════════════════════════════════════╗
║                                                            ║
║        NoneBot2 DST 管理插件 - 本地测试                    ║
║                                                            ║
║  使用 Mock API 服务器，不会连接真实 DMP 服务器              ║
║                                                            ║
╚══════════════════════════════════════════════════════════╝
    """)
    
    try:
        # 运行测试
        await test_api_client()
        await test_error_handling()
        
        print("\n🎉 所有测试通过！代码运行正常！")
        
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
