"""
DST 存档 AI 分析器

解析 ZIP 存档结构并调用 AI 生成分析报告。
"""

from __future__ import annotations

import io
import json
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple
from zipfile import ZipFile, BadZipFile

from loguru import logger

from .base import AIError, format_ai_error
from .client import AIClient

MAX_ARCHIVE_SIZE = 50 * 1024 * 1024  # 50MB 上限，防止 zip bomb


@dataclass
class ArchiveSnippet:
    """存档片段"""

    path: str
    content: str


class ArchiveAnalyzer:
    """
    存档分析器

    Attributes:
        ai_client: AI 客户端
    """

    def __init__(self, ai_client: AIClient) -> None:
        self.ai_client = ai_client

    async def analyze_archive(self, archive_data: bytes) -> str:
        """
        分析存档 ZIP 数据并返回报告

        Args:
            archive_data: ZIP 文件二进制数据

        Returns:
            str: Markdown 报告
        """
        # 先做体积检查，避免超大压缩包造成资源消耗或 zip bomb 风险。
        if len(archive_data) > MAX_ARCHIVE_SIZE:
            logger.warning("拦截超大存档文件，大小={size} bytes", size=len(archive_data))
            return "存档文件过大，已拒绝分析。请使用不超过 50MB 的较小文件后重试。"

        try:
            file_list, snippets = self._extract_files(archive_data)
        except Exception as exc:
            return f"存档解析失败：{exc}"

        prompt = self._build_prompt(file_list, snippets)
        system_prompt = self._system_prompt()

        try:
            response = await self.ai_client.chat(
                [{"role": "user", "content": prompt}],
                system_prompt=system_prompt,
            )
            if response and response.strip():
                return response.strip()
        except AIError as exc:
            logger.warning("AI 存档分析失败，回退本地报告：{err}", err=exc)
            return self._build_fallback_report(file_list, snippets, exc)
        except Exception as exc:
            logger.exception("存档分析发生未知错误：{err}", err=exc)
            return self._build_fallback_report(file_list, snippets, exc)

        return self._build_fallback_report(file_list, snippets, None)

    def _extract_files(self, archive_data: bytes) -> Tuple[List[str], List[ArchiveSnippet]]:
        try:
            zf = ZipFile(io.BytesIO(archive_data))
        except BadZipFile as exc:
            raise RuntimeError("无效的 ZIP 文件") from exc

        file_list = [name for name in zf.namelist() if not name.endswith("/")]
        snippets: List[ArchiveSnippet] = []

        for name in file_list:
            if not (name.endswith(".lua") or name.endswith(".ini")):
                continue
            try:
                raw = zf.read(name).decode("utf-8", errors="ignore")
            except Exception:
                continue
            if len(raw) > 4000:
                raw = raw[:4000] + "\n-- truncated --"
            snippets.append(ArchiveSnippet(path=name, content=raw))

        return file_list, snippets

    def _build_prompt(self, file_list: List[str], snippets: List[ArchiveSnippet]) -> str:
        payload = {
            "files": file_list,
            "snippets": [
                {
                    "path": item.path,
                    "content": item.content,
                }
                for item in snippets
            ],
        }

        return (
            "你是 DST 存档分析专家，请根据存档结构与配置文件给出分析报告。\n\n"
            f"输入数据(JSON)：\n{json.dumps(payload, ensure_ascii=True, indent=2)}\n\n"
            "要求：\n"
            "1. 识别存档中的世界、模组与核心配置。\n"
            "2. 指出潜在风险或缺失文件。\n"
            "3. 给出优化建议与注意事项。\n"
            "4. 输出 Markdown 报告。\n"
        )

    def _system_prompt(self) -> str:
        return "你是 DST 存档专家，擅长解析存档结构与配置文件。"

    def _build_fallback_report(
        self,
        file_list: List[str],
        snippets: List[ArchiveSnippet],
        error: Optional[Exception],
    ) -> str:
        lines = ["📦 存档分析报告（本地生成）", ""]
        lines.append(f"文件数量：{len(file_list)}")
        lua_files = [name for name in file_list if name.endswith(".lua")]
        ini_files = [name for name in file_list if name.endswith(".ini")]
        lines.append(f"Lua 文件：{len(lua_files)} 个")
        lines.append(f"INI 文件：{len(ini_files)} 个")

        if snippets:
            lines.append("")
            lines.append("📄 关键配置文件：")
            for item in snippets[:5]:
                lines.append(f"- {item.path}")

        if error is not None:
            lines.append("")
            if isinstance(error, AIError):
                lines.append(f"⚠️ AI 分析失败：{format_ai_error(error)}")
            else:
                lines.append(f"⚠️ AI 分析失败：{error}")

        return "\n".join(lines)
