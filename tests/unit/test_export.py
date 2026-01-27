"""Tests for export service."""

from __future__ import annotations

import os
from pathlib import Path

import pandas as pd
import pytest

from sugar.services.export import ExportService


@pytest.fixture
def temp_export_dir(tmp_path: Path) -> Path:
    """Create temporary export directory."""
    return tmp_path


@pytest.fixture
def export_service(temp_export_dir: Path) -> ExportService:
    """Create export service with temp directory."""
    return ExportService(temp_export_dir)


@pytest.fixture
def sample_df() -> pd.DataFrame:
    """Create sample DataFrame for testing."""
    return pd.DataFrame(
        {
            "col1": [1, 2, 3],
            "col2": ["a", "b", "c"],
            "col3": [1.1, 2.2, 3.3],
        }
    )


class TestToCsv:
    """Test to_csv method."""

    def test_exports_dataframe(
        self, export_service: ExportService, sample_df: pd.DataFrame
    ) -> None:
        """Should export DataFrame to CSV."""
        path = export_service.to_csv(sample_df, "test.csv")

        assert path.exists()
        assert path.name == "test.csv"

    def test_creates_subdirectory(
        self, export_service: ExportService, sample_df: pd.DataFrame
    ) -> None:
        """Should create subdirectory if specified."""
        path = export_service.to_csv(sample_df, "test.csv", subdirectory="subdir")

        assert path.exists()
        assert "subdir" in str(path)

    def test_includes_index_by_default(
        self, export_service: ExportService, sample_df: pd.DataFrame
    ) -> None:
        """Should include index by default."""
        path = export_service.to_csv(sample_df, "test.csv")

        df_read = pd.read_csv(path, index_col=0)
        assert len(df_read) == 3

    def test_excludes_index_when_specified(
        self, export_service: ExportService, sample_df: pd.DataFrame
    ) -> None:
        """Should exclude index when specified."""
        path = export_service.to_csv(sample_df, "test.csv", index=False)

        df_read = pd.read_csv(path)
        assert "Unnamed: 0" not in df_read.columns


class TestToJson:
    """Test to_json method."""

    def test_exports_dataframe(
        self, export_service: ExportService, sample_df: pd.DataFrame
    ) -> None:
        """Should export DataFrame to JSON."""
        path = export_service.to_json(sample_df, "test.json")

        assert path.exists()
        assert path.name == "test.json"

    def test_default_records_orient(
        self, export_service: ExportService, sample_df: pd.DataFrame
    ) -> None:
        """Should use records orientation by default."""
        path = export_service.to_json(sample_df, "test.json")

        df_read = pd.read_json(path)
        assert len(df_read) == 3


class TestExportLpData:
    """Test export_lp_data method."""

    def test_exports_lp_data(
        self, export_service: ExportService, sample_df: pd.DataFrame
    ) -> None:
        """Should export LP data to correct location."""
        path = export_service.export_lp_data(sample_df, "base")

        assert path.exists()
        assert "data-lp" in str(path)
        assert "lp_all_base" in path.name

    def test_includes_block_number(
        self, export_service: ExportService, sample_df: pd.DataFrame
    ) -> None:
        """Should include block number in filename."""
        path = export_service.export_lp_data(sample_df, "base", block_num=12345)

        assert "12345" in path.name

    def test_no_block_number(
        self, export_service: ExportService, sample_df: pd.DataFrame
    ) -> None:
        """Should work without block number."""
        path = export_service.export_lp_data(sample_df, "base")

        assert path.exists()


class TestExportTokens:
    """Test export_tokens method."""

    def test_exports_tokens(
        self, export_service: ExportService, sample_df: pd.DataFrame
    ) -> None:
        """Should export token data."""
        path = export_service.export_tokens(sample_df, "base")

        assert path.exists()
        assert "lp_tokens_base" in path.name


class TestExportVeData:
    """Test export_ve_data method."""

    def test_exports_ve_data(
        self, export_service: ExportService, sample_df: pd.DataFrame
    ) -> None:
        """Should export VE data."""
        path = export_service.export_ve_data(sample_df, "base")

        assert path.exists()
        assert "data-ve" in str(path)
        assert "ve_all_base" in path.name


class TestExportRelayData:
    """Test export_relay_data method."""

    def test_exports_relay_data(
        self, export_service: ExportService, sample_df: pd.DataFrame
    ) -> None:
        """Should export relay data."""
        path = export_service.export_relay_data(sample_df, "base")

        assert path.exists()
        assert "data-relay" in str(path)
        assert "relay_all_base" in path.name


class TestExportEpochs:
    """Test export_epochs method."""

    def test_exports_epochs(
        self, export_service: ExportService, sample_df: pd.DataFrame
    ) -> None:
        """Should export epoch data."""
        path = export_service.export_epochs(sample_df, "base")

        assert path.exists()
        assert "data-rewards" in str(path)
        assert "epochs_latest_base" in path.name


class TestExportCombined:
    """Test export_combined method."""

    def test_exports_combined(
        self, export_service: ExportService, sample_df: pd.DataFrame
    ) -> None:
        """Should export combined data."""
        path = export_service.export_combined(sample_df, "base")

        assert path.exists()
        assert "data-combined" in str(path)
        assert "pools_with_rewards_base" in path.name


class TestSaveRaw:
    """Test save_raw method."""

    def test_saves_raw_data(
        self, export_service: ExportService
    ) -> None:
        """Should save raw string data."""
        data = "This is raw data content"
        path = export_service.save_raw(data, "raw.txt")

        assert path.exists()
        assert path.read_text() == data

    def test_creates_subdirectory(
        self, export_service: ExportService
    ) -> None:
        """Should create subdirectory."""
        data = "test"
        path = export_service.save_raw(data, "test.txt", subdirectory="raw")

        assert path.exists()
        assert "raw" in str(path)
