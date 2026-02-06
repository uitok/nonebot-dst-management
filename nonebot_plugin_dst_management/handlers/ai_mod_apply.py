"""
AI 模组配置应用命令处理器

提供 /dst mod config show 和 /dst mod config apply 命令。
"""

from __future__ import annotations

import argparse
import difflib
import shlex
from typing import Any, Dict, List, Optional, Tuple

from nonebot import on_command
from nonebot.adapters.onebot.v11 import Bot, MessageEvent, Message
from nonebot.params import CommandArg

from ..ai.mod_parser import ModConfigParser
from ..ai.client import AIClient
from ..client.api_client import DSTApiClient
from ..utils.permission import check_admin, check_group
from ..utils.formatter import format_error, format_info, format_success


def _build_show_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="dst mod config show", add_help=False)
    parser.add_argument("room_id")
    parser.add_argument("world_id")
    return parser


def _build_apply_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="dst mod config apply", add_help=False)
    parser.add_argument("room_id")
    parser.add_argument("world_id")
    parser.add_argument("--auto", action="store_true", dest="auto")
    parser.add_argument("--dry-run", action="store_true", dest="dry_run")
    return parser


def _parse_args(
    parser: argparse.ArgumentParser, raw: str
) -> Tuple[Optional[argparse.Namespace], Optional[Message]]:
    if not raw:
        return None, format_error(f"用法：/{parser.prog} <房间ID> <世界ID>")
    try:
        args = parser.parse_args(shlex.split(raw))
    except SystemExit:
        return None, format_error(f"用法：/{parser.prog} <房间ID> <世界ID>")
    return args, None


def _status_label(status: str) -> str:
    return {
        "valid": "✅ 有效",
        "warn": "⚠️ 有问题需关注",
        "error": "❌ 错误",
    }.get(str(status or "").strip().lower(), "⚠️ 警告")


def _format_issue_lines(issues: List[Dict[str, Any]]) -> List[str]:
    grouped: Dict[str, List[Dict[str, Any]]] = {"critical": [], "warning": [], "info": []}
    for issue in issues:
        level = str(issue.get("level") or "warning").strip().lower()
        if level not in grouped:
            level = "warning"
        grouped[level].append(issue)

    lines: List[str] = []
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
            current_value = issue.get("current_value")
            suggested_value = issue.get("suggested_value")
            lines.append(f"{idx}. 【{mod_name}】{title}")
            lines.append(f"   - 描述：{description}")
            lines.append(f"   - 影响：{impact}")
            if current_value is not None:
                lines.append(f"   - 当前值：{current_value}")
            if suggested_value is not None:
                lines.append(f"   - 建议值：{suggested_value}")
    return lines


def _build_cached_report(cached: Dict[str, Any]) -> str:
    report = cached.get("report")
    if isinstance(report, str) and report.strip():
        return report

    status = cached.get("status") or "warn"
    summary = cached.get("summary") or {}
    issues = cached.get("issues") or []

    lines = ["📄 模组配置诊断报告（缓存）", "", "🔍 配置概览："]
    lines.append(f"- 状态：{_status_label(status)}")
    lines.append(f"- 已配置模组：{summary.get('mod_count', 0)} 个")
    lines.append(f"- 问题数量：{summary.get('issue_count', len(issues))} 个")
    lines.append(f"- 严重问题：{summary.get('critical_count', 0)} 个")
    lines.append(f"- 建议项：{summary.get('suggestion_count', 0)} 个")

    if issues:
        lines.append("")
        lines.append("❌ 发现的问题：")
        lines.extend(_format_issue_lines(issues))
    else:
        lines.append("")
        lines.append("✅ 未发现明显问题")

    return "\n".join(lines)


def _resolve_save_handler(api_client: DSTApiClient):
    for name in ("save_mod_config", "update_modoverrides", "update_mod_config", "save_modoverrides"):
        if hasattr(api_client, name):
            return getattr(api_client, name)
    return None


def _build_diff(current: str, optimized: str) -> str:
    diff = difflib.unified_diff(
        current.splitlines(),
        optimized.splitlines(),
        fromfile="current",
        tofile="optimized",
        lineterm="",
    )
    return "\n".join(diff)


