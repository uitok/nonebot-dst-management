"""
自动发现命令 (on_alconna 版本)

使用 nonebot-plugin-alconna 的 on_alconna 匹配器。

Phase C (Auto): DST cluster auto discovery and import.

Commands:
- /dst room scan [--depth N] [path...]
  Scan directories to find DST clusters (directories containing cluster.ini).

- /dst room import --select <all|1,2|1-3> [--depth N] [path...]
  Scan and import selected clusters into plugin config (data/dst_clusters.json).
"""

from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Any, List, Optional, Tuple

from arclet.alconna import Alconna, Args, CommandMeta
from nonebot.internal.adapter import Event

from nonebot_plugin_alconna import Match, AlconnaMatch, on_alconna

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
from ..utils.permission import ADMIN_PERMISSION


# ========== 辅助函数 ==========

def _default_scan_roots() -> List[Path]:
    """默认扫描根路径"""
    # Common DST dedicated server save location on Linux.
    candidate = Path("~/.klei/DoNotStarveTogether").expanduser()
    if candidate.is_dir():
        return [candidate]
    return []


def _parse_selection(selection: str, max_index: int) -> Tuple[Optional[List[int]], Optional[str]]:
    """解析选择参数（支持 all, 1,2, 1-3 等格式）"""
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
) -> str:
    """渲染扫描结果"""
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
    roots_text = ", ".join(str(normalize_path(p)) for p in roots)
    text = "\n".join(
        [
            f"{ICON_INFO} 自动发现结果",
            f"- 扫描路径：{roots_text}",
            f"- 深度：{depth}",
            f"- 发现：{count} 个集群",
            "",
            str(table_obj),
            "",
            f"{ICON_TIP} 导入：/dst room import --select all <同样的路径>",
            f"{ICON_TIP} 导入部分：/dst room import --select 1,3-5 <同样的路径>",
        ]
    ).strip()
    return text


# ========== 命令定义 + on_alconna 匹配器 ==========

# 注意：Alconna 的 Args 对于可变参数和可选标志的处理有限制
# 这里使用简化版本，路径参数通过字符串处理

scan_command = Alconna(
    "dst room scan",
    Args["paths", str, ""]["depth", int, 4],
    meta=CommandMeta(
        description="扫描 DST 集群目录",
        usage="/dst room scan [路径...]",
        example="/dst room scan ~/.klei/DoNotStarveTogether",
    ),
)

import_command = Alconna(
    "dst room import",
    Args["select", str]["paths", str, ""]["depth", int, 4],
    meta=CommandMeta(
        description="导入扫描到的 DST 集群",
        usage="/dst room import --select <all|1,2|1-3> [路径...]",
        example="/dst room import --select all ~/.klei/DoNotStarveTogether",
    ),
)

# ========== on_alconna 匹配器 ==========

scan_matcher = on_alconna(scan_command, permission=ADMIN_PERMISSION, priority=5, block=True)
import_matcher = on_alconna(import_command, permission=ADMIN_PERMISSION, priority=5, block=True)


# ========== 命令处理函数 ==========

def _split_paths(text: Optional[str]) -> List[Path]:
    """从文本中解析路径"""
    if not text:
        return []
    import shlex
    try:
        parts = shlex.split(text or "")
    except ValueError:
        parts = (text or "").split()
    return [Path(p) for p in parts if p.strip()]


@scan_matcher.handle()
async def handle_scan(
    event: Event,
    paths: Match[str] = AlconnaMatch("paths"),
    depth: Match[int] = AlconnaMatch("depth"),
) -> None:
    """处理扫描命令"""
    depth_val = depth.result if depth.available else 4
    roots = _split_paths(paths.result if paths.available else None)

    if not roots:
        roots = _default_scan_roots()

    if not roots:
        await scan_matcher.finish(format_error("请提供扫描路径：/dst room scan <路径>（或将存档放在 ~/.klei/DoNotStarveTogether）"))
        return

    clusters = await asyncio.to_thread(discover_dst_clusters, roots, max_depth=depth_val)

    # 获取 bot 和 event 用于渲染
    bot = getattr(event, "bot", None)
    message = await _render_scan_result(
        bot=bot,
        event=event,
        roots=roots,
        depth=depth_val,
        clusters=clusters,
    )
    await scan_matcher.finish(message)


@import_matcher.handle()
async def handle_import(
    event: Event,
    select: Match[str] = AlconnaMatch("select"),
    paths: Match[str] = AlconnaMatch("paths"),
    depth: Match[int] = AlconnaMatch("depth"),
) -> None:
    """处理导入命令"""
    if not select.available:
        await import_matcher.finish(format_error("用法：/dst room import --select <all|1,2|1-3> [--depth N] <路径...>"))
        return

    depth_val = depth.result if depth.available else 4
    roots = _split_paths(paths.result if paths.available else None)

    if not roots:
        roots = _default_scan_roots()

    if not roots:
        await import_matcher.finish(format_error("请提供扫描路径：/dst room import --select all <路径>"))
        return

    clusters = await asyncio.to_thread(discover_dst_clusters, roots, max_depth=depth_val)
    if not clusters:
        await import_matcher.finish(format_info("未发现任何可导入的集群"))
        return

    chosen, sel_error = _parse_selection(select.result, len(clusters))
    if sel_error:
        await import_matcher.finish(format_error(sel_error))
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
        await import_matcher.send(format_info(f"⚠️ {warning}"))

    merged, imported, skipped = merge_cluster_entries(existing, incoming_entries)
    err = save_cluster_config(merged)
    if err:
        await import_matcher.finish(format_error(err))
        return

    cfg_path = get_cluster_config_path()
    await import_matcher.finish(
        format_success(
            f"已导入 {imported} 个集群，跳过 {skipped} 个（重复或无效）\n配置文件：{cfg_path}"
        )
    )


def init() -> None:
    """初始化自动发现命令（无需 API 客户端）"""
    pass


__all__ = [
    "scan_command",
    "import_command",
    "scan_matcher",
    "import_matcher",
    "handle_scan",
    "handle_import",
    "init",
]
