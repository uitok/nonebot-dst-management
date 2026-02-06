"""
简单的 Mock DMP API 服务器 - 用于本地测试

使用 Python 内置 http.server，不需要额外依赖。
"""

from http.server import HTTPServer, BaseHTTPRequestHandler
import json
import urllib.parse
from typing import Dict, Any


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
        "modData": 'return {\\n  ["workshop-1234567"]={ enabled=true }\\n}'
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


class MockDMPHandler(BaseHTTPRequestHandler):
    """Mock DMP API 请求处理器"""
    
    def _send_json_response(self, code: int, message: str, data: Any):
        """发送 JSON 响应"""
        response = {
            "code": code,
            "message": message,
            "data": data
        }
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(json.dumps(response).encode())
    
    def _parse_path(self):
        """解析请求路径"""
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        query = urllib.parse.parse_qs(parsed.query)
        return path, query
    
    def do_GET(self):
        """处理 GET 请求"""
        path, query = self._parse_path()
        
        # /v3/room/list
        if path == "/v3/room/list":
            page = int(query.get("page", [1])[0])
            page_size = int(query.get("pageSize", [10])[0])
            total = len(MOCK_ROOMS)
            start = (page - 1) * page_size
            end = start + page_size
            rows = MOCK_ROOMS[start:end]
            
            return self._send_json_response(200, "success", {
                "rows": rows,
                "page": page,
                "pageSize": page_size,
                "totalCount": total
            })
        
        # /v3/room/{id}
        elif path.startswith("/v3/room/"):
            room_id = int(path.split("/")[-1])
            room = next((r for r in MOCK_ROOMS if r["id"] == room_id), None)
            if room:
                return self._send_json_response(200, "success", room)
            else:
                return self._send_json_response(201, "房间不存在", None)
        
        # /v3/room/world/list
        elif path == "/v3/room/world/list":
            return self._send_json_response(200, "success", {
                "rows": MOCK_WORLDS,
                "totalCount": len(MOCK_WORLDS)
            })
        
        # /v3/room/player/online
        elif path == "/v3/room/player/online":
            room_id = int(query.get("roomID", [1])[0])
            room = next((r for r in MOCK_ROOMS if r["id"] == room_id), None)
            if room:
                return self._send_json_response(200, "success", room.get("players", []))
            else:
                return self._send_json_response(201, "房间不存在", [])
        
        # /v3/tools/backup/list
        elif path == "/v3/tools/backup/list":
            return self._send_json_response(200, "success", MOCK_BACKUPS)
        
        # /v3/platform/overview
        elif path == "/v3/platform/overview":
            return self._send_json_response(200, "success", {
                "totalRooms": len(MOCK_ROOMS),
                "activeRooms": 1,
                "totalPlayers": 1
            })
        
        else:
            return self._send_json_response(404, "未找到接口", None)
    
    def do_POST(self):
        """处理 POST 请求"""
        path, _ = self._parse_path()
        
        # 读取请求体
        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length)
        data = json.loads(body.decode()) if body else {}
        
        # /v3/dashboard/startup
        if path == "/v3/dashboard/startup":
            room_id = data.get("roomID")
            return self._send_json_response(200, "服务器启动成功", {
                "roomID": room_id,
                "status": "starting"
            })
        
        # /v3/dashboard/shutdown
        elif path == "/v3/dashboard/shutdown":
            room_id = data.get("roomID")
            return self._send_json_response(200, "服务器已停止", {
                "roomID": room_id,
                "status": "stopped"
            })
        
        # /v3/dashboard/restart
        elif path == "/v3/dashboard/restart":
            room_id = data.get("roomID")
            return self._send_json_response(200, "服务器重启成功", {
                "roomID": room_id,
                "status": "restarting"
            })
        
        # /v3/tools/backup/create
        elif path == "/v3/tools/backup/create":
            return self._send_json_response(200, "备份创建成功", {
                "filename": "backup_2026-02-03_10-30-00.zip"
            })
        
        # /v3/tools/backup/restore
        elif path == "/v3/tools/backup/restore":
            filename = data.get("filename")
            return self._send_json_response(200, f"备份 {filename} 恢复成功", None)
        
        # /v3/dashboard/console
        elif path == "/v3/dashboard/console":
            command = data.get("extra", "")
            return self._send_json_response(200, f"命令执行成功: {command}", None)
        
        else:
            return self._send_json_response(404, "未找到接口", None)
    
    def log_message(self, format, *args):
        """自定义日志输出"""
        print(f"📡 {self.address_string} - {format % args}")


def main():
    """启动 Mock API 服务器"""
    server_address = ("localhost", 9999)
    httpd = HTTPServer(server_address, MockDMPHandler)
    
    print("""
╔══════════════════════════════════════════════════════════╗
║                                                            ║
║        Mock DMP API 服务器                                 ║
║                                                            ║
║  📍 地址: http://localhost:9999                            ║
║  📝 这是一个测试服务器，不会连接真实 DMP 服务器              ║
║                                                            ║
║  按 Ctrl+C 停止服务器                                       ║
║                                                            ║
╚══════════════════════════════════════════════════════════╝
    """)
    
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n\n👋 服务器已停止")
        httpd.server_close()


if __name__ == "__main__":
    main()
