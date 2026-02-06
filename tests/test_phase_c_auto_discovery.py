from __future__ import annotations

from pathlib import Path

import pytest

from nonebot_plugin_dst_management.services import cluster_store
from nonebot_plugin_dst_management.utils.path import (
    discover_dst_clusters,
    parse_cluster_ini_file,
)


def _write_cluster_ini(path: Path, name: str) -> None:
    path.write_text(
        "\n".join(
            [
                "[NETWORK]",
                f"cluster_name = {name}",
                "cluster_description = hello",
                "",
            ]
        ),
        encoding="utf-8",
    )


def test_parse_cluster_ini_extracts_cluster_name(tmp_path: Path) -> None:
    ini = tmp_path / "cluster.ini"
    _write_cluster_ini(ini, "My Room")
    name, warnings = parse_cluster_ini_file(ini)
    assert name == "My Room"
    assert warnings == []


def test_discover_dst_clusters_finds_cluster_and_worlds(tmp_path: Path) -> None:
    root = tmp_path / "DoNotStarveTogether"
    root.mkdir()

    cluster1 = root / "Cluster_1"
    cluster1.mkdir()
    _write_cluster_ini(cluster1 / "cluster.ini", "Cluster One")

    (cluster1 / "Master").mkdir()
    (cluster1 / "Master" / "server.ini").write_text("", encoding="utf-8")
    (cluster1 / "Caves").mkdir()
    # Missing Caves/server.ini should be reflected in metadata (but still discovered).

    clusters = discover_dst_clusters([root], max_depth=2)
    assert len(clusters) == 1
    assert clusters[0].display_name == "Cluster One"
    assert clusters[0].worlds == ["Master", "Caves"]
    assert clusters[0].world_server_ini["Master"] is True
    assert clusters[0].world_server_ini["Caves"] is False


def test_discover_dst_clusters_stops_descending_when_cluster_found(tmp_path: Path) -> None:
    root = tmp_path / "DoNotStarveTogether"
    root.mkdir()

    cluster1 = root / "Cluster_1"
    cluster1.mkdir()
    _write_cluster_ini(cluster1 / "cluster.ini", "Cluster One")

    nested = cluster1 / "nested"
    nested.mkdir()
    _write_cluster_ini(nested / "cluster.ini", "Nested Cluster")

    clusters = discover_dst_clusters([root], max_depth=5)
    # Only the top cluster should be found; once a cluster directory is detected, we don't descend into it.
    assert [c.display_name for c in clusters] == ["Cluster One"]


def test_cluster_store_save_load_and_merge(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    cfg_path = tmp_path / "clusters.json"
    monkeypatch.setenv("DST_CLUSTER_CONFIG_PATH", str(cfg_path))

    entries = [
        cluster_store.ClusterConfigEntry(
            path="/a/b/Cluster_1",
            name="Room 1",
            token="t",
            worlds=["Master"],
        )
    ]

    err = cluster_store.save_cluster_config(entries)
    assert err is None

    loaded, warning = cluster_store.load_cluster_config()
    assert warning is None
    assert len(loaded) == 1
    assert loaded[0].path == "/a/b/Cluster_1"
    assert loaded[0].name == "Room 1"

    merged, imported, skipped = cluster_store.merge_cluster_entries(
        loaded,
        [
            # Duplicate path should be skipped but can enrich metadata.
            cluster_store.ClusterConfigEntry(path="/a/b/Cluster_1", name=""),
            # New cluster should be imported.
            cluster_store.ClusterConfigEntry(path="/a/b/Cluster_2", name="Room 2"),
        ],
    )
    assert imported == 1
    assert skipped == 1
    assert len(merged) == 2


def test_cluster_store_handles_broken_json(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    cfg_path = tmp_path / "clusters.json"
    monkeypatch.setenv("DST_CLUSTER_CONFIG_PATH", str(cfg_path))

    cfg_path.parent.mkdir(parents=True, exist_ok=True)
    cfg_path.write_text("{not json", encoding="utf-8")

    loaded, warning = cluster_store.load_cluster_config()
    assert loaded == []
    assert warning is not None

    # A backup should be attempted.
    backups = list(cfg_path.parent.glob("clusters.json.broken.*"))
    assert backups
