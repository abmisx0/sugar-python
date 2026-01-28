"""Export service for Sugar Python library."""

from __future__ import annotations

import logging
from pathlib import Path

import pandas as pd

logger = logging.getLogger(__name__)


class ExportService:
    """
    Service for exporting DataFrames to various formats.

    Handles directory creation and file naming conventions.
    """

    def __init__(self, base_dir: str | Path = ".") -> None:
        """
        Initialize export service.

        Args:
            base_dir: Base directory for exports.
        """
        self._base_dir = Path(base_dir)

    def to_csv(
        self,
        df: pd.DataFrame,
        filename: str,
        subdirectory: str | None = None,
        index: bool = True,
    ) -> Path:
        """
        Export DataFrame to CSV.

        Args:
            df: DataFrame to export.
            filename: Output filename.
            subdirectory: Optional subdirectory within base_dir.
            index: Whether to include index in output.

        Returns:
            Path to exported file.
        """
        if subdirectory:
            output_dir = self._base_dir / subdirectory
        else:
            output_dir = self._base_dir

        output_dir.mkdir(parents=True, exist_ok=True)
        output_path = output_dir / filename

        df.to_csv(output_path, index=index)
        logger.info(f"Exported {len(df)} rows to {output_path}")

        return output_path

    def to_json(
        self,
        df: pd.DataFrame,
        filename: str,
        subdirectory: str | None = None,
        orient: str = "records",
    ) -> Path:
        """
        Export DataFrame to JSON.

        Args:
            df: DataFrame to export.
            filename: Output filename.
            subdirectory: Optional subdirectory within base_dir.
            orient: JSON orientation (records, index, columns, etc.).

        Returns:
            Path to exported file.
        """
        if subdirectory:
            output_dir = self._base_dir / subdirectory
        else:
            output_dir = self._base_dir

        output_dir.mkdir(parents=True, exist_ok=True)
        output_path = output_dir / filename

        df.to_json(output_path, orient=orient, indent=2)
        logger.info(f"Exported {len(df)} rows to {output_path}")

        return output_path

    def save_raw(
        self,
        data: str,
        filename: str,
        subdirectory: str | None = None,
    ) -> Path:
        """
        Save raw data string to file.

        Args:
            data: Raw data string.
            filename: Output filename.
            subdirectory: Optional subdirectory within base_dir.

        Returns:
            Path to saved file.
        """
        if subdirectory:
            output_dir = self._base_dir / subdirectory
        else:
            output_dir = self._base_dir

        output_dir.mkdir(parents=True, exist_ok=True)
        output_path = output_dir / filename

        with open(output_path, "w") as f:
            f.write(data)

        logger.debug(f"Saved raw data to {output_path}")
        return output_path
