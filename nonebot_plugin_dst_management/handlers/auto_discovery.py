"""
Phase C (Auto): DST cluster auto discovery and import.

Commands:
- /dst room scan [--depth N] [path...]
  Scan directories to find DST clusters (directories containing cluster.ini).

- /dst room import --select <all|1,2|1-3> [--depth N] [path...]
  Scan and import selected clusters into plugin config (data/dst_clusters.json).
"""

from __future__ import annotations

import shlex
import asyncio
from pathlib import Path
from typing import Any, List, Optional, Tuple

from nonebot import on_command
from nonebot.adapters.onebot.v11 import Message
from nonebot.params import CommandArg

from ..helpers.formatters import (
    ICON_INFO,
    ICON_ROOM,
    ICON_TIP,
    build_qq_markdown_message,
    detect_bot_family,
    format_error,
    format_info,
    format_success,
    render,
    resolve_ui_mode,
)
from ..services.cluster_store import ClusterConfigEntry, get_cluster_config_path, load_cluster_config, merge_cluster_entries, save_cluster_config
from ..utils.path import discover_dst_clusters, normalize_path
from ..utils.permission import check_admin, check_group


def _to_platform_message(bot: Any, event: Any, message: Any) -> Any:
    """Convert OneBot Message helpers to a cross-adapter payload."""

    family = detect_bot_family(bot, event)
    if family == "qq":
        if hasattr(message, "extract_plain_text"):
            try:
                return str(message.extract_plain_text())
            except Exception:
                return str(message)
        return str(message)
    return message


def _split_args(raw: Any) -> List[str]:
    text = ""
    if hasattr(raw, "extract_plain_text"):
        try:
            text = str(raw.extract_plain_text())
        except Exception:
            text = str(raw)
    else:
        text = str(raw)
    text = (text or "").strip()
    if not text:
        return []
    try:
        return shlex.split(text)
    except ValueError:
        # Unbalanced quotes etc; fall back to naive split.
        return text.split()


def _default_scan_roots() -> List[Path]:
    # Common DST dedicated server save location on Linux.
    candidate = Path("~/.klei/DoNotStarveTogether").expanduser()
    if candidate.is_dir():
        return [candidate]
    return []


def _parse_scan_options(parts: List[str]) -> Tuple[int, List[Path], Optional[str]]:
    depth = 4
    paths: List[Path] = []

    i = 0
    while i < len(parts):
        token = parts[i]
        if token in {"--depth", "--max-depth", "-d"}:
            if i + 1 >= len(parts):
                return depth, paths, "缺少 --depth 参数值"
            value = parts[i + 1]
            if not value.isdigit():
                return depth, paths, "--depth 必须是非负整数"
            depth = max(0, int(value))
            i += 2
            continue
        paths.append(Path(token))
        i += 1

    if not paths:
        paths = _default_scan_roots()

    if not paths:
        return depth, [], "请提供扫描路径：/dst room scan <路径>（或将存档放在 ~/.klei/DoNotStarveTogether）"

    return depth, paths, None


def _parse_selection(selection: str, max_index: int) -> Tuple[Optional[List[int]], Optional[str]]:
    raw = (selection or "").strip().lower()
    if not raw:
        return None, "请选择要导入的序号（或 all）"
    if raw == "all":
        return list(range(1, max_index + 1)), None

    chosen: set[int] = set()
    for part in raw.replace(" ", "").split(","):
        if not part:
            continue
        if "-" in part:
            left, right = part.split("-", 1)
            if not left.isdigit() or not right.isdigit():
                return None, f"无效范围：{part}"
            start = int(left)
            end = int(right)
            if start <= 0 or end <= 0:
                return None, f"序号必须是正整数：{part}"
            if start > end:
                start, end = end, start
            for idx in range(start, end + 1):
                chosen.add(idx)
            continue
        if not part.isdigit():
            return None, f"无效序号：{part}"
        idx = int(part)
        if idx <= 0:
            return None, "序号必须是正整数"
        chosen.add(idx)

    if not chosen:
        return None, "未选择任何序号"

    invalid = [idx for idx in chosen if idx > max_index]
    if invalid:
        return None, f"序号超出范围：{', '.join(str(x) for x in sorted(invalid))}"

    return sorted(chosen), None


async def _render_scan_result(
    *,
    bot: Any,
    event: Any,
    roots: List[Path],
    depth: int,
    clusters,
) -> Any:
    family = detect_bot_family(bot, event)
    mode = await resolve_ui_mode(bot=bot, event=event)
    if family != "qq":
        mode = "text"
    if family == "onebot_v11":
        mode = "text"

    headers = ["#", "房间名", "世界", "Token", "路径"]
    rows: List[List[str]] = []

    primary_root = normalize_path(roots[0]) if len(roots) == 1 else None

    for idx, item in enumerate(clusters, 1):
        token_flag = "Y" if item.token else "N"
        display_path: str
        if primary_root is not None:
            try:
                rel = normalize_path(item.path).relative_to(primary_root)
                display_path = str(rel)
            except Exception:
                display_path = str(item.path)
        else:
            display_path = str(item.path)

        rows.append(
            [
                str(idx),
                item.display_name,
                item.worlds_label,
                token_flag,
                display_path,
            ]
        )

    table_obj = render("table", mode=mode, headers=headers, rows=rows)
    count = len(clusters)

    if mode == "markdown":
        # `table_obj` is a Markdown code block string.
        roots_text = ", ".join(f"`{normalize_path(p)}`" for p in roots)
        md = "\n".join(
            [
                f"# {ICON_ROOM} 自动发现结果",
                f"- **扫描路径**：{roots_text}",
                f"- **深度**：`{depth}`",
                f"- **发现**：**{count}** 个集群",
                "",
                str(table_obj),
                "",
                f"{ICON_TIP} 导入：`/dst room import --select all <同样的路径>`",
                f"{ICON_TIP} 导入部分：`/dst room import --select 1,3-5 <同样的路径>`",
            ]
        ).strip()
        return build_qq_markdown_message(md)

    # text
    if hasattr(table_obj, "extract_plain_text"):
        try:
            table_text = str(table_obj.extract_plain_text())
        except Exception:
            table_text = str(table_obj)
    else:
        table_text = str(table_obj)
    roots_text = ", ".join(str(normalize_path(p)) for p in roots)
    text = "\n".join(
        [
            f"{ICON_INFO} 自动发现结果",
            f"- 扫描路径：{roots_text}",
            f"- 深度：{depth}",
            f"- 发现：{count} 个集群",
            "",
            table_text,
            "",
            f"{ICON_TIP} 导入：/dst room import --select all <同样的路径>",
            f"{ICON_TIP} 导入部分：/dst room import --select 1,3-5 <同样的路径>",
        ]
    ).strip()
    if family == "qq":
        return text
    return Message(text)


