"""Tests for the persistent snapshot store."""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

from sugar.services.snapshot import (
    DEFAULT_SNAPSHOT_DIR,
    SNAPSHOT_DIR_ENV,
    SnapshotStore,
)


@pytest.fixture
def store(tmp_path: Path) -> SnapshotStore:
    """Create a store rooted in a temp directory."""
    return SnapshotStore(tmp_path / "snaps")


@pytest.fixture
def sample_df() -> pd.DataFrame:
    """Small DataFrame to snapshot."""
    return pd.DataFrame(
        {"lp": ["0xabc", "0xdef"], "tvl": [1.5, 2.5]},
    ).set_index("lp")


class TestSnapshotStoreInit:
    """Test store construction and directory resolution."""

    def test_explicit_dir(self, tmp_path: Path) -> None:
        """Should use the directory passed in."""
        store = SnapshotStore(tmp_path / "x")
        assert store.base_dir == tmp_path / "x"

    def test_env_var_default(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Should fall back to SUGAR_SNAPSHOT_DIR."""
        monkeypatch.setenv(SNAPSHOT_DIR_ENV, str(tmp_path / "from-env"))
        store = SnapshotStore()
        assert store.base_dir == tmp_path / "from-env"

    def test_hardcoded_default(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Should fall back to ./sugar-snapshots without env var."""
        monkeypatch.delenv(SNAPSHOT_DIR_ENV, raising=False)
        store = SnapshotStore()
        assert store.base_dir == Path(DEFAULT_SNAPSHOT_DIR)


class TestSnapshotSaveLoad:
    """Test the save → history → load round trip."""

    def test_save_creates_file_and_manifest(
        self, store: SnapshotStore, sample_df: pd.DataFrame
    ) -> None:
        """Save should write a data file plus a manifest entry."""
        path = store.save(sample_df, dataset="pools", chain="base", block=100)

        assert path is not None and path.exists()
        hist = store.history("pools", "base")
        assert len(hist) == 1
        assert hist.iloc[0]["block"] == 100
        assert hist.iloc[0]["rows"] == 2

    def test_empty_df_skipped(self, store: SnapshotStore) -> None:
        """Empty DataFrames should not be written."""
        assert store.save(pd.DataFrame(), "pools", "base", 100) is None
        assert store.history("pools", "base").empty

    def test_round_trip_latest(
        self, store: SnapshotStore, sample_df: pd.DataFrame
    ) -> None:
        """Load without block should return the latest snapshot."""
        store.save(sample_df, "pools", "base", 100)
        newer = sample_df.copy()
        newer["tvl"] = [9.0, 9.0]
        store.save(newer, "pools", "base", 200)

        loaded = store.load("pools", "base")
        assert list(loaded["tvl"]) == [9.0, 9.0]
        assert store.latest_block("pools", "base") == 200

    def test_round_trip_specific_block(
        self, store: SnapshotStore, sample_df: pd.DataFrame
    ) -> None:
        """Load with block should return that exact snapshot."""
        store.save(sample_df, "pools", "base", 100)
        store.save(sample_df.assign(tvl=0.0), "pools", "base", 200)

        loaded = store.load("pools", "base", block=100)
        assert list(loaded["tvl"]) == [1.5, 2.5]

    def test_resave_same_block_no_duplicate_manifest(
        self, store: SnapshotStore, sample_df: pd.DataFrame
    ) -> None:
        """Re-saving the same block should not duplicate manifest rows."""
        store.save(sample_df, "pools", "base", 100)
        store.save(sample_df, "pools", "base", 100)
        assert len(store.history("pools", "base")) == 1

    def test_load_missing_raises(self, store: SnapshotStore) -> None:
        """Loading a nonexistent snapshot should raise FileNotFoundError."""
        with pytest.raises(FileNotFoundError):
            store.load("pools", "base")

    def test_load_missing_block_raises(
        self, store: SnapshotStore, sample_df: pd.DataFrame
    ) -> None:
        """Loading a block that was never saved should raise."""
        store.save(sample_df, "pools", "base", 100)
        with pytest.raises(FileNotFoundError):
            store.load("pools", "base", block=999)


class TestSnapshotEnumeration:
    """Test dataset discovery."""

    def test_datasets_listing(
        self, store: SnapshotStore, sample_df: pd.DataFrame
    ) -> None:
        """Should enumerate (chain, dataset) pairs on disk."""
        store.save(sample_df, "pools", "base", 100)
        store.save(sample_df, "tokens", "base", 100)
        store.save(sample_df, "pools", "optimism", 50)

        assert store.datasets() == [
            ("base", "pools"),
            ("base", "tokens"),
            ("optimism", "pools"),
        ]
        assert store.datasets(chain="base") == [
            ("base", "pools"),
            ("base", "tokens"),
        ]

    def test_datasets_empty(self, store: SnapshotStore) -> None:
        """Should return empty list when nothing saved."""
        assert store.datasets() == []
