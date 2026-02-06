"""
DST 服务器 AI 配置分析器

负责汇总房间信息、模组数据与玩家统计，并调用 AI 输出分析报告。
"""

from __future__ import annotations

import json
from typing import Any, Dict, List, Optional

from loguru import logger

from .base import AIError, format_ai_error
from .client import AIClient
from ..client.api_client import DSTApiClient


class ServerConfigAnalyzer:
    """
    DST 服务器配置分析器

    Attributes:
        api_client: DMP API 客户端
        ai_client: AI 客户端
    """

    def __init__(self, api_client: DSTApiClient, ai_client: AIClient) -> None:
        """
        初始化分析器

        Args:
            api_client: DMP API 客户端
            ai_client: AI 客户端
        """
        self.api_client = api_client
        self.ai_client = ai_client

    async def analyze_server(self, room_id: int) -> str:
        """
        分析指定房间的服务器配置并返回 Markdown 报告

        Args:
            room_id: 房间 ID

        Returns:
            str: Markdown 格式的分析报告

        Raises:
            RuntimeError: 当房间信息获取失败时抛出
        """
        room_result = await self.api_client.get_room_info(room_id)
        if not room_result.get("success"):
            error = room_result.get("error") or "未知错误"
            raise RuntimeError(f"获取房间信息失败：{error}")

        room_info = room_result.get("data") or {}

        mods_result = await self.api_client.get_room_mods(room_id)
        mods_data = mods_result.get("data") if mods_result.get("success") else None

        stats_result = await self.api_client.get_room_stats(room_id)
        stats_data = stats_result.get("data") if stats_result.get("success") else None

        prompt = self._build_prompt(room_info, mods_data, stats_data)
        system_prompt = self._system_prompt()

        try:
            response = await self.ai_client.chat(
                [{"role": "user", "content": prompt}],
                system_prompt=system_prompt,
            )
            if response and response.strip():
                return response.strip()
        except AIError as exc:
            logger.warning("AI 分析失败，回退到本地报告：{err}", err=exc)
            return self._build_fallback_report(room_info, mods_data, stats_data, exc)
        except Exception as exc:
            logger.exception("分析器发生未知错误：{err}", err=exc)
            return self._build_fallback_report(room_info, mods_data, stats_data, exc)

        return self._build_fallback_report(room_info, mods_data, stats_data, None)

    def _system_prompt(self) -> str:
        """构建系统提示词。"""
        return "你是 DST 服务器配置专家，擅长分析房间配置、模组冲突与性能风险。"

    def _build_prompt(
        self,
        room_info: Dict[str, Any],
        mods_data: Optional[Dict[str, Any]],
        stats_data: Optional[Dict[str, Any]],
    ) -> str:
        """构建 AI 提示词。"""
        payload = {
            "room": self._summarize_room(room_info),
            "mods": mods_data or {"enabled": [], "disabled": [], "duplicates": []},
            "stats": stats_data or {},
        }

        return (
            "请根据以下 DST 房间配置生成分析报告：\n\n"
            f"配置数据(JSON)：\n{json.dumps(payload, ensure_ascii=True, indent=2)}\n\n"
            "输出要求：\n"
            "1. 使用 Markdown 格式，包含标题和分段。\n"
            "2. 包含基础信息（房间名、模式、玩家限制）。\n"
            "3. 模组统计（数量、冲突检测）。\n"
            "4. 性能预测（CPU、内存、延迟）。\n"
            "5. 提供 3-5 条优化建议。\n"
            "6. 总评分 1-10 分，并给出简短评价。\n"
        )

    def _build_fallback_report(
        self,
        room_info: Dict[str, Any],
        mods_data: Optional[Dict[str, Any]],
        stats_data: Optional[Dict[str, Any]],
        error: Optional[Exception],
    ) -> str:
        """生成本地兜底报告。"""
        room_name = room_info.get("gameName", "未知房间")
        game_mode = room_info.get("gameMode", "未知")
        max_players = room_info.get("maxPlayer", 0)

        mods_data = mods_data or {}
        enabled = mods_data.get("enabled") or []
        disabled = mods_data.get("disabled") or []
        duplicates = mods_data.get("duplicates") or []
        mod_count = len(enabled) + len(disabled)

        stats_data = stats_data or {}
        online_players = stats_data.get("online_players")

        cpu_level, mem_level, latency = self._estimate_performance(mod_count, max_players)

        suggestions = self._build_suggestions(mod_count, duplicates, max_players)

        lines = [
            "🔍 DST 服务器分析报告（本地生成）",
            "",
            "📊 基本信息：",
            f"- 房间名：{room_name}",
            f"- 模式：{game_mode}",
            f"- 玩家限制：{max_players}人",
        ]

        if online_players is not None:
            lines.append(f"- 当前在线：{online_players}人")

        lines.extend([
            "",
            "🧩 模组统计：",
            f"- 已安装：{mod_count}个",
            f"- 已启用：{len(enabled)}个 | 已禁用：{len(disabled)}个",
        ])

        if duplicates:
            lines.append(f"- 冲突检测：{len(duplicates)}个潜在重复条目")
        else:
            lines.append("- 冲突检测：未发现明显重复")

        lines.extend([
            "",
            "⚡ 性能预测：",
            f"- CPU 使用：{cpu_level}",
            f"- 内存使用：{mem_level}",
            f"- 延迟表现：{latency}",
            "",
            "💡 优化建议：",
        ])

        for idx, suggestion in enumerate(suggestions, 1):
            lines.append(f"{idx}. {suggestion}")

        score = self._estimate_score(mod_count, duplicates, max_players)
        lines.extend([
            "",
            f"📈 总评分：{score}/10",
        ])

        if error is not None:
            lines.append("")
            if isinstance(error, AIError):
                lines.append(f"⚠️ AI 分析失败：{format_ai_error(error)}")
            else:
                lines.append(f"⚠️ AI 分析失败：{error}")

        return "\n".join(lines)

    def _summarize_room(self, room_info: Dict[str, Any]) -> Dict[str, Any]:
        """提取房间摘要字段，避免向 AI 发送过多数据。"""
        return {
            "id": room_info.get("id"),
            "name": room_info.get("gameName"),
            "mode": room_info.get("gameMode"),
            "max_players": room_info.get("maxPlayer"),
            "pvp": bool(room_info.get("pvp")),
            "password": bool(room_info.get("password")),
            "description": room_info.get("description"),
        }

    def _estimate_performance(self, mod_count: int, max_players: int) -> tuple[str, str, str]:
        """根据模组数量与玩家限制估算性能。"""
        if mod_count <= 5 and max_players <= 6:
            return "低 (~20-30%)", "低 (~1-2GB)", "优秀 (<80ms)"
        if mod_count <= 15 and max_players <= 10:
            return "中等 (~30-50%)", "中等 (~2-3GB)", "良好 (<120ms)"
        if mod_count <= 25 and max_players <= 12:
            return "偏高 (~50-70%)", "偏高 (~3-4GB)", "一般 (120-180ms)"
        return "高 (~70%+)", "高 (~4GB+)", "偏高 (180ms+)"

    def _build_suggestions(self, mod_count: int, duplicates: List[str], max_players: int) -> List[str]:
        """根据统计数据生成建议列表。"""
        suggestions: List[str] = []

        if mod_count > 20:
            suggestions.append("模组数量较多，建议清理不常用模组以降低资源占用")
        if duplicates:
            suggestions.append("检测到重复模组条目，建议检查 modData 配置并去重")
        if max_players >= 12:
            suggestions.append("玩家上限较高，建议监控 CPU/内存并预留性能裕度")
        suggestions.append("建议设置定期自动保存与备份，降低异常宕机风险")
        suggestions.append("如需提升稳定性，可保持世界配置与模组版本同步更新")

        return suggestions[:5]

    def _estimate_score(self, mod_count: int, duplicates: List[str], max_players: int) -> int:
        """粗略估算评分（1-10）。"""
        score = 9
        score -= min(4, mod_count // 8)
        score -= min(2, len(duplicates))
        if max_players >= 12:
            score -= 1
        return max(1, min(10, score))