def init() -> None:
    # ========== Scan ==========
    scan_cmd = on_command(
        "dst room scan",
        aliases={"dst 房间扫描", "dst 扫描房间", "dst room discover", "dst scan"},
        priority=5,
        block=True,
    )

    @scan_cmd.handle()
    async def handle_scan(bot: Any, event: Any, args: Message = CommandArg()):
        if not await check_group(event):
            await scan_cmd.finish(_to_platform_message(bot, event, format_error("当前群组未授权使用此功能")))
            return
        if not await check_admin(bot, event):
            await scan_cmd.finish(_to_platform_message(bot, event, format_error("只有管理员才能执行此操作")))
            return

        parts = _split_args(args)
        depth, roots, error = _parse_scan_options(parts)
        if error:
            await scan_cmd.finish(_to_platform_message(bot, event, format_error(error)))
            return

        clusters = await asyncio.to_thread(discover_dst_clusters, roots, max_depth=depth)
        message = await _render_scan_result(
            bot=bot,
            event=event,
            roots=roots,
            depth=depth,
            clusters=clusters,
        )
        await scan_cmd.finish(message)

    # ========== Import ==========
    import_cmd = on_command(
        "dst room import",
        aliases={"dst 房间导入", "dst 导入房间", "dst room setup", "dst setup"},
        priority=5,
        block=True,
    )

    @import_cmd.handle()
    async def handle_import(bot: Any, event: Any, args: Message = CommandArg()):
        if not await check_group(event):
            await import_cmd.finish(_to_platform_message(bot, event, format_error("当前群组未授权使用此功能")))
            return
        if not await check_admin(bot, event):
            await import_cmd.finish(_to_platform_message(bot, event, format_error("只有管理员才能执行此操作")))
            return

        parts = _split_args(args)

        depth = 4
        selection: Optional[str] = None
        paths: List[Path] = []

        i = 0
        while i < len(parts):
            token = parts[i]
            if token in {"--depth", "--max-depth", "-d"}:
                if i + 1 >= len(parts):
                    await import_cmd.finish(_to_platform_message(bot, event, format_error("缺少 --depth 参数值")))
                    return
                value = parts[i + 1]
                if not value.isdigit():
                    await import_cmd.finish(_to_platform_message(bot, event, format_error("--depth 必须是非负整数")))
                    return
                depth = max(0, int(value))
                i += 2
                continue
            if token in {"--select", "-s"}:
                if i + 1 >= len(parts):
                    await import_cmd.finish(_to_platform_message(bot, event, format_error("缺少 --select 参数值")))
                    return
                selection = parts[i + 1]
                i += 2
                continue
            paths.append(Path(token))
            i += 1

        if not paths:
            paths = _default_scan_roots()

        if not paths:
            await import_cmd.finish(
                _to_platform_message(bot, event, format_error("请提供扫描路径：/dst room import --select all <路径>"))
            )
            return

        if not selection:
            await import_cmd.finish(
                _to_platform_message(
                    bot,
                    event,
                    format_error("用法：/dst room import --select <all|1,2|1-3> [--depth N] <路径...>"),
                )
            )
            return

        clusters = await asyncio.to_thread(discover_dst_clusters, paths, max_depth=depth)
        if not clusters:
            await import_cmd.finish(_to_platform_message(bot, event, format_info("未发现任何可导入的集群")))
            return

        chosen, sel_error = _parse_selection(selection, len(clusters))
        if sel_error:
            await import_cmd.finish(_to_platform_message(bot, event, format_error(sel_error)))
            return

        selected_clusters = [clusters[i - 1] for i in chosen or []]
        incoming_entries: List[ClusterConfigEntry] = []
        for item in selected_clusters:
            incoming_entries.append(
                ClusterConfigEntry(
                    path=str(normalize_path(item.path)),
                    name=item.display_name,
                    token=item.token,
                    worlds=item.worlds,
                )
            )

        existing, warning = load_cluster_config()
        if warning:
            await import_cmd.send(_to_platform_message(bot, event, format_info(f"⚠️ {warning}")))

        merged, imported, skipped = merge_cluster_entries(existing, incoming_entries)
        err = save_cluster_config(merged)
        if err:
            await import_cmd.finish(_to_platform_message(bot, event, format_error(err)))
            return

        cfg_path = get_cluster_config_path()
        await import_cmd.finish(
            _to_platform_message(
                bot,
                event,
                format_success(
                    f"已导入 {imported} 个集群，跳过 {skipped} 个（重复或无效）\n配置文件：{cfg_path}"
                ),
            )
        )


__all__ = ["init"]
