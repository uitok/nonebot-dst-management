"""
DMP API 客户端

提供与 DMP (DST Management Platform) API v3 交互的异步客户端。
"""

import os
import json
import re
from typing import Any, Dict, List, Optional, Tuple
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

    async def get_room_mods(self, room_id: int) -> Dict[str, Any]:
        """
        获取房间模组列表（解析 modData）

        Args:
            room_id: 房间 ID

        Returns:
            Dict[str, Any]: 模组数据（enabled/disabled/duplicates/raw）
        """
        room_result = await self.get_room_info(room_id)
        if not room_result.get("success"):
            return room_result

        room_data = room_result.get("data") or {}
        mod_data = room_data.get("modData", "") or ""

        enabled, disabled = self._parse_mod_data(mod_data)
        counts: Dict[str, int] = {}
        for mod_id in re.findall(r"workshop-\d+", mod_data):
            counts[mod_id] = counts.get(mod_id, 0) + 1
        duplicates = [mod_id for mod_id, count in counts.items() if count > 1]

        return {
            "success": True,
            "data": {
                "enabled": enabled,
                "disabled": disabled,
                "duplicates": duplicates,
                "raw": mod_data,
            },
            "message": "success",
        }

    # ========== 模组管理 ==========

    async def search_mod(self, type: str, keyword: str) -> Dict[str, Any]:
        """
        搜索模组

        使用 DMP API v3 的模组搜索接口，支持文本、ID 或热门搜索。

        Args:
            type: 搜索类型（text/id/hot）
            keyword: 搜索关键词（text/id 模式必填，hot 可为空）

        Returns:
            {
                "success": True/False,
                "data": [...],  # 模组列表
                "error": "错误信息"
            }
        """
        search_type = (type or "").strip().lower()
        if search_type not in {"text", "id", "hot"}:
            return {"success": False, "error": "不支持的搜索类型", "code": 400}
        if search_type in {"text", "id"} and not (keyword or "").strip():
            return {"success": False, "error": "搜索关键词不能为空", "code": 400}

        params: Dict[str, Any] = {"type": search_type}
        if keyword:
            params["keyword"] = keyword

        return await self._request("GET", "/mod/search", params=params)

    async def download_mod(self, mod_id: str) -> Dict[str, Any]:
        """
        下载模组到服务器

        使用 DMP API v3 的模组下载接口，将指定 workshop 模组下载到服务器。

        Args:
            mod_id: 模组 ID（workshop-数字）

        Returns:
            {
                "success": True/False,
                "data": {"path": "..."},
                "error": "错误信息"
            }
        """
        mod_id = (mod_id or "").strip()
        if mod_id.isdigit():
            mod_id = f"workshop-{mod_id}"
        if not re.fullmatch(r"workshop-\d+", mod_id):
            return {"success": False, "error": "无效的模组ID", "code": 400}

        return await self._request("POST", "/mod/download", data={"modID": mod_id})

    async def get_mod_setting_struct(self, mod_id: str) -> Dict[str, Any]:
        """
        获取模组配置结构

        使用 DMP API v3 的模组配置结构接口，返回可用配置项定义。

        Args:
            mod_id: 模组 ID（workshop-数字）

        Returns:
            {
                "success": True/False,
                "data": {...},  # 配置结构
                "error": "错误信息"
            }
        """
        mod_id = (mod_id or "").strip()
        if mod_id.isdigit():
            mod_id = f"workshop-{mod_id}"
        if not re.fullmatch(r"workshop-\d+", mod_id):
            return {"success": False, "error": "无效的模组ID", "code": 400}

        return await self._request("GET", "/mod/setting/struct", params={"modID": mod_id})

    async def update_mod_setting(
        self,
        room_id: int,
        world_id: str,
        mod_id: str,
        config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        更新模组配置

        使用 DMP API v3 的模组配置更新接口，按房间/世界维度更新模组配置。

        Args:
            room_id: 房间 ID
            world_id: 世界 ID
            mod_id: 模组 ID（workshop-数字）
            config: 配置数据（Dict）

        Returns:
            {
                "success": True/False,
                "error": "错误信息"
            }
        """
        mod_id = (mod_id or "").strip()
        if mod_id.isdigit():
            mod_id = f"workshop-{mod_id}"
        if not re.fullmatch(r"workshop-\d+", mod_id):
            return {"success": False, "error": "无效的模组ID", "code": 400}
        if world_id is None or str(world_id).strip() == "":
            return {"success": False, "error": "世界ID不能为空", "code": 400}
        if not isinstance(config, dict):
            return {"success": False, "error": "配置数据必须是字典", "code": 400}

        data = {
            "roomID": room_id,
            "worldID": world_id,
            "modID": mod_id,
            "config": config,
        }
        return await self._request("POST", "/room/mod/setting/update", data=data)

    async def enable_mod(self, room_id: int, world_id: str, mod_id: str) -> Dict[str, Any]:
        """
        启用模组

        使用 DMP API v3 的模组启用接口，在指定房间/世界启用模组。

        Args:
            room_id: 房间 ID
            world_id: 世界 ID
            mod_id: 模组 ID（workshop-数字）

        Returns:
            {
                "success": True/False,
                "error": "错误信息"
            }
        """
        mod_id = (mod_id or "").strip()
        if mod_id.isdigit():
            mod_id = f"workshop-{mod_id}"
        if not re.fullmatch(r"workshop-\d+", mod_id):
            return {"success": False, "error": "无效的模组ID", "code": 400}
        if world_id is None or str(world_id).strip() == "":
            return {"success": False, "error": "世界ID不能为空", "code": 400}

        data = {"roomID": room_id, "worldID": world_id, "modID": mod_id}
        return await self._request("POST", "/room/mod/enable", data=data)

    # ========== 玩家管理 ==========

    async def get_online_players(self, room_id: int) -> Dict[str, Any]:
        """获取在线玩家列表"""
        return await self._request(
            "GET",
            "/room/player/online",
            params={"roomID": room_id}
        )

    async def get_room_stats(self, room_id: int) -> Dict[str, Any]:
        """
        获取房间玩家统计（若无独立接口则从在线列表推断）

        Args:
            room_id: 房间 ID

        Returns:
            Dict[str, Any]: 玩家统计信息
        """
        result = await self.get_online_players(room_id)
        if not result.get("success"):
            return result

        players = result.get("data") or []
        return {
            "success": True,
            "data": {
                "online_players": len(players),
                "players": players,
            },
            "message": "success",
        }

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

    @staticmethod
    def _parse_mod_data(mod_data: str) -> Tuple[List[str], List[str]]:
        """解析 modData 内容，返回 (enabled, disabled) 模组列表。"""
        enabled: List[str] = []
        disabled: List[str] = []

        if not mod_data:
            return enabled, disabled

        seen = set()

        def add_mod(mod_id: str, is_enabled: bool) -> None:
            if mod_id in seen:
                return
            seen.add(mod_id)
            if is_enabled:
                enabled.append(mod_id)
            else:
                disabled.append(mod_id)

        # 1) 尝试解析 JSON
        try:
            data = json.loads(mod_data)
            if isinstance(data, dict):
                for key, value in data.items():
                    if not isinstance(key, str) or not key.startswith("workshop-"):
                        continue
                    is_enabled = True
                    if isinstance(value, dict) and "enabled" in value:
                        is_enabled = bool(value.get("enabled"))
                    add_mod(key, is_enabled)
            elif isinstance(data, list):
                for item in data:
                    if not isinstance(item, dict):
                        continue
                    mod_id = item.get("id") or item.get("mod_id") or item.get("modId")
                    if not mod_id:
                        continue
                    mod_id = str(mod_id)
                    if not mod_id.startswith("workshop-"):
                        mod_id = f"workshop-{mod_id}"
                    is_enabled = bool(item.get("enabled", True))
                    add_mod(mod_id, is_enabled)
        except Exception:
            pass

        # 2) 尝试解析 Lua 风格 modoverrides
        lua_pattern = re.compile(
            r'\["(workshop-\d+)"\]\s*=\s*\{[^}]*?enabled\s*=\s*(true|false)',
            re.IGNORECASE | re.DOTALL,
        )
        for match in lua_pattern.finditer(mod_data):
            mod_id = match.group(1)
            is_enabled = match.group(2).lower() == "true"
            add_mod(mod_id, is_enabled)

        # 3) 兜底：仅提取 workshop- 前缀 ID
        if not enabled and not disabled:
            for mod_id in re.findall(r"workshop-\d+", mod_data):
                add_mod(mod_id, True)

        return enabled, disabled

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

    # ========== 存档管理 ==========

    async def upload_archive(self, room_id: int, archive_path: str) -> Dict[str, Any]:
        """上传房间存档"""
        return await self._upload_archive("/tools/archive/upload", room_id, archive_path)

    async def replace_archive(self, room_id: int, archive_path: str) -> Dict[str, Any]:
        """替换房间存档"""
        return await self._upload_archive("/tools/archive/replace", room_id, archive_path)

    async def download_archive(self, room_id: int) -> Dict[str, Any]:
        """下载房间存档"""
        try:
            async with httpx.AsyncClient(
                base_url=f"{self.base_url}/v3",
                headers={"X-DMP-TOKEN": self.token},
                timeout=self.timeout,
            ) as client:
                response = await client.get("/tools/archive/download", params={"roomID": room_id})

            content_type = response.headers.get("content-type", "")
            if "application/json" in content_type:
                result = response.json()
                if result.get("code") == 200:
                    return {
                        "success": True,
                        "data": result.get("data"),
                        "message": result.get("message", "success"),
                    }
                return {
                    "success": False,
                    "error": result.get("message", "Unknown error"),
                    "code": result.get("code"),
                }

            filename = response.headers.get("content-disposition", "")
            return {
                "success": True,
                "data": {
                    "filename": filename,
                    "content": response.content,
                },
            }
        except httpx.TimeoutException:
            logger.error("请求超时: /tools/archive/download")
            return {"success": False, "error": "请求超时", "code": 408}
        except httpx.RequestError as e:
            logger.error(f"请求错误: {e}")
            return {"success": False, "error": str(e), "code": 500}
        except Exception as e:
            logger.exception(f"未知错误: {e}")
            return {"success": False, "error": str(e), "code": 500}

    async def _upload_archive(self, path: str, room_id: int, archive_path: str) -> Dict[str, Any]:
        try:
            filename = os.path.basename(archive_path)
            async with httpx.AsyncClient(
                base_url=f"{self.base_url}/v3",
                headers={"X-DMP-TOKEN": self.token},
                timeout=self.timeout,
            ) as client:
                with open(archive_path, "rb") as file_handle:
                    files = {"file": (filename, file_handle, "application/zip")}
                    data = {"roomID": str(room_id)}
                    response = await client.post(path, data=data, files=files)

            result = response.json()
            if result.get("code") == 200:
                return {
                    "success": True,
                    "data": result.get("data"),
                    "message": result.get("message", "success"),
                }
            return {
                "success": False,
                "error": result.get("message", "Unknown error"),
                "code": result.get("code"),
            }

        except FileNotFoundError:
            return {"success": False, "error": "存档文件不存在", "code": 404}
        except httpx.TimeoutException:
            logger.error(f"请求超时: {path}")
            return {"success": False, "error": "请求超时", "code": 408}
        except httpx.RequestError as e:
            logger.error(f"请求错误: {e}")
            return {"success": False, "error": str(e), "code": 500}
        except Exception as e:
            logger.exception(f"未知错误: {e}")
            return {"success": False, "error": str(e), "code": 500}

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
