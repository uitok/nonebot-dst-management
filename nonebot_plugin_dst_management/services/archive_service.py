"""
存档处理服务

提供 ZIP 文件操作、存档结构验证、Lua 配置解析、文件下载等功能。
"""

from __future__ import annotations

import os
import re
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from zipfile import ZipFile, BadZipFile

import httpx

from ..config import get_dst_config


@dataclass
class ArchiveInfo:
    """存档分析结果"""

    worlds: List[str]
    mod_count: int
    game_mode: Optional[str]
    cluster_name: Optional[str]
    warnings: List[str]


class ArchiveService:
    """存档处理服务"""

    def __init__(self, work_dir: Optional[str] = None):
        config = get_dst_config()
        self.ai_enabled = bool(config.dst_enable_ai)
        base_dir = Path(work_dir) if work_dir else Path(tempfile.gettempdir())
        self.work_dir = base_dir / "dst_archives"
        self.work_dir.mkdir(parents=True, exist_ok=True)

    async def prepare_archive(self, source: str) -> Dict[str, object]:
        """
        准备存档文件（支持 URL 或本地路径）

        Returns:
            {success: bool, path: str, cleanup: bool, error?: str}
        """
        source = source.strip()
        if not source:
            return {"success": False, "error": "文件路径或 URL 为空"}

        if self._is_url(source):
            try:
                filename = self._safe_filename_from_url(source)
                dest = self.work_dir / filename
                await self.download_file(source, dest)
                return {"success": True, "path": str(dest), "cleanup": True}
            except Exception as exc:
                return {"success": False, "error": f"下载失败：{exc}"}

        path = Path(source)
        if not path.exists():
            return {"success": False, "error": f"文件不存在：{source}"}
        if not path.is_file():
            return {"success": False, "error": f"不是有效文件：{source}"}

        return {"success": True, "path": str(path), "cleanup": False}

    async def download_file(self, url: str, dest: Path) -> None:
        """下载文件到指定路径"""
        dest.parent.mkdir(parents=True, exist_ok=True)
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.get(url)
            response.raise_for_status()
            with open(dest, "wb") as f:
                f.write(response.content)

    def validate_archive(self, archive_path: str) -> Dict[str, object]:
        """
        验证 ZIP 存档结构

        Returns:
            {success: bool, info?: ArchiveInfo, errors?: List[str]}
        """
        errors: List[str] = []
        warnings: List[str] = []

        if not archive_path.lower().endswith(".zip"):
            warnings.append("文件不是 .zip 扩展名，仍将尝试解析")

        try:
            with ZipFile(archive_path, "r") as zf:
                file_list = [name for name in zf.namelist() if not name.endswith("/")]

                if not file_list:
                    return {"success": False, "errors": ["ZIP 为空"]}

                has_cluster_ini, cluster_ini_name = self._find_file(file_list, "cluster.ini")
                has_cluster_token, _ = self._find_file(file_list, "cluster_token.txt")

                if not has_cluster_ini:
                    errors.append("缺少 cluster.ini")
                if not has_cluster_token:
                    errors.append("缺少 cluster_token.txt")

                worlds = self._detect_worlds(file_list)
                if not worlds:
                    errors.append("未检测到世界目录（Master/Caves）")

                for world in worlds:
                    required = f"{world}/server.ini"
                    if not self._has_path(file_list, required):
                        warnings.append(f"{world} 缺少 server.ini")

                mod_count = self._count_mods(zf, file_list)
                game_mode, cluster_name = self._parse_cluster_ini(zf, cluster_ini_name)

                if errors:
                    return {"success": False, "errors": errors, "warnings": warnings}

                info = ArchiveInfo(
                    worlds=worlds,
                    mod_count=mod_count,
                    game_mode=game_mode,
                    cluster_name=cluster_name,
                    warnings=warnings,
                )
                return {"success": True, "info": info}

        except BadZipFile:
            return {"success": False, "errors": ["无效的 ZIP 文件"]}
        except Exception as exc:
            return {"success": False, "errors": [f"解析失败：{exc}"]}

    def cleanup_file(self, path: str) -> None:
        """清理临时文件"""
        try:
            if path and os.path.isfile(path):
                os.remove(path)
        except Exception:
            pass

    def analyze_with_ai(self, info: ArchiveInfo) -> Optional[str]:
        """AI 辅助分析（可选）"""
        if not self.ai_enabled:
            return None
        # 当前未集成具体 AI 提供方，保留接口
        return "AI 功能已启用，但当前未配置分析器"

    def _is_url(self, value: str) -> bool:
        return value.startswith("http://") or value.startswith("https://")

    def _safe_filename_from_url(self, url: str) -> str:
        base = url.split("?")[0].split("#")[0].rstrip("/")
        name = os.path.basename(base) or "archive.zip"
        if not name.lower().endswith(".zip"):
            name = f"{name}.zip"
        return name

    def _find_file(self, file_list: List[str], filename: str) -> Tuple[bool, Optional[str]]:
        for name in file_list:
            if name.endswith(f"/{filename}") or name == filename:
                return True, name
        return False, None

    def _detect_worlds(self, file_list: List[str]) -> List[str]:
        worlds: List[str] = []
        if self._has_dir(file_list, "Master"):
            worlds.append("Master")
        if self._has_dir(file_list, "Caves"):
            worlds.append("Caves")
        return worlds

    def _has_dir(self, file_list: List[str], dir_name: str) -> bool:
        prefix = f"{dir_name}/"
        return any(name.startswith(prefix) for name in file_list)

    def _has_path(self, file_list: List[str], path: str) -> bool:
        if path in file_list:
            return True
        return any(name.endswith(f"/{path}") for name in file_list)

    def _count_mods(self, zf: ZipFile, file_list: List[str]) -> int:
        mod_ids = set()
        for lua_name in file_list:
            if not lua_name.endswith("modoverrides.lua"):
                continue
            try:
                content = zf.read(lua_name).decode("utf-8", errors="ignore")
            except Exception:
                continue
            mod_ids.update(self._parse_lua_mods(content))
        return len(mod_ids)

    def _parse_lua_mods(self, content: str) -> List[str]:
        mods = set(re.findall(r"workshop-\d+", content))
        numeric = re.findall(r"\b(\d{5,})\b", content)
        for item in numeric:
            mods.add(f"workshop-{item}")
        return list(mods)

    def _parse_cluster_ini(self, zf: ZipFile, ini_name: Optional[str]) -> Tuple[Optional[str], Optional[str]]:
        if not ini_name:
            return None, None
        try:
            raw = zf.read(ini_name).decode("utf-8", errors="ignore")
        except Exception:
            return None, None

        data = self._parse_ini(raw)
        game_mode = data.get("game_mode")
        cluster_name = data.get("cluster_name")
        return game_mode, cluster_name

    def _parse_ini(self, content: str) -> Dict[str, str]:
        result: Dict[str, str] = {}
        for line in content.splitlines():
            line = line.strip()
            if not line or line.startswith("#") or line.startswith(";"):
                continue
            if "=" not in line:
                continue
            key, value = line.split("=", 1)
            result[key.strip()] = value.strip()
        return result
