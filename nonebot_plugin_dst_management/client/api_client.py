"""
DMP API 客户端

提供与 DMP (DST Management Platform) API v3 交互的异步客户端。
"""

from typing import Any, Dict, List, Optional
from loguru import logger
import httpx


class DSTApiClient:
    """
    DMP API 异步客户端

    通过 DMP API v3 管理 Don't Starve Together 服务器。

    Attributes:
        base_url: API 基础 URL
        token: JWT 认证令牌
        timeout: 请求超时时间（秒）
    """

    def __init__(
        self,
        base_url: str,
        token: str,
        timeout: int = 10,
    ):
        """
        初始化 API 客户端

        Args:
            base_url: DMP API 基础 URL（如 http://285k.mc5173.cn:35555）
            token: JWT 认证令牌
            timeout: 请求超时时间（秒），默认 10
        """
        self.base_url = base_url.rstrip("/")
        self.token = token
        self.timeout = timeout

        # 初始化 httpx 异步客户端
        self.client = httpx.AsyncClient(
            base_url=f"{self.base_url}/v3",
            headers={
                "X-DMP-TOKEN": token,
                "Content-Type": "application/json"
            },
            timeout=timeout
        )

    async def _request(
        self,
        method: str,
        path: str,
        data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        发送 API 请求

        Args:
            method: HTTP 方法（GET, POST, PUT, DELETE）
            path: API 路径
            data: 请求体数据
            params: URL 查询参数

        Returns:
            响应数据字典：{ success: bool, data: Any, message: str }
        """
        try:
            response = await self.client.request(
                method=method,
                url=path,
                json=data,
                params=params
            )
            result = response.json()

            # 检查响应状态码
            if result.get("code") == 200:
                return {
                    "success": True,
                    "data": result.get("data"),
                    "message": result.get("message", "success")
                }
            else:
                return {
                    "success": False,
                    "error": result.get("message", "Unknown error"),
                    "code": result.get("code")
                }

        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP 状态错误: {e.response.status_code}")
            return {
                "success": False,
                "error": f"HTTP 错误: {e.response.status_code}",
                "code": e.response.status_code
            }
        except httpx.TimeoutException:
            logger.error(f"请求超时: {path}")
            return {
                "success": False,
                "error": "请求超时",
                "code": 408
            }
        except httpx.RequestError as e:
            logger.error(f"请求错误: {e}")
            return {
                "success": False,
                "error": str(e),
                "code": 500
            }
        except Exception as e:
            logger.exception(f"未知错误: {e}")
            return {
                "success": False,
                "error": str(e),
                "code": 500
            }

    async def close(self):
        """关闭客户端连接"""
        await self.client.aclose()

    # ========== 房间管理 ==========

    async def get_room_list(
        self,
        page: int = 1,
        page_size: int = 10
    ) -> Dict[str, Any]:
        """获取房间列表"""
        return await self._request(
            "GET",
            "/room/list",
            params={"page": page, "pageSize": page_size}
        )

    async def get_room_info(self, room_id: int) -> Dict[str, Any]:
        """获取房间详情"""
        return await self._request("GET", f"/room/{room_id}")

    async def activate_room(self, room_id: int) -> Dict[str, Any]:
        """启动房间（所有世界）"""
        return await self._request("POST", "/dashboard/startup", data={
            "roomID": room_id,
            "extra": "all"
        })

    async def deactivate_room(self, room_id: int) -> Dict[str, Any]:
        """停止房间（所有世界）"""
        return await self._request("POST", "/dashboard/shutdown", data={
            "roomID": room_id,
            "extra": "all"
        })

    async def restart_room(self, room_id: int) -> Dict[str, Any]:
        """重启房间（所有世界）"""
        return await self._request("POST", "/dashboard/restart", data={
            "roomID": room_id
        })

    # ========== 世界管理 ==========

    async def get_world_list(self, room_id: int) -> Dict[str, Any]:
        """获取房间世界列表"""
        return await self._request(
            "GET",
            "/room/world/list",
            params={"roomID": room_id}
        )

    # ========== 玩家管理 ==========

    async def get_online_players(self, room_id: int) -> Dict[str, Any]:
        """获取在线玩家列表"""
        return await self._request(
            "GET",
            "/room/player/online",
            params={"roomID": room_id}
        )

    async def update_player_list(
        self,
        room_id: int,
        uids: List[str],
        list_type: str,
        action: str
    ) -> Dict[str, Any]:
        """更新玩家列表（白名单/黑名单/管理员）"""
        return await self._request("POST", "/room/player/update", data={
            "roomID": room_id,
            "uids": ",".join(uids),
            "listType": list_type,
            "type": action
        })

    # ========== 备份管理 ==========

    async def create_backup(self, room_id: int) -> Dict[str, Any]:
        """创建房间备份"""
        return await self._request(
            "POST",
            "/tools/backup/create",
            data={"roomID": room_id}
        )

    async def list_backups(self, room_id: int) -> Dict[str, Any]:
        """获取房间备份列表"""
        return await self._request(
            "GET",
            "/tools/backup/list",
            params={"roomID": room_id}
        )

    async def restore_backup(
        self,
        room_id: int,
        filename: str
    ) -> Dict[str, Any]:
        """恢复房间备份"""
        return await self._request("POST", "/tools/backup/restore", data={
            "roomID": room_id,
            "filename": filename
        })

    # ========== 控制台命令 ==========

    async def execute_console_command(
        self,
        room_id: int,
        world_id: Optional[int],
        command: str
    ) -> Dict[str, Any]:
        """执行控制台命令"""
        return await self._request("POST", "/dashboard/console", data={
            "roomID": room_id,
            "worldID": world_id,
            "extra": command
        })

    async def announce(
        self,
        room_id: int,
        message: str
    ) -> Dict[str, Any]:
        """发送全服公告"""
        return await self.execute_console_command(
            room_id,
            None,
            f'c_announce("{message}")'
        )

    # ========== 系统监控 ==========

    async def get_platform_overview(self) -> Dict[str, Any]:
        """获取平台概览"""
        return await self._request("GET", "/platform/overview")

    async def get_platform_metrics(
        self,
        minutes: int = 60
    ) -> Dict[str, Any]:
        """获取系统指标"""
        return await self._request(
            "GET",
            "/platform/metrics",
            params={"minutes": minutes}
        )