def _extract_text(args: Message, event: MessageEvent) -> str:
    raw = None
    if hasattr(args, "extract_plain_text"):
        raw = args.extract_plain_text()
    if not isinstance(raw, str) and hasattr(event, "extract_plain_text"):
        raw = event.extract_plain_text()
    if raw is None:
        raw = ""
    return str(raw).strip()


def init(api_client: DSTApiClient, ai_client: AIClient) -> None:
    """
    初始化 AI 模组配置应用命令

    Args:
        api_client: DMP API 客户端实例
        ai_client: AI 客户端实例
    """

    parser = ModConfigParser(api_client, ai_client)
    show_parser = _build_show_parser()
    apply_parser = _build_apply_parser()

    show_cmd = on_command("dst mod config show", priority=10, block=True)

    @show_cmd.handle()
    async def handle_show(event: MessageEvent, args: Message = CommandArg()):
        if not await check_group(event):
            await show_cmd.finish(format_error("当前群组未授权使用此功能"))
            return

        raw = _extract_text(args, event)
        parsed, error = _parse_args(show_parser, raw)
        if error:
            await show_cmd.finish(error)
            return

        if not str(parsed.room_id).isdigit():
            await show_cmd.finish(format_error("请提供有效的房间ID"))
            return

        room_id = int(parsed.room_id)
        world_id = str(parsed.world_id)
        cached = parser.get_cached_result(room_id, world_id)
        if not cached:
            await show_cmd.finish(
                format_error("未找到缓存的分析结果，请先运行 /dst mod parse <房间ID> <世界ID>")
            )
            return

        report = _build_cached_report(cached)
        await show_cmd.finish(Message(report))

    apply_cmd = on_command("dst mod config apply", priority=10, block=True)

    @apply_cmd.handle()
    async def handle_apply(bot: Bot, event: MessageEvent, args: Message = CommandArg()):
        if not await check_group(event):
            await apply_cmd.finish(format_error("当前群组未授权使用此功能"))
            return
        if not await check_admin(bot, event):
            await apply_cmd.finish(format_error("只有管理员才能执行此操作"))
            return

        raw = _extract_text(args, event)
        parsed, error = _parse_args(apply_parser, raw)
        if error:
            await apply_cmd.finish(error)
            return

        if not str(parsed.room_id).isdigit():
            await apply_cmd.finish(format_error("请提供有效的房间ID"))
            return

        room_id = int(parsed.room_id)
        world_id = str(parsed.world_id)

        cached = parser.get_cached_result(room_id, world_id)
        if not cached:
            await apply_cmd.finish(
                format_error("未找到缓存的分析结果，请先运行 /dst mod parse <房间ID> <世界ID>")
            )
            return

        optimized = cached.get("optimized_config")
        if not optimized:
            await apply_cmd.finish(format_error("缓存中未包含优化配置内容"))
            return

        if parsed.dry_run:
            await apply_cmd.send(format_info("正在生成差异预览..."))
            try:
                current = await parser.fetch_modoverrides(room_id, world_id)
            except Exception as exc:
                await apply_cmd.finish(format_error(f"获取当前配置失败：{exc}"))
                return

            diff_text = _build_diff(current, optimized)
            if not diff_text:
                await apply_cmd.finish(format_info("当前配置与优化配置无差异"))
                return

            lines = ["📋 配置差异预览", "", "```diff", diff_text, "```"]
            await apply_cmd.finish(Message("\n".join(lines)))
            return

        if not parsed.auto:
            await apply_cmd.finish(
                format_info("已检测到优化配置，请使用 --auto 应用，或使用 --dry-run 预览")
            )
            return

        save_handler = _resolve_save_handler(api_client)
        if save_handler is None:
            await apply_cmd.finish(format_error("当前 API 客户端未实现配置保存"))
            return

        await apply_cmd.send(format_info("正在保存优化配置..."))
        result = await save_handler(room_id, world_id, optimized)
        if not result.get("success"):
            await apply_cmd.finish(format_error(f"保存失败：{result.get('error')}"))
            return

        if hasattr(api_client, "restart_room"):
            await apply_cmd.send(format_info("正在重启房间..."))
            restart_result = await api_client.restart_room(room_id)
            if not restart_result.get("success"):
                await apply_cmd.finish(format_error(f"重启失败：{restart_result.get('error')}"))
                return

        await apply_cmd.finish(format_success("配置已应用并完成重启"))
