"""Tests for data processor service."""

from __future__ import annotations

from decimal import Decimal
from unittest.mock import MagicMock

import pandas as pd
import pytest

from sugar.services.data_processor import DataProcessor


@pytest.fixture
def mock_price_provider() -> MagicMock:
    """Create mock price provider."""
    provider = MagicMock()
    provider.get_price_usd.return_value = None
    return provider


@pytest.fixture
def processor(mock_price_provider: MagicMock) -> DataProcessor:
    """Create data processor with mock price provider."""
    return DataProcessor(mock_price_provider)


class TestProcessTokens:
    """Test process_tokens method."""

    def test_processes_token_tuples(self, processor: DataProcessor) -> None:
        """Should process token tuples into DataFrame."""
        raw_data = [
            (
                "0xtoken_address1",
                "WETH",
                18,
                "Wrapped Ether",
                True,
                1000000000000000000000000,
            ),
            (
                "0xtoken_address2",
                "USDC",
                6,
                "USD Coin",
                True,
                1000000000000,
            ),
        ]

        result = processor.process_tokens(raw_data)

        assert isinstance(result, pd.DataFrame)
        assert len(result) == 2
        assert "symbol" in result.columns
        assert "decimals" in result.columns
        assert "listed" in result.columns

    def test_filters_listed_tokens(self, processor: DataProcessor) -> None:
        """Should filter for listed tokens only."""
        raw_data = [
            ("0xtoken1", "WETH", 18, "Wrapped Ether", True, 1000),
            ("0xtoken2", "UNLISTED", 18, "Unlisted Token", False, 1000),
        ]

        result = processor.process_tokens(raw_data, listed_only=True)

        assert len(result) == 1
        assert result.iloc[0]["symbol"] == "WETH"

    def test_empty_data(self, processor: DataProcessor) -> None:
        """Should handle empty data."""
        result = processor.process_tokens([])

        assert isinstance(result, pd.DataFrame)
        assert len(result) == 0


class TestProcessEpochsLatest:
    """Test process_epochs_latest method."""

    def test_processes_epoch_tuples(self, processor: DataProcessor) -> None:
        """Should process epoch tuples into DataFrame."""
        epoch_data = [
            (
                1704067200,  # ts
                "0xpool",  # lp
                1000000000000000000000,  # votes
                1000000000000000000,  # emissions
                (),  # incentives
                (),  # fees
            ),
        ]

        tokens_df = pd.DataFrame(
            {"symbol": ["WETH"], "decimals": [18]},
            index=["0xtoken"],
        )

        result = processor.process_epochs_latest(epoch_data, tokens_df)

        assert isinstance(result, pd.DataFrame)

    def test_empty_data(self, processor: DataProcessor) -> None:
        """Should handle empty epoch data."""
        tokens_df = pd.DataFrame(
            {"symbol": ["WETH"], "decimals": [18]},
            index=["0xtoken"],
        )

        result = processor.process_epochs_latest([], tokens_df)

        assert isinstance(result, pd.DataFrame)
        assert len(result) == 0
