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

    _shared_cache: Dict[str, Tuple[float, Dict[str, Any]]] = {}
    _cache: Dict[str, Tuple[float, Dict[str, Any]]]

    def __init__(self, api_client: DSTApiClient, ai_client: AIClient) -> None:
        self.api_client = api_client
        self.ai_client = ai_client
        self._cache = ModConfigParser._shared_cache

    async def parse_mod_config(self, room_id: int, world_id: str) -> Dict[str, Any]:
        """
        解析 modoverrides.lua 并生成报告

        Args:
            room_id: 房间 ID
            world_id: 世界 ID（如 Master/Caves）

        Returns:
            Dict[str, Any]: {
                "status": str,
                "summary": dict,
                "issues": list,
                "optimized_config": str,
                "report": str,
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
            status, summary, issues, report, optimized = self._build_ai_report(response, parsed)
        except AIError as exc:
            logger.warning("AI 模组配置解析失败，回退本地报告：{err}", err=exc)
            status, summary, issues, report, optimized = self._build_fallback_report(
                room_id, world_id, parsed, exc
            )
        except Exception as exc:
            logger.exception("模组配置解析发生未知错误：{err}", err=exc)
            status, summary, issues, report, optimized = self._build_fallback_report(
                room_id, world_id, parsed, exc
            )

        result = {
            "status": status,
            "summary": summary,
            "issues": issues,
            "optimized_config": optimized,
            "report": report,
        }
        self._set_cached(cache_key, result)
        return {**result, "cached": False}

    def get_cached_optimized(self, room_id: int, world_id: str) -> Optional[str]:
        """获取缓存中的优化配置内容。"""
        cache_key = f"{room_id}:{world_id.lower()}"
        cached = self._get_cached(cache_key, ttl=3600)
        if not cached:
            return None
        return cached.get("optimized_config")

    def get_cached_result(self, room_id: int, world_id: str) -> Optional[Dict[str, Any]]:
        """获取缓存中的完整分析结果。"""
        cache_key = f"{room_id}:{world_id.lower()}"
        cached = self._get_cached(cache_key, ttl=3600)
        if not cached:
            return None
        return dict(cached)

    async def fetch_modoverrides(self, room_id: int, world_id: str) -> str:
        """获取指定房间/世界的 modoverrides.lua 原始内容。"""
        return await self._fetch_modoverrides(room_id, world_id)

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

        # 使用 lupa 进行 Lua 编译与执行，避免正则解析带来的嵌套/转义/注释问题。
        try:
            runtime, lua_error, lupa_bytecode = self._init_lua_runtime()
        except Exception as exc:
            warnings.append(f"Lua 解析器初始化失败：{exc}，已回退正则解析")
            return self._parse_lua_config_fallback(content, warnings)

        try:
            # 先编译进行语法校验，避免执行阶段才暴露错误。
            lupa_bytecode.compile(content)
        except Exception as exc:
            warnings.append(f"Lua 语法错误：{exc}")
            return ParsedModConfig(mods=[], warnings=warnings, mod_count=0, option_count=0)

        try:
            result = runtime.execute(content)
        except lua_error as exc:
            warnings.append(f"Lua 执行失败：{exc}")
            return ParsedModConfig(mods=[], warnings=warnings, mod_count=0, option_count=0)
        except Exception as exc:
            warnings.append(f"Lua 解析失败：{exc}")
            return ParsedModConfig(mods=[], warnings=warnings, mod_count=0, option_count=0)

        if not self._is_lua_table(result):
            warnings.append("Lua 返回值不是表结构，无法解析")
            return ParsedModConfig(mods=[], warnings=warnings, mod_count=0, option_count=0)

        config = self._lua_table_to_python(result)
        if not isinstance(config, dict):
            warnings.append("Lua 配置不是键值表结构，无法解析")
            return ParsedModConfig(mods=[], warnings=warnings, mod_count=0, option_count=0)

        mods: List[Dict[str, Any]] = []
        for raw_mod_id, raw_block in config.items():
            mod_id = self._normalize_mod_id(raw_mod_id)
            if not isinstance(raw_block, dict):
                warnings.append(f"模组 {mod_id} 配置不是表结构，已跳过")
                continue
            enabled = bool(raw_block.get("enabled", True))
            options_raw = raw_block.get("configuration_options")
            if options_raw is None:
                options: Dict[str, Any] = {}
            elif isinstance(options_raw, dict):
                options = options_raw
            else:
                warnings.append(f"模组 {mod_id} 的 configuration_options 非表结构，已忽略")
                options = {}
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

    def _init_lua_runtime(self) -> Tuple[Any, Any, Any]:
        """初始化 lupa LuaRuntime，并返回运行时/错误类型/编译器。"""
        from lupa import LuaError, LuaRuntime, bytecode as lupa_bytecode

        runtime = LuaRuntime(unpack_returned_tuples=True)
        return runtime, LuaError, lupa_bytecode

    def _parse_lua_config_fallback(self, content: str, warnings: Optional[List[str]] = None) -> ParsedModConfig:
        """lupa 不可用时的正则降级解析。"""
        warnings = warnings or []
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

    def _is_lua_table(self, value: Any) -> bool:
        module_name = getattr(value.__class__, "__module__", "")
        return "lupa" in module_name and hasattr(value, "items")

    def _lua_table_to_python(self, value: Any) -> Any:
        if not self._is_lua_table(value):
            return value

        items = list(value.items())
        if not items:
            return {}

        keys = [key for key, _ in items]
        if all(isinstance(key, int) and key >= 1 for key in keys):
            max_key = max(keys)
            if len(keys) == max_key:
                return [self._lua_table_to_python(value[idx]) for idx in range(1, max_key + 1)]

        converted: Dict[str, Any] = {}
        for key, item in items:
            key_str = str(key)
            converted[key_str] = self._lua_table_to_python(item)
        return converted

    def _normalize_mod_id(self, raw_mod_id: Any) -> str:
        mod_id = str(raw_mod_id).strip()
        if not mod_id.startswith("workshop-"):
            mod_id = f"workshop-{mod_id}"
        return mod_id

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
        if raw.startswith("{") and raw.endswith("}"):
            return self._parse_table_literal(raw)
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

    def _parse_table_literal(self, raw: str) -> Any:
        content = raw.strip()[1:-1].strip()
        if not content:
            return {}

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

        has_pairs = any("=" in entry for entry in entries)
        if has_pairs:
            result: Dict[str, Any] = {}
            for entry in entries:
                if "=" not in entry:
                    continue
                key_raw, value_raw = entry.split("=", 1)
                key = self._normalize_option_key(key_raw.strip())
                value = self._normalize_option_value(value_raw.strip())
                result[key] = value
            return result

        return [self._normalize_option_value(entry.strip()) for entry in entries]

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
            "你是 DST 模组配置诊断专家，请分析以下 modoverrides.lua 配置并给出详细诊断与建议。\n\n"
            f"输入数据(JSON)：\n{json.dumps(payload, ensure_ascii=True, indent=2)}\n\n"
            "要求：\n"
            "1. 只输出 JSON（不要包含额外说明或 Markdown）。\n"
            "2. status 为 valid/warn/error。\n"
            "3. 输出格式：\n"
            "{\n"
            "  \"status\": \"valid\" | \"warn\" | \"error\",\n"
            "  \"summary\": {\n"
            "    \"mod_count\": int,\n"
            "    \"issue_count\": int,\n"
            "    \"critical_count\": int,\n"
            "    \"suggestion_count\": int\n"
            "  },\n"
            "  \"issues\": [\n"
            "    {\n"
            "      \"level\": \"critical\" | \"warning\" | \"info\",\n"
            "      \"mod_id\": \"workshop-xxxx\",\n"
            "      \"mod_name\": \"模组名称\",\n"
            "      \"issue_type\": \"missing\" | \"conflict\" | \"invalid\" | \"performance\" | \"other\",\n"
            "      \"title\": \"问题标题\",\n"
            "      \"description\": \"问题描述\",\n"
            "      \"impact\": \"影响\",\n"
            "      \"current_value\": \"当前值\",\n"
            "      \"suggested_value\": \"建议值\",\n"
            "      \"reason\": \"修改理由\",\n"
            "      \"config_path\": \"配置路径\"\n"
            "    }\n"
            "  ],\n"
            "  \"optimized_config\": \"完整 Lua 配置文本\"\n"
            "}\n"
        )

    def _system_prompt(self) -> str:
        return "你是 DST 模组配置专家，擅长语法校验、冲突检测与优化建议。"

    def _build_ai_report(
        self,
        response: str,
        parsed: ParsedModConfig,
    ) -> Tuple[str, Dict[str, Any], List[Dict[str, Any]], str, str]:
        data = self._extract_json(response)
        if not isinstance(data, dict):
            raise ValueError("AI 响应格式错误")

        status = self._normalize_status(data.get("status"))
        optimized = data.get("optimized_config")
        if not isinstance(optimized, str):
            optimized = self._build_optimized_config(parsed.mods)

        if "issues" in data or "summary" in data:
            issues = self._normalize_issues(data.get("issues"))
            summary = self._build_summary(parsed, issues, data.get("summary"))
        else:
            warnings = data.get("warnings") or []
            suggestions = data.get("suggestions") or []
            issues = self._convert_legacy_issues(warnings, suggestions)
            summary = self._build_summary(parsed, issues, None)

        report = self._render_report(
            status=status,
            parsed=parsed,
            summary=summary,
            issues=issues,
            optimized=optimized,
            ai_error=None,
        )
        return status, summary, issues, report, optimized

    def _build_fallback_report(
        self,
        room_id: int,
        world_id: str,
        parsed: ParsedModConfig,
        error: Exception,
    ) -> Tuple[str, Dict[str, Any], List[Dict[str, Any]], str, str]:
        suggestions = [
            "检查配置是否包含无效字段",
            "减少不必要的模组选项以提升稳定性",
            "保持配置文件格式统一",
        ]
        issues = self._convert_legacy_issues([], suggestions)
        optimized = self._build_optimized_config(parsed.mods)
        status = "warn" if parsed.warnings else "valid"
        summary = self._build_summary(parsed, issues, None)
        report = self._render_report(
            status=status,
            parsed=parsed,
            summary=summary,
            issues=issues,
            optimized=optimized,
            ai_error=error,
        )
        return status, summary, issues, report, optimized

    def _render_report(
        self,
        status: str,
        parsed: ParsedModConfig,
        summary: Dict[str, Any],
        issues: List[Dict[str, Any]],
        optimized: str,
        ai_error: Optional[Exception],
    ) -> str:
        status_label = {
            "valid": "✅ 有效",
            "warn": "⚠️ 有问题需关注",
            "error": "❌ 错误",
        }.get(status, "⚠️ 警告")

        lines = ["📄 模组配置诊断报告", "", "🔍 配置概览："]
        lines.append(f"- 状态：{status_label}")
        lines.append(f"- 已配置模组：{summary.get('mod_count', parsed.mod_count)} 个")
        lines.append(f"- 总配置项：{parsed.option_count} 个")
        lines.append(f"- 问题数量：{summary.get('issue_count', len(issues))} 个")
        lines.append(f"- 严重问题：{summary.get('critical_count', 0)} 个")
        lines.append(f"- 建议项：{summary.get('suggestion_count', 0)} 个")

        if parsed.warnings:
            lines.append("")
            lines.append("⚠️ 解析警告：")
            for item in parsed.warnings:
                lines.append(f"- {item}")

        grouped = {"critical": [], "warning": [], "info": []}
        for issue in issues:
            level = self._normalize_issue_level(issue.get("level"))
            issue["level"] = level
            grouped[level].append(issue)

        if any(grouped.values()):
            lines.append("")
            lines.append("❌ 发现的问题：")
            level_titles = {
                "critical": "❌ 严重问题",
                "warning": "⚠️ 警告问题",
                "info": "ℹ️ 建议优化",
            }
            for level in ("critical", "warning", "info"):
                items = grouped[level]
                if not items:
                    continue
                lines.append("")
                lines.append(level_titles[level])
                for idx, issue in enumerate(items, 1):
                    mod_name = issue.get("mod_name") or issue.get("mod_id") or "未知模组"
                    title = issue.get("title") or issue.get("issue_type") or "配置问题"
                    description = issue.get("description") or "未提供"
                    impact = issue.get("impact") or "未提供"
                    current_value = self._format_issue_value(issue.get("current_value"))
                    suggested_value = self._format_issue_value(issue.get("suggested_value"))
                    reason = issue.get("reason") or "未提供"
                    config_path = issue.get("config_path") or ""
                    lines.append(f"{idx}. 【{mod_name}】{title}")
                    lines.append(f"   - 描述：{description}")
                    lines.append(f"   - 影响：{impact}")
                    lines.append(f"   - 当前值：{current_value}")
                    lines.append(f"   - 建议值：{suggested_value}")
                    lines.append(f"   - 修改理由：{reason}")
                    if config_path:
                        lines.append(f"   - 配置路径：{config_path}")
        else:
            lines.append("")
            lines.append("✅ 未发现明显问题")

        lines.append("")
        lines.append("📋 优化后的配置：")
        lines.append("```lua")
        lines.append(optimized)
        lines.append("```")

        lines.append("")
        lines.append("🚀 如何应用配置：")
        lines.append("- 使用 /dst mod config save <房间ID> <世界ID> --optimized 保存优化配置")
        lines.append("- 应用后请重启房间以生效")

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
        if isinstance(value, list):
            return self._format_lua_table(value)
        if isinstance(value, dict):
            return self._format_lua_table(value)
        return f"\"{str(value)}\""

    def _format_lua_table(self, value: Any) -> str:
        if isinstance(value, list):
            items = ", ".join(self._format_lua_value(item) for item in value)
            return f"{{ {items} }}"
        if isinstance(value, dict):
            pairs = []
            for key, item in value.items():
                pairs.append(f"{self._format_lua_key(key)} = {self._format_lua_value(item)}")
            inner = ", ".join(pairs)
            return f"{{ {inner} }}"
        return "{}"

    def _format_lua_key(self, key: Any) -> str:
        if isinstance(key, (int, float)):
            return f"[{key}]"
        key_str = str(key)
        if re.match(r"^[A-Za-z_][A-Za-z0-9_]*$", key_str):
            return key_str
        escaped = key_str.replace("\\", "\\\\").replace("\"", "\\\"")
        return f"[\"{escaped}\"]"

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

    def _normalize_status(self, value: Any) -> str:
        text = str(value or "").strip().lower()
        if text in ("valid", "ok", "success"):
            return "valid"
        if text in ("error", "fail", "failed", "critical"):
            return "error"
        if text in ("warn", "warning", "warnings"):
            return "warn"
        return "warn"

    def _normalize_issue_level(self, value: Any) -> str:
        text = str(value or "").strip().lower()
        if text in ("critical", "error", "high", "severe"):
            return "critical"
        if text in ("warn", "warning", "medium"):
            return "warning"
        if text in ("info", "low", "suggestion", "hint"):
            return "info"
        return "warning"

    def _normalize_issues(self, value: Any) -> List[Dict[str, Any]]:
        if not isinstance(value, list):
            return []
        issues: List[Dict[str, Any]] = []
        for item in value:
            if not isinstance(item, dict):
                issues.append(
                    {
                        "level": "warning",
                        "mod_id": "",
                        "mod_name": "",
                        "issue_type": "other",
                        "title": str(item),
                        "description": "",
                        "impact": "",
                        "current_value": None,
                        "suggested_value": None,
                        "reason": "",
                        "config_path": "",
                    }
                )
                continue
            issues.append(
                {
                    "level": item.get("level") or "warning",
                    "mod_id": str(item.get("mod_id") or ""),
                    "mod_name": str(item.get("mod_name") or ""),
                    "issue_type": str(item.get("issue_type") or "other"),
                    "title": str(item.get("title") or ""),
                    "description": str(item.get("description") or ""),
                    "impact": str(item.get("impact") or ""),
                    "current_value": item.get("current_value"),
                    "suggested_value": item.get("suggested_value"),
                    "reason": str(item.get("reason") or ""),
                    "config_path": str(item.get("config_path") or ""),
                }
            )
        return issues

    def _build_summary(
        self,
        parsed: ParsedModConfig,
        issues: List[Dict[str, Any]],
        summary: Optional[Dict[str, Any]],
    ) -> Dict[str, Any]:
        critical_count = sum(
            1 for issue in issues if self._normalize_issue_level(issue.get("level")) == "critical"
        )
        suggestion_count = sum(
            1
            for issue in issues
            if issue.get("suggested_value") not in (None, "")
            or self._normalize_issue_level(issue.get("level")) == "info"
        )
        result = {
            "mod_count": parsed.mod_count,
            "issue_count": len(issues),
            "critical_count": critical_count,
            "suggestion_count": suggestion_count,
        }
        if isinstance(summary, dict):
            for key in result:
                value = summary.get(key)
                if isinstance(value, int):
                    result[key] = value
        return result

    def _convert_legacy_issues(
        self,
        warnings: List[Any],
        suggestions: List[Any],
    ) -> List[Dict[str, Any]]:
        issues: List[Dict[str, Any]] = []
        for warn in warnings:
            if isinstance(warn, dict):
                mod_id = warn.get("mod_id") or ""
                title = warn.get("issue") or warn.get("title") or "配置问题"
                suggestion = warn.get("suggestion") or ""
            else:
                mod_id = ""
                title = str(warn)
                suggestion = ""
            issues.append(
                {
                    "level": "warning",
                    "mod_id": str(mod_id),
                    "mod_name": "",
                    "issue_type": "other",
                    "title": str(title),
                    "description": "",
                    "impact": "",
                    "current_value": None,
                    "suggested_value": suggestion or None,
                    "reason": "",
                    "config_path": "",
                }
            )
        for suggestion in suggestions:
            issues.append(
                {
                    "level": "info",
                    "mod_id": "",
                    "mod_name": "",
                    "issue_type": "suggestion",
                    "title": str(suggestion),
                    "description": "",
                    "impact": "",
                    "current_value": None,
                    "suggested_value": None,
                    "reason": "",
                    "config_path": "",
                }
            )
        return issues

    def _format_issue_value(self, value: Any) -> str:
        if value is None:
            return "未提供"
        if isinstance(value, bool):
            return "true" if value else "false"
        if isinstance(value, (int, float)):
            return str(value)
        return str(value)

