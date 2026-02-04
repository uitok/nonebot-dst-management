"""
DST 模组配置解析器

解析 modoverrides.lua 配置并调用 AI 输出优化报告。
"""

from __future__ import annotations

import io
import json
import re
import time
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple
from zipfile import ZipFile

import httpx
from loguru import logger

from .base import AIError, format_ai_error
from .client import AIClient
from ..client.api_client import DSTApiClient


@dataclass
class ParsedModConfig:
    """解析后的模组配置"""

    mods: List[Dict[str, Any]]
    warnings: List[str]
    mod_count: int
    option_count: int


class ModConfigParser:
    """
    模组配置解析器

    Attributes:
        api_client: DMP API 客户端
        ai_client: AI 客户端
    """

    _cache: Dict[str, Tuple[float, Dict[str, Any]]]

    def __init__(self, api_client: DSTApiClient, ai_client: AIClient) -> None:
        self.api_client = api_client
        self.ai_client = ai_client
        self._cache = {}

    async def parse_mod_config(self, room_id: int, world_id: str) -> Dict[str, Any]:
        """
        解析 modoverrides.lua 并生成报告

        Args:
            room_id: 房间 ID
            world_id: 世界 ID（如 Master/Caves）

        Returns:
            Dict[str, Any]: {
                "report": str,
                "optimized_config": str,
                "cached": bool,
            }
        """
        cache_key = f"{room_id}:{world_id.lower()}"
        cached = self._get_cached(cache_key, ttl=3600)
        if cached is not None:
            return {**cached, "cached": True}

        content = await self._fetch_modoverrides(room_id, world_id)
        parsed = self._parse_lua_config(content)
        prompt = self._build_prompt(room_id, world_id, content, parsed)
        system_prompt = self._system_prompt()

        try:
            response = await self.ai_client.chat(
                [{"role": "user", "content": prompt}],
                system_prompt=system_prompt,
            )
            report, optimized = self._build_ai_report(response, parsed)
        except AIError as exc:
            logger.warning("AI 模组配置解析失败，回退本地报告：{err}", err=exc)
            report, optimized = self._build_fallback_report(room_id, world_id, parsed, exc)
        except Exception as exc:
            logger.exception("模组配置解析发生未知错误：{err}", err=exc)
            report, optimized = self._build_fallback_report(room_id, world_id, parsed, exc)

        result = {"report": report, "optimized_config": optimized}
        self._set_cached(cache_key, result)
        return {**result, "cached": False}

    def get_cached_optimized(self, room_id: int, world_id: str) -> Optional[str]:
        """获取缓存中的优化配置内容。"""
        cache_key = f"{room_id}:{world_id.lower()}"
        cached = self._get_cached(cache_key, ttl=3600)
        if not cached:
            return None
        return cached.get("optimized_config")

    async def _fetch_modoverrides(self, room_id: int, world_id: str) -> str:
        """通过存档下载获取 modoverrides.lua 内容。"""
        if not hasattr(self.api_client, "download_archive"):
            raise RuntimeError("当前 API 客户端未实现存档下载")

        result = await self.api_client.download_archive(room_id)
        if not result.get("success"):
            error = result.get("error") or "未知错误"
            raise RuntimeError(f"存档下载失败：{error}")

        data = result.get("data") or {}
        content = data.get("content")
        url = data.get("url") or data.get("downloadUrl") or data.get("download_url")

        if content is None and url:
            content = await self._download_zip(url)

        if content is None:
            raise RuntimeError("存档内容为空")

        return self._extract_modoverrides_from_zip(content, world_id)

    async def _download_zip(self, url: str) -> bytes:
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.get(url)
            response.raise_for_status()
            return response.content

    def _extract_modoverrides_from_zip(self, content: bytes, world_id: str) -> str:
        world_name = self._normalize_world_id(world_id)
        with ZipFile(io.BytesIO(content)) as zf:
            candidates = [
                name
                for name in zf.namelist()
                if name.lower().endswith(f"{world_name.lower()}/modoverrides.lua")
            ]
            if not candidates:
                # fallback: search any modoverrides.lua
                candidates = [name for name in zf.namelist() if name.lower().endswith("modoverrides.lua")]

            if not candidates:
                raise RuntimeError("未找到 modoverrides.lua")

            target = candidates[0]
            raw = zf.read(target)
            return raw.decode("utf-8", errors="ignore")

    def _normalize_world_id(self, world_id: str) -> str:
        if world_id.isdigit():
            if world_id == "1":
                return "Master"
            if world_id == "2":
                return "Caves"
        return world_id

    def _parse_lua_config(self, content: str) -> ParsedModConfig:
        warnings: List[str] = []
        mods: List[Dict[str, Any]] = []

        for mod_id, block in self._extract_mod_blocks(content):
            enabled = self._extract_enabled(block)
            options = self._extract_options(block)
            mods.append(
                {
                    "mod_id": mod_id,
                    "enabled": enabled,
                    "configuration_options": options,
                }
            )

        if not mods:
            warnings.append("未解析到任何模组配置")

        option_count = sum(len(item.get("configuration_options") or {}) for item in mods)
        return ParsedModConfig(mods=mods, warnings=warnings, mod_count=len(mods), option_count=option_count)

    def _extract_mod_blocks(self, content: str) -> List[Tuple[str, str]]:
        result: List[Tuple[str, str]] = []
        pattern = re.compile(r'\["([^"]+)"\]\s*=\s*\{')
        for match in pattern.finditer(content):
            mod_id_raw = match.group(1)
            mod_id = mod_id_raw if mod_id_raw.startswith("workshop-") else f"workshop-{mod_id_raw}"
            start_index = match.end() - 1
            block, _ = self._extract_brace_block(content, start_index)
            if block is not None:
                result.append((mod_id, block))
        return result

    def _extract_brace_block(self, text: str, start_index: int) -> Tuple[Optional[str], int]:
        depth = 0
        in_string: Optional[str] = None
        escaped = False
        for idx in range(start_index, len(text)):
            ch = text[idx]
            if in_string:
                if escaped:
                    escaped = False
                    continue
                if ch == "\\":
                    escaped = True
                    continue
                if ch == in_string:
                    in_string = None
                continue
            if ch in ("'", '"'):
                in_string = ch
                continue
            if ch == "{":
                depth += 1
                continue
            if ch == "}":
                depth -= 1
                if depth == 0:
                    return text[start_index + 1:idx], idx + 1
        return None, start_index

    def _extract_enabled(self, block: str) -> bool:
        match = re.search(r"enabled\s*=\s*(true|false)", block, re.IGNORECASE)
        if not match:
            return True
        return match.group(1).lower() == "true"

    def _extract_options(self, block: str) -> Dict[str, Any]:
        match = re.search(r"configuration_options\s*=\s*\{", block)
        if not match:
            return {}
        start_index = match.end() - 1
        options_block, _ = self._extract_brace_block(block, start_index)
        if options_block is None:
            return {}
        return self._parse_option_entries(options_block)

    def _parse_option_entries(self, content: str) -> Dict[str, Any]:
        entries: List[str] = []
        current: List[str] = []
        depth = 0
        in_string: Optional[str] = None
        escaped = False

        for ch in content:
            if in_string:
                current.append(ch)
                if escaped:
                    escaped = False
                    continue
                if ch == "\\":
                    escaped = True
                    continue
                if ch == in_string:
                    in_string = None
                continue
            if ch in ("'", '"'):
                in_string = ch
                current.append(ch)
                continue
            if ch == "{":
                depth += 1
                current.append(ch)
                continue
            if ch == "}":
                depth -= 1
                current.append(ch)
                continue
            if ch == "," and depth == 0:
                entry = "".join(current).strip()
                if entry:
                    entries.append(entry)
                current = []
                continue
            current.append(ch)

        tail = "".join(current).strip()
        if tail:
            entries.append(tail)

        options: Dict[str, Any] = {}
        for entry in entries:
            if "=" not in entry:
                continue
            key_raw, value_raw = entry.split("=", 1)
            key = self._normalize_option_key(key_raw.strip())
            value = self._normalize_option_value(value_raw.strip())
            options[key] = value
        return options

    def _normalize_option_key(self, key: str) -> str:
        if key.startswith("["):
            key = key.strip("[]")
        return key.strip().strip('"').strip("'")

    def _normalize_option_value(self, raw: str) -> Any:
        raw = raw.strip()
        if raw.lower() == "true":
            return True
        if raw.lower() == "false":
            return False
        if raw.lower() == "nil":
            return None
        if raw.startswith("\"") and raw.endswith("\""):
            return raw[1:-1]
        if raw.startswith("'") and raw.endswith("'"):
            return raw[1:-1]
        try:
            if "." in raw:
                return float(raw)
            return int(raw)
        except ValueError:
            return raw

    def _build_prompt(
        self,
        room_id: int,
        world_id: str,
        content: str,
        parsed: ParsedModConfig,
    ) -> str:
        snippet = content
        if len(snippet) > 6000:
            snippet = snippet[:6000] + "\n-- content truncated --"

        payload = {
            "room_id": room_id,
            "world_id": world_id,
            "summary": {
                "mod_count": parsed.mod_count,
                "option_count": parsed.option_count,
                "warnings": parsed.warnings,
            },
            "mods": parsed.mods,
            "raw": snippet,
        }

        return (
            "你是 DST 模组配置专家，请分析以下 modoverrides.lua 配置并输出优化报告。\n\n"
            f"输入数据(JSON)：\n{json.dumps(payload, ensure_ascii=True, indent=2)}\n\n"
            "要求：\n"
            "1. 输出 JSON，包含 status, warnings, suggestions, optimized_config。\n"
            "2. status 为 valid/warn/error。\n"
            "3. warnings 为数组，每项包含 mod_id, issue, suggestion。\n"
            "4. optimized_config 为完整 Lua 配置文本。\n"
        )

    def _system_prompt(self) -> str:
        return "你是 DST 模组配置专家，擅长语法校验、冲突检测与优化建议。"

    def _build_ai_report(self, response: str, parsed: ParsedModConfig) -> Tuple[str, str]:
        data = self._extract_json(response)
        if not isinstance(data, dict):
            raise ValueError("AI 响应格式错误")

        status = data.get("status") or "warn"
        warnings = data.get("warnings") or []
        suggestions = data.get("suggestions") or []
        optimized = data.get("optimized_config")
        if not isinstance(optimized, str):
            optimized = self._build_optimized_config(parsed.mods)

        report = self._render_report(
            status=str(status),
            parsed=parsed,
            warnings=warnings,
            suggestions=suggestions,
            optimized=optimized,
            ai_error=None,
        )
        return report, optimized

    def _build_fallback_report(
        self,
        room_id: int,
        world_id: str,
        parsed: ParsedModConfig,
        error: Exception,
    ) -> Tuple[str, str]:
        suggestions = [
            "检查配置是否包含无效字段",
            "减少不必要的模组选项以提升稳定性",
            "保持配置文件格式统一",
        ]
        optimized = self._build_optimized_config(parsed.mods)
        report = self._render_report(
            status="warn" if parsed.warnings else "valid",
            parsed=parsed,
            warnings=[],
            suggestions=suggestions,
            optimized=optimized,
            ai_error=error,
        )
        return report, optimized

    def _render_report(
        self,
        status: str,
        parsed: ParsedModConfig,
        warnings: List[Dict[str, Any]],
        suggestions: List[Any],
        optimized: str,
        ai_error: Optional[Exception],
    ) -> str:
        status_label = {
            "valid": "✅ 有效",
            "warn": "⚠️ 警告",
            "error": "❌ 错误",
        }.get(status, "⚠️ 警告")

        lines = ["📄 模组配置解析报告", "", "🔍 解析结果："]
        lines.append(f"- 状态：{status_label}")
        lines.append(f"- 已配置模组：{parsed.mod_count} 个")
        lines.append(f"- 总配置项：{parsed.option_count} 个")

        if parsed.warnings:
            lines.append("")
            lines.append("⚠️ 解析警告：")
            for item in parsed.warnings:
                lines.append(f"- {item}")

        if warnings:
            lines.append("")
            lines.append("⚠️ 配置警告：")
            for idx, warn in enumerate(warnings, 1):
                mod_id = warn.get("mod_id") if isinstance(warn, dict) else "未知模组"
                issue = warn.get("issue") if isinstance(warn, dict) else str(warn)
                suggestion = warn.get("suggestion") if isinstance(warn, dict) else ""
                lines.append(f"{idx}. [{mod_id}] {issue}")
                if suggestion:
                    lines.append(f"   💡 {suggestion}")

        if suggestions:
            lines.append("")
            lines.append("💡 优化建议：")
            for idx, item in enumerate(suggestions, 1):
                lines.append(f"{idx}. {item}")

        lines.append("")
        lines.append("📋 优化后的配置：")
        lines.append("```lua")
        lines.append(optimized)
        lines.append("```")

        if ai_error is not None:
            lines.append("")
            if isinstance(ai_error, AIError):
                lines.append(f"⚠️ AI 分析失败：{format_ai_error(ai_error)}")
            else:
                lines.append(f"⚠️ AI 分析失败：{ai_error}")

        return "\n".join(lines)

    def _build_optimized_config(self, mods: List[Dict[str, Any]]) -> str:
        lines = ["return {"]
        for mod in mods:
            mod_id = mod.get("mod_id") or "unknown"
            enabled = bool(mod.get("enabled", True))
            options = mod.get("configuration_options") or {}

            lines.append(f"  [\"{mod_id}\"] = {{")
            lines.append(f"    enabled = {'true' if enabled else 'false'},")
            if options:
                lines.append("    configuration_options = {")
                for key, value in options.items():
                    lines.append(f"      {key} = {self._format_lua_value(value)},")
                lines.append("    },")
            lines.append("  },")
        lines.append("}")
        return "\n".join(lines)

    def _format_lua_value(self, value: Any) -> str:
        if value is True:
            return "true"
        if value is False:
            return "false"
        if value is None:
            return "nil"
        if isinstance(value, (int, float)):
            return str(value)
        if isinstance(value, str):
            escaped = value.replace("\\", "\\\\").replace("\"", "\\\"")
            return f"\"{escaped}\""
        return f"\"{str(value)}\""

    def _extract_json(self, text: str) -> Any:
        text = text.strip()
        if text.startswith("{"):
            return json.loads(text)
        start = text.find("```json")
        if start != -1:
            start = text.find("\n", start)
            end = text.find("```", start + 1)
            if start != -1 and end != -1:
                return json.loads(text[start:end].strip())
        brace_start = text.find("{")
        brace_end = text.rfind("}")
        if brace_start != -1 and brace_end != -1 and brace_end > brace_start:
            return json.loads(text[brace_start: brace_end + 1])
        raise ValueError("无法提取 JSON")

    def _get_cached(self, cache_key: str, ttl: int) -> Optional[Dict[str, Any]]:
        cached = self._cache.get(cache_key)
        if not cached:
            return None
        timestamp, value = cached
        if time.monotonic() - timestamp > ttl:
            self._cache.pop(cache_key, None)
            return None
        return value

    def _set_cached(self, cache_key: str, value: Dict[str, Any]) -> None:
        self._cache[cache_key] = (time.monotonic(), value)
