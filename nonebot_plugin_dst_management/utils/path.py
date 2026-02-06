"""
Path utilities (Phase C Auto Discovery).

This module provides a robust directory scanner to discover DST clusters on the
local filesystem. A DST cluster is identified by the presence of `cluster.ini`
in a directory.

Design goals:
- Robustness: never crash on invalid / unreadable files or permission errors.
- Performance: stop descending into a directory once a cluster is found (to
  avoid scanning large save folders under Master/Caves).
- Safety: do not follow symlinks by default; limit recursion depth.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence, Tuple


DEFAULT_EXCLUDED_DIR_NAMES: frozenset[str] = frozenset(
    {
        ".git",
        ".hg",
        ".svn",
        "__pycache__",
        "node_modules",
        ".venv",
        "venv",
        "env",
        "dist",
        "build",
        # DST world folders can be huge if a user starts scanning from the wrong root.
        "save",
        "backup",
        "backups",
        "logs",
        "log",
    }
)


@dataclass(frozen=True)
class DiscoveredCluster:
    """A discovered DST cluster (directory containing cluster.ini)."""

    path: Path
    cluster_name: Optional[str] = None
    token: Optional[str] = None
    worlds: List[str] = field(default_factory=list)
    world_server_ini: Dict[str, bool] = field(default_factory=dict)
    warnings: List[str] = field(default_factory=list)

    @property
    def display_name(self) -> str:
        value = (self.cluster_name or "").strip()
        return value or self.path.name

    @property
    def worlds_label(self) -> str:
        return "+".join(self.worlds) if self.worlds else "-"

    @property
    def server_ini_label(self) -> str:
        if not self.worlds:
            return "-"
        parts: list[str] = []
        for world in self.worlds:
            ok = self.world_server_ini.get(world)
            if ok is True:
                parts.append(f"{world}:Y")
            elif ok is False:
                parts.append(f"{world}:N")
            else:
                parts.append(f"{world}:?")
        return " ".join(parts)


def normalize_path(path: str | Path) -> Path:
    """Best-effort normalize a path without requiring it to exist."""

    p = Path(path).expanduser()
    try:
        return p.resolve(strict=False)
    except Exception:
        # Fallback when running on older filesystems / edge cases.
        try:
            return p.absolute()
        except Exception:
            return p


def parse_dst_ini(content: str) -> Dict[str, str]:
    """Parse a DST-style ini file content into a flat key-value dict.

    DST ini files contain section headers like [NETWORK] which are ignored.
    This parser is intentionally forgiving.
    """

    data: Dict[str, str] = {}
    for raw_line in (content or "").splitlines():
        line = raw_line.strip()
        if not line:
            continue
        if line.startswith("#") or line.startswith(";"):
            continue
        if line.startswith("[") and line.endswith("]"):
            continue
        if "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip().lower()
        value = value.strip()
        if not key:
            continue
        data[key] = value
    return data


def parse_cluster_ini_file(path: Path) -> Tuple[Optional[str], List[str]]:
    """Parse `cluster.ini` and return (cluster_name, warnings)."""

    warnings: List[str] = []
    try:
        # `cluster.ini` is small; still guard against weirdly large files.
        raw = path.read_bytes()
        if len(raw) > 512 * 1024:
            raw = raw[: 512 * 1024]
            warnings.append("cluster.ini 文件过大，已截断解析")
        text = raw.decode("utf-8-sig", errors="replace")
    except FileNotFoundError:
        return None, ["cluster.ini 不存在"]
    except PermissionError:
        return None, ["无权限读取 cluster.ini"]
    except OSError as exc:
        return None, [f"读取 cluster.ini 失败：{exc}"]

    data = parse_dst_ini(text)
    name = (data.get("cluster_name") or "").strip()
    if not name:
        return None, warnings
    return name, warnings


def read_cluster_token_file(path: Path) -> Tuple[Optional[str], List[str]]:
    """Read `cluster_token.txt` (first non-empty line)."""

    warnings: List[str] = []
    if not path.exists():
        return None, warnings
    if not path.is_file():
        return None, ["cluster_token.txt 不是文件"]
    try:
        raw = path.read_bytes()
        if len(raw) > 64 * 1024:
            raw = raw[: 64 * 1024]
            warnings.append("cluster_token.txt 文件过大，已截断读取")
        text = raw.decode("utf-8-sig", errors="replace")
    except PermissionError:
        return None, ["无权限读取 cluster_token.txt"]
    except OSError as exc:
        return None, [f"读取 cluster_token.txt 失败：{exc}"]

    token: Optional[str] = None
    for line in text.splitlines():
        val = line.strip()
        if val:
            token = val
            break
    return token, warnings


def detect_worlds(cluster_dir: Path) -> Tuple[List[str], Dict[str, bool]]:
    """Detect Master/Caves worlds and whether server.ini exists."""

    worlds: List[str] = []
    server_ini: Dict[str, bool] = {}
    for world in ("Master", "Caves"):
        world_dir = cluster_dir / world
        if world_dir.is_dir():
            worlds.append(world)
            server_ini[world] = (world_dir / "server.ini").is_file()
    return worlds, server_ini


def discover_dst_clusters(
    roots: Sequence[str | Path],
    *,
    max_depth: int = 4,
    excluded_dir_names: Iterable[str] = DEFAULT_EXCLUDED_DIR_NAMES,
    follow_symlinks: bool = False,
) -> List[DiscoveredCluster]:
    """Discover DST clusters under the given roots.

    Args:
        roots: Base directories to scan.
        max_depth: Maximum recursion depth (0 means only check root itself).
        excluded_dir_names: Directory names to skip.
        follow_symlinks: Whether to follow symlinks when descending.
    """

    if max_depth < 0:
        max_depth = 0

    excludes = set(excluded_dir_names or [])

    found: List[DiscoveredCluster] = []
    seen: set[str] = set()

    def add_cluster(cluster_dir: Path) -> None:
        key = str(normalize_path(cluster_dir))
        if key in seen:
            return
        seen.add(key)

        cluster_ini = cluster_dir / "cluster.ini"
        token_path = cluster_dir / "cluster_token.txt"

        name, name_warnings = parse_cluster_ini_file(cluster_ini)
        token, token_warnings = read_cluster_token_file(token_path)
        worlds, server_ini = detect_worlds(cluster_dir)

        warnings: List[str] = []
        warnings.extend(name_warnings)
        warnings.extend(token_warnings)

        found.append(
            DiscoveredCluster(
                path=cluster_dir,
                cluster_name=name,
                token=token,
                worlds=worlds,
                world_server_ini=server_ini,
                warnings=warnings,
            )
        )

    for root in roots:
        root_path = normalize_path(root)
        if not root_path.exists():
            continue
        if not root_path.is_dir():
            continue

        stack: List[Tuple[Path, int]] = [(root_path, 0)]
        visited_dirs: set[str] = set()

        while stack:
            current, depth = stack.pop()
            current_key = str(normalize_path(current))
            if current_key in visited_dirs:
                continue
            visited_dirs.add(current_key)

            # Cluster root detection.
            try:
                if (current / "cluster.ini").is_file():
                    add_cluster(current)
                    # Do not descend further into cluster directory.
                    continue
            except OSError:
                # Permission errors etc; treat as not a cluster and don't crash.
                continue

            if depth >= max_depth:
                continue

            try:
                with os.scandir(current) as it:
                    for entry in it:
                        try:
                            if not entry.is_dir(follow_symlinks=follow_symlinks):
                                continue
                        except OSError:
                            continue

                        name = entry.name
                        if name in excludes:
                            continue

                        stack.append((Path(entry.path), depth + 1))
            except (FileNotFoundError, NotADirectoryError):
                continue
            except PermissionError:
                continue
            except OSError:
                continue

    found.sort(key=lambda item: str(item.path))
    return found


__all__ = [
    "DiscoveredCluster",
    "DEFAULT_EXCLUDED_DIR_NAMES",
    "normalize_path",
    "parse_dst_ini",
    "parse_cluster_ini_file",
    "read_cluster_token_file",
    "detect_worlds",
    "discover_dst_clusters",
]

