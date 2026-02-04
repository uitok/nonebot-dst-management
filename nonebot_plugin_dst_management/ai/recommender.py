"""
DST 模组推荐器

基于当前房间模组配置与热门模组池，调用 AI 输出推荐报告。
"""

from __future__ import annotations

import json
import time
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

from loguru import logger

from .base import AIError, format_ai_error
from .client import AIClient
from ..client.api_client import DSTApiClient


@dataclass(frozen=True)
class ModCandidate:
    """候选模组结构"""

    mod_id: str
    name: str
    mod_type: str
    tags: Tuple[str, ...] = ()


@dataclass(frozen=True)
class ModRecommendation:
    """推荐结果结构"""

    mod_id: str
    name: str
    score: float
    reason: str


class ModRecommender:
    """
    模组推荐器

    Attributes:
        api_client: DMP API 客户端
        ai_client: AI 客户端
    """

    _cache: Dict[str, Tuple[float, Dict[str, Any]]]

    def __init__(self, api_client: DSTApiClient, ai_client: AIClient) -> None:
        self.api_client = api_client
        self.ai_client = ai_client
        self._cache = {}

    async def recommend_mods(self, room_id: int, mod_type: Optional[str] = None) -> Dict[str, Any]:
        """
        推荐模组并生成 Markdown 报告

        Args:
            room_id: 房间 ID
            mod_type: 模组类型（可选）

        Returns:
            Dict[str, Any]: {
                "report": str,
                "recommendations": List[Dict[str, Any]],
                "cached": bool,
            }
        """
        cache_key = f"{room_id}:{(mod_type or '').lower()}"
        cached = self._get_cached(cache_key, ttl=86400)
        if cached is not None:
            return {**cached, "cached": True}

        mods_result = await self.api_client.get_room_mods(room_id)
        if not mods_result.get("success"):
            error = mods_result.get("error") or "未知错误"
            raise RuntimeError(f"获取房间模组失败：{error}")

        mods_data = mods_result.get("data") or {}
        installed = set((mods_data.get("enabled") or []) + (mods_data.get("disabled") or []))
        duplicates = mods_data.get("duplicates") or []

        candidates = await self._get_top_mods()
        filtered, filtered_reason = self._filter_candidates(candidates, installed, mod_type)

        prompt = self._build_prompt(room_id, mod_type, installed, filtered)
        system_prompt = self._system_prompt()

        try:
            response = await self.ai_client.chat(
                [{"role": "user", "content": prompt}],
                system_prompt=system_prompt,
            )
            recommendations = self._parse_ai_response(response, filtered)
        except AIError as exc:
            logger.warning("AI 模组推荐失败，回退本地推荐：{err}", err=exc)
            recommendations = self._fallback_recommendations(filtered)
            report = self._build_report(
                room_id,
                mod_type,
                installed,
                duplicates,
                recommendations,
                filtered_reason,
                ai_error=exc,
            )
            result = {"report": report, "recommendations": recommendations}
            self._set_cached(cache_key, result)
            return {**result, "cached": False}
        except Exception as exc:
            logger.exception("模组推荐发生未知错误：{err}", err=exc)
            recommendations = self._fallback_recommendations(filtered)
            report = self._build_report(
                room_id,
                mod_type,
                installed,
                duplicates,
                recommendations,
                filtered_reason,
                ai_error=exc,
            )
            result = {"report": report, "recommendations": recommendations}
            self._set_cached(cache_key, result)
            return {**result, "cached": False}

        report = self._build_report(
            room_id,
            mod_type,
            installed,
            duplicates,
            recommendations,
            filtered_reason,
            ai_error=None,
        )
        result = {"report": report, "recommendations": recommendations}
        self._set_cached(cache_key, result)
        return {**result, "cached": False}

    async def _get_top_mods(self) -> List[ModCandidate]:
        """获取热门模组池（Top 50）。"""
        if hasattr(self.api_client, "search_mod"):
            try:
                result = await self.api_client.search_mod("hot", "50")  # type: ignore[attr-defined]
                if result.get("success"):
                    return self._convert_search_results(result.get("data") or [])
            except Exception as exc:
                logger.warning("热门模组拉取失败，使用内置池：{err}", err=exc)
        return list(_DEFAULT_MOD_POOL)

    def _convert_search_results(self, data: List[Dict[str, Any]]) -> List[ModCandidate]:
        candidates: List[ModCandidate] = []
        for item in data:
            mod_id = item.get("id") or item.get("modId") or item.get("mod_id")
            name = item.get("name") or item.get("title") or "Unknown Mod"
            mod_type = item.get("type") or item.get("category") or "functional"
            if not mod_id:
                continue
            mod_id_str = str(mod_id)
            if not mod_id_str.startswith("workshop-"):
                mod_id_str = f"workshop-{mod_id_str}"
            candidates.append(ModCandidate(mod_id_str, str(name), str(mod_type), ()))
        if candidates:
            return candidates[:50]
        return list(_DEFAULT_MOD_POOL)

    def _filter_candidates(
        self,
        candidates: List[ModCandidate],
        installed: set[str],
        mod_type: Optional[str],
    ) -> Tuple[List[ModCandidate], str]:
        """过滤已安装与冲突模组，并按类型筛选。"""
        mod_type_norm = mod_type.lower().strip() if mod_type else ""
        filtered: List[ModCandidate] = []
        filtered_out = 0

        for mod in candidates:
            if mod.mod_id in installed:
                filtered_out += 1
                continue
            conflicts = _CONFLICT_MAP.get(mod.mod_id, set())
            if conflicts.intersection(installed):
                filtered_out += 1
                continue
            if mod_type_norm and mod.mod_type.lower() != mod_type_norm:
                continue
            filtered.append(mod)

        reason = f"已过滤 {filtered_out} 个已安装/冲突模组"
        return filtered, reason

    def _build_prompt(
        self,
        room_id: int,
        mod_type: Optional[str],
        installed: set[str],
        candidates: List[ModCandidate],
    ) -> str:
        payload = {
            "room_id": room_id,
            "mod_type": mod_type or "all",
            "installed_mods": sorted(installed),
            "candidates": [
                {
                    "id": mod.mod_id,
                    "name": mod.name,
                    "type": mod.mod_type,
                    "tags": list(mod.tags),
                }
                for mod in candidates
            ],
        }

        return (
            "你是 DST 模组推荐专家，请根据候选模组池和当前已安装模组，推荐最适合的 5 个模组。\n\n"
            f"输入数据(JSON)：\n{json.dumps(payload, ensure_ascii=True, indent=2)}\n\n"
            "要求：\n"
            "1. 输出 JSON 格式，键名为 recommendations。\n"
            "2. recommendations 为数组，每项包含 mod_id, name, score(1-10), reason。\n"
            "3. 推荐应避免与已安装模组冲突。\n"
            "4. 只返回 5 个推荐。\n"
        )

    def _system_prompt(self) -> str:
        return "你是 DST 服务器模组专家，擅长分析模组兼容性与玩法需求。"

    def _parse_ai_response(self, response: str, candidates: List[ModCandidate]) -> List[Dict[str, Any]]:
        data = self._extract_json(response)
        if not isinstance(data, dict):
            raise ValueError("AI 响应不是 JSON 对象")
        items = data.get("recommendations")
        if not isinstance(items, list):
            raise ValueError("AI 响应缺少 recommendations")

        candidate_map = {mod.mod_id: mod for mod in candidates}
        recommendations: List[Dict[str, Any]] = []
        for item in items[:5]:
            if not isinstance(item, dict):
                continue
            mod_id = str(item.get("mod_id") or item.get("id") or "").strip()
            if not mod_id:
                continue
            if not mod_id.startswith("workshop-"):
                mod_id = f"workshop-{mod_id}"
            name = str(item.get("name") or candidate_map.get(mod_id, ModCandidate(mod_id, mod_id, "")).name)
            score = float(item.get("score") or 8.0)
            reason = str(item.get("reason") or "推荐")
            recommendations.append(
                {
                    "mod_id": mod_id,
                    "name": name,
                    "score": score,
                    "reason": reason,
                }
            )

        if not recommendations:
            raise ValueError("AI 推荐结果为空")
        return recommendations[:5]

    def _fallback_recommendations(self, candidates: List[ModCandidate]) -> List[Dict[str, Any]]:
        recommendations: List[Dict[str, Any]] = []
        for idx, mod in enumerate(candidates[:5], 1):
            recommendations.append(
                {
                    "mod_id": mod.mod_id,
                    "name": mod.name,
                    "score": round(9.5 - idx * 0.3, 1),
                    "reason": "基于热门度与兼容性进行本地推荐",
                }
            )
        return recommendations

    def _build_report(
        self,
        room_id: int,
        mod_type: Optional[str],
        installed: set[str],
        duplicates: List[str],
        recommendations: List[Dict[str, Any]],
        filtered_reason: str,
        ai_error: Optional[Exception],
    ) -> str:
        mod_type_label = mod_type or "全部"
        lines = ["🧩 模组推荐报告", ""]
        lines.append("📊 当前配置：")
        lines.append(f"- 房间ID：{room_id}")
        lines.append(f"- 已安装模组：{len(installed)} 个")
        lines.append(f"- 推荐类型：{mod_type_label}")
        lines.append(f"- {filtered_reason}")

        if duplicates:
            lines.append(f"- ⚠️ 检测到重复条目：{len(duplicates)} 个")

        lines.append("")
        lines.append("🎯 推荐模组（Top 5）：")
        for idx, item in enumerate(recommendations, 1):
            mod_id = item.get("mod_id", "未知")
            name = item.get("name", "未知模组")
            score = item.get("score", "-")
            reason = item.get("reason", "-")
            lines.append(f"\n{idx}. {name}")
            lines.append(f"   📝 模组ID: {mod_id}")
            lines.append(f"   ⭐ 评分: {score}/10")
            lines.append(f"   💡 理由: {reason}")
            lines.append(f"   📦 安装: /dst mod add {room_id} Master {mod_id}")

        if ai_error is not None:
            lines.append("")
            if isinstance(ai_error, AIError):
                lines.append(f"⚠️ AI 推荐失败：{format_ai_error(ai_error)}")
            else:
                lines.append(f"⚠️ AI 推荐失败：{ai_error}")

        return "\n".join(lines)

    def _extract_json(self, text: str) -> Any:
        text = text.strip()
        if not text:
            raise ValueError("empty response")

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


_DEFAULT_MOD_POOL: Tuple[ModCandidate, ...] = tuple(
    ModCandidate(
        mod_id=f"workshop-{1000000000 + idx}",
        name=f"Popular Mod {idx:02d}",
        mod_type="functional" if idx % 3 == 0 else "decorative" if idx % 3 == 1 else "balance",
        tags=("popular", "stable"),
    )
    for idx in range(1, 51)
)

_CONFLICT_MAP: Dict[str, set[str]] = {
    "workshop-1000000001": {"workshop-1000000002"},
    "workshop-1000000005": {"workshop-1000000010"},
}
