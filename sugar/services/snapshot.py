"""Persistent snapshot store for Sugar data.

Sugar contracts only serve real-time state, so every fetch that isn't
recorded is lost. SnapshotStore writes each fetched DataFrame to disk,
stamped with the chain and block number, and keeps a manifest so past
snapshots can be listed and reloaded later.

Layout on disk::

    <base_dir>/
        <chain>/
            <dataset>/
                manifest.jsonl          # one JSON line per snapshot
                <block>.parquet         # or <block>.csv.gz without pyarrow

Example:
    >>> store = SnapshotStore("sugar-snapshots")
    >>> store.save(pools_df, dataset="pools", chain="base", block=31000000)
    >>> store.history("pools", "base")          # manifest as a DataFrame
    >>> old = store.load("pools", "base")       # latest snapshot
    >>> old = store.load("pools", "base", block=30950000)
"""

from __future__ import annotations

import json
import logging
import os
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

logger = logging.getLogger(__name__)

#: Environment variable that overrides the default snapshot directory.
SNAPSHOT_DIR_ENV = "SUGAR_SNAPSHOT_DIR"

#: Default directory (relative to the working directory) for snapshots.
DEFAULT_SNAPSHOT_DIR = "sugar-snapshots"


def _parquet_available() -> bool:
    """Check whether a parquet engine (pyarrow/fastparquet) is installed."""
    try:
        import pyarrow  # noqa: F401

        return True
    except ImportError:
        pass
    try:
        import fastparquet  # noqa: F401

        return True
    except ImportError:
        return False


class SnapshotStore:
    """
    Disk-backed store that indexes fetched Sugar data for posterity.

    Each snapshot is a DataFrame written under ``<chain>/<dataset>/`` and
    named by block number, with an append-only ``manifest.jsonl`` recording
    block, fetch time, row count, and file name.
    """

    def __init__(self, base_dir: str | Path | None = None) -> None:
        """
        Initialize the snapshot store.

        Args:
            base_dir: Root directory for snapshots. Defaults to the
                ``SUGAR_SNAPSHOT_DIR`` environment variable, falling back
                to ``./sugar-snapshots``.
        """
        if base_dir is None:
            base_dir = os.environ.get(SNAPSHOT_DIR_ENV, DEFAULT_SNAPSHOT_DIR)
        self._base_dir = Path(base_dir)
        self._use_parquet = _parquet_available()

    @property
    def base_dir(self) -> Path:
        """Root directory for snapshots."""
        return self._base_dir

    def _dataset_dir(self, dataset: str, chain: str) -> Path:
        return self._base_dir / chain.lower() / dataset

    def _manifest_path(self, dataset: str, chain: str) -> Path:
        return self._dataset_dir(dataset, chain) / "manifest.jsonl"

    def save(
        self,
        df: pd.DataFrame,
        dataset: str,
        chain: str,
        block: int,
    ) -> Path | None:
        """
        Persist a DataFrame snapshot.

        Re-saving the same (dataset, chain, block) overwrites the data file
        but does not duplicate the manifest entry.

        Args:
            df: DataFrame to persist.
            dataset: Logical dataset name (e.g. "pools", "tokens").
            chain: Chain name (e.g. "base", "optimism").
            block: Block number the data was fetched at.

        Returns:
            Path to the written snapshot file, or None if df is empty.
        """
        if df.empty:
            logger.debug(f"Skipping snapshot of empty {dataset} ({chain})")
            return None

        out_dir = self._dataset_dir(dataset, chain)
        out_dir.mkdir(parents=True, exist_ok=True)

        if self._use_parquet:
            path = out_dir / f"{block}.parquet"
            try:
                df.to_parquet(path)
            except (ValueError, TypeError, ImportError):
                # Mixed-type object columns (e.g. Decimal, nested lists) can
                # be unserializable for parquet; fall back to CSV for this df.
                path = out_dir / f"{block}.csv.gz"
                df.to_csv(path, compression="gzip")
        else:
            path = out_dir / f"{block}.csv.gz"
            df.to_csv(path, compression="gzip")

        manifest = self._manifest_path(dataset, chain)
        already_recorded = block in set(self._read_manifest(manifest)["block"]) if manifest.exists() else False
        if not already_recorded:
            entry = {
                "block": block,
                "fetched_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                "rows": len(df),
                "file": path.name,
            }
            with open(manifest, "a") as f:
                f.write(json.dumps(entry) + "\n")

        logger.info(f"Snapshot saved: {path} ({len(df)} rows)")
        return path

    def _read_manifest(self, manifest: Path) -> pd.DataFrame:
        if not manifest.exists():
            return pd.DataFrame(columns=["block", "fetched_at", "rows", "file"])
        records = [json.loads(line) for line in manifest.read_text().splitlines() if line.strip()]
        return pd.DataFrame(records)

    def history(self, dataset: str, chain: str) -> pd.DataFrame:
        """
        List all recorded snapshots for a dataset/chain.

        Args:
            dataset: Logical dataset name.
            chain: Chain name.

        Returns:
            DataFrame with columns block, fetched_at, rows, file
            (empty if no snapshots exist).
        """
        return self._read_manifest(self._manifest_path(dataset, chain))

    def latest_block(self, dataset: str, chain: str) -> int | None:
        """Return the highest snapshotted block, or None if none exist."""
        hist = self.history(dataset, chain)
        if hist.empty:
            return None
        return int(hist["block"].max())

    def load(
        self,
        dataset: str,
        chain: str,
        block: int | None = None,
    ) -> pd.DataFrame:
        """
        Load a snapshot from disk.

        Args:
            dataset: Logical dataset name.
            chain: Chain name.
            block: Specific block to load. Defaults to the latest snapshot.

        Returns:
            The snapshotted DataFrame.

        Raises:
            FileNotFoundError: If no matching snapshot exists.
        """
        hist = self.history(dataset, chain)
        if hist.empty:
            raise FileNotFoundError(
                f"No snapshots for dataset={dataset!r} chain={chain!r} "
                f"under {self._base_dir}"
            )
        if block is None:
            row = hist.loc[hist["block"].idxmax()]
        else:
            match = hist[hist["block"] == block]
            if match.empty:
                raise FileNotFoundError(
                    f"No snapshot at block {block} for dataset={dataset!r} "
                    f"chain={chain!r} (available: {sorted(hist['block'])})"
                )
            row = match.iloc[0]

        path = self._dataset_dir(dataset, chain) / str(row["file"])
        if path.suffix == ".parquet":
            return pd.read_parquet(path)
        return pd.read_csv(path, index_col=0, compression="gzip")

    def datasets(self, chain: str | None = None) -> list[tuple[str, str]]:
        """
        Enumerate stored (chain, dataset) pairs.

        Args:
            chain: Optionally restrict to one chain.

        Returns:
            Sorted list of (chain, dataset) tuples present on disk.
        """
        if not self._base_dir.exists():
            return []
        pairs = []
        chains = [self._base_dir / chain.lower()] if chain else sorted(self._base_dir.iterdir())
        for chain_dir in chains:
            if not chain_dir.is_dir():
                continue
            for ds_dir in sorted(chain_dir.iterdir()):
                if ds_dir.is_dir() and (ds_dir / "manifest.jsonl").exists():
                    pairs.append((chain_dir.name, ds_dir.name))
        return pairs
