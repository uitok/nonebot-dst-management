"""
Cluster config store (Phase C Auto Discovery).

Persist discovered DST clusters into a small JSON file so users can import
rooms into "plugin config" without hand-editing files.

Default location:
  data/dst_clusters.json

Override via env:
  DST_CLUSTER_CONFIG_PATH=/path/to/dst_clusters.json
"""

from __future__ import annotations

import json
import os
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


DEFAULT_CLUSTER_CONFIG_PATH = "data/dst_clusters.json"

_config_path_override: Optional[Path] = None


def set_cluster_config_path(path: str | Path) -> None:
    """Override config path (mainly for tests)."""

    global _config_path_override
    _config_path_override = Path(path)


def get_cluster_config_path() -> Path:
    """Get config path, preferring env override."""

    if (env_path := os.getenv("DST_CLUSTER_CONFIG_PATH")):
        return Path(env_path)
    if _config_path_override is not None:
        return _config_path_override
    return Path(DEFAULT_CLUSTER_CONFIG_PATH)


@dataclass
class ClusterConfigEntry:
    """A persisted cluster entry."""

    path: str
    name: Optional[str] = None
    token: Optional[str] = None
    worlds: List[str] = field(default_factory=list)
    imported_at: Optional[str] = None

    def normalized_key(self) -> str:
        # Use path as the stable identity.
        return (self.path or "").rstrip("/")


def _now_iso() -> str:
    # ISO-ish without requiring timezone libs; stable and human-friendly.
    return time.strftime("%Y-%m-%dT%H:%M:%S", time.localtime())


def load_cluster_config() -> Tuple[List[ClusterConfigEntry], Optional[str]]:
    """Load config entries from disk.

    Returns:
        (entries, warning) where warning is a user-facing string if the config
        file was unreadable/corrupted.
    """

    path = get_cluster_config_path()
    if not path.exists():
        return [], None
    try:
        raw = path.read_text(encoding="utf-8")
    except OSError as exc:
        return [], f"读取配置失败：{exc}"

    try:
        data = json.loads(raw) if raw.strip() else {}
    except json.JSONDecodeError:
        # Back up broken config and continue with empty.
        try:
            backup = path.with_suffix(path.suffix + f".broken.{int(time.time())}")
            backup.parent.mkdir(parents=True, exist_ok=True)
            backup.write_text(raw, encoding="utf-8")
        except OSError:
            pass
        return [], "配置文件损坏，已忽略（并尝试备份 broken 文件）"

    clusters = data.get("clusters") if isinstance(data, dict) else None
    if not isinstance(clusters, list):
        return [], None

    entries: List[ClusterConfigEntry] = []
    for item in clusters:
        if not isinstance(item, dict):
            continue
        path_val = item.get("path")
        if not isinstance(path_val, str) or not path_val.strip():
            continue
        entry = ClusterConfigEntry(
            path=path_val.strip(),
            name=str(item.get("name")).strip() if item.get("name") else None,
            token=str(item.get("token")).strip() if item.get("token") else None,
            worlds=[str(x) for x in (item.get("worlds") or []) if str(x).strip()],
            imported_at=str(item.get("imported_at")).strip() if item.get("imported_at") else None,
        )
        entries.append(entry)

    return entries, None


def save_cluster_config(entries: List[ClusterConfigEntry]) -> Optional[str]:
    """Save config entries to disk. Returns error message on failure."""

    path = get_cluster_config_path()
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        payload: Dict[str, Any] = {
            "version": 1,
            "clusters": [asdict(entry) for entry in entries],
        }
        tmp_path = path.with_suffix(path.suffix + ".tmp")
        tmp_path.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True),
            encoding="utf-8",
        )
        tmp_path.replace(path)
        return None
    except OSError as exc:
        return f"保存配置失败：{exc}"


def merge_cluster_entries(
    existing: List[ClusterConfigEntry],
    incoming: List[ClusterConfigEntry],
) -> Tuple[List[ClusterConfigEntry], int, int]:
    """Merge incoming clusters into existing list (dedupe by path).

    Returns:
        (merged_entries, imported_count, skipped_count)
    """

    index: Dict[str, ClusterConfigEntry] = {e.normalized_key(): e for e in existing}

    imported = 0
    skipped = 0
    for entry in incoming:
        key = entry.normalized_key()
        if not key:
            skipped += 1
            continue
        if key in index:
            # Update missing metadata (best-effort) without breaking existing settings.
            cur = index[key]
            updated = False
            if not cur.name and entry.name:
                cur.name = entry.name
                updated = True
            if not cur.token and entry.token:
                cur.token = entry.token
                updated = True
            if not cur.worlds and entry.worlds:
                cur.worlds = entry.worlds
                updated = True
            if updated and not cur.imported_at:
                cur.imported_at = cur.imported_at or _now_iso()
            skipped += 1
            continue

        if not entry.imported_at:
            entry.imported_at = _now_iso()
        existing.append(entry)
        index[key] = entry
        imported += 1

    existing.sort(key=lambda e: e.path)
    return existing, imported, skipped


__all__ = [
    "DEFAULT_CLUSTER_CONFIG_PATH",
    "ClusterConfigEntry",
    "set_cluster_config_path",
    "get_cluster_config_path",
    "load_cluster_config",
    "save_cluster_config",
    "merge_cluster_entries",
]

