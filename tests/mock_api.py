"""
DMP API Mock 服务器 - 用于本地测试

模拟 DMP API 的响应，不需要真实的服务器。
"""

from fastapi import FastAPI
from fastapi.responses import JSONResponse
from typing import Dict, Any, List
import uvicorn

app = FastAPI(title="Mock DMP API")


# 模拟数据
MOCK_ROOMS = [
    {
        "id": 1,
        "status": True,
        "gameName": "测试服务器1",
        "description": "这是一个测试服务器",
        "gameMode": "endless",
        "maxPlayer": 6,
        "password": "123456",
        "players": [
            {"uid": "KU_TEST1", "nickname": "测试玩家1", "prefab": "wilson"}
        ],
        "modData": 'return {\n  ["workshop-1234567"]={ enabled=true }\n}'
    },
    {
        "id": 2,
        "status": False,
        "gameName": "测试服务器2",
        "description": "已停止的测试服务器",
        "gameMode": "survival",
        "maxPlayer": 4,
        "password": "",
        "players": [],
        "modData": ""
    }
]

MOCK_WORLDS = [
    {
        "id": 1,
        "roomID": 1,
        "worldName": "Master",
        "serverPort": 11000,
        "isMaster": True,
        "lastAliveTime": "2026-02-03T10:00:00Z"
    },
    {
        "id": 2,
        "roomID": 1,
        "worldName": "Caves",
        "serverPort": 11001,
        "isMaster": False,
        "lastAliveTime": "2026-02-03T10:00:00Z"
    }
]

MOCK_BACKUPS = [
    {
        "filename": "backup_2026-02-03_10-00-00.zip",
        "size": 1024000,
        "created_at": "2026-02-03T10:00:00Z"
    },
    {
        "filename": "backup_2026-02-02_23-00-00.zip",
        "size": 1024000,
        "created_at": "2026-02-02T23:00:00Z"
    }
]


@app.get("/v3/room/list")
async def get_room_list(page: int = 1, pageSize: int = 10):
    """获取房间列表"""
    total = len(MOCK_ROOMS)
    start = (page - 1) * pageSize
    end = start + pageSize
    rows = MOCK_ROOMS[start:end]

    return JSONResponse({
        "code": 200,
        "message": "success",
        "data": {
            "rows": rows,
            "page": page,
            "pageSize": pageSize,
            "totalCount": total
        }
    })


@app.get("/v3/room/{room_id}")
async def get_room_info(room_id: int):
    """获取房间详情"""
    room = next((r for r in MOCK_ROOMS if r["id"] == room_id), None)
    if not room:
        return JSONResponse({
            "code": 201,
            "message": "房间不存在",
            "data": None
        })

    return JSONResponse({
        "code": 200,
        "message": "success",
        "data": room
    })


@app.post("/v3/dashboard/startup")
async def activate_room(request: dict):
    """启动房间"""
    room_id = request.get("roomID")
    return JSONResponse({
        "code": 200,
        "message": "服务器启动成功",
        "data": {"roomID": room_id, "status": "starting"}
    })


@app.post("/v3/dashboard/shutdown")
async def deactivate_room(request: dict):
    """停止房间"""
    room_id = request.get("roomID")
    return JSONResponse({
        "code": 200,
        "message": "服务器已停止",
        "data": {"roomID": room_id, "status": "stopped"}
    })


@app.post("/v3/dashboard/restart")
async def restart_room(request: dict):
    """重启房间"""
    room_id = request.get("roomID")
    return JSONResponse({
        "code": 200,
        "message": "服务器重启成功",
        "data": {"roomID": room_id, "status": "restarting"}
    })


@app.get("/v3/room/world/list")
async def get_world_list(roomID: int):
    """获取世界列表"""
    return JSONResponse({
        "code": 200,
        "message": "success",
        "data": {
            "rows": MOCK_WORLDS,
            "totalCount": len(MOCK_WORLDS)
        }
    })


@app.get("/v3/room/player/online")
async def get_online_players(roomID: int):
    """获取在线玩家"""
    room = next((r for r in MOCK_ROOMS if r["id"] == roomID), None)
    if not room:
        return JSONResponse({
            "code": 201,
            "message": "房间不存在",
            "data": []
        })

    return JSONResponse({
        "code": 200,
        "message": "success",
        "data": room.get("players", [])
    })


@app.post("/v3/room/player/update")
async def update_player_list(request: dict):
    """更新玩家列表"""
    return JSONResponse({
        "code": 200,
        "message": "玩家列表更新成功",
        "data": None
    })


@app.post("/v3/tools/backup/create")
async def create_backup(request: dict):
    """创建备份"""
    return JSONResponse({
        "code": 200,
        "message": "备份创建成功",
        "data": {"filename": "backup_2026-02-03_10-30-00.zip"}
    })


@app.get("/v3/tools/backup/list")
async def list_backups(roomID: int):
    """获取备份列表"""
    return JSONResponse({
        "code": 200,
        "message": "success",
        "data": MOCK_BACKUPS
    })


@app.post("/v3/tools/backup/restore")
async def restore_backup(request: dict):
    """恢复备份"""
    filename = request.get("filename")
    return JSONResponse({
        "code": 200,
        "message": f"备份 {filename} 恢复成功",
        "data": None
    })


@app.post("/v3/dashboard/console")
async def execute_console(request: dict):
    """执行控制台命令"""
    command = request.get("extra", "")
    return JSONResponse({
        "code": 200,
        "message": f"命令执行成功: {command}",
        "data": None
    })


@app.get("/v3/platform/overview")
async def get_platform_overview():
    """获取平台概览"""
    return JSONResponse({
        "code": 200,
        "message": "success",
        "data": {
            "totalRooms": len(MOCK_ROOMS),
            "activeRooms": 1,
            "totalPlayers": 1
        }
    })


if __name__ == "__main__":
    print("🚀 启动 Mock DMP API 服务器...")
    print("📍 地址: http://localhost:9999")
    print("📝 这是一个测试服务器，不会连接真实 DST 服务器")
    uvicorn.run(app, host="localhost", port=9999, log_level="info")
