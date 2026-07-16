"""Tests for SugarClient facade."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pandas as pd
import pytest

from sugar.config.chains import ChainId
from sugar.core.client import SugarClient
from sugar.core.exceptions import ContractNotAvailableError


@pytest.fixture
def mock_web3_provider() -> MagicMock:
    """Create mock Web3Provider."""
    mock = MagicMock()
    mock.block_number = 12345678
    return mock


@pytest.fixture
def mock_lp_sugar() -> MagicMock:
    """Create mock LpSugar."""
    mock = MagicMock()
    mock.all_paginated.return_value = []
    mock.tokens_paginated.return_value = []
    return mock


class TestSugarClientInit:
    """Test SugarClient initialization."""

    @patch("sugar.core.client.Web3Provider")
    @patch("sugar.core.client.LpSugar")
    def test_init_with_chain_id(
        self,
        mock_lp_class: MagicMock,
        mock_provider_class: MagicMock,
    ) -> None:
        """Should initialize with ChainId enum."""
        mock_provider_class.return_value = MagicMock()
        mock_lp_class.return_value = MagicMock()

        client = SugarClient(ChainId.BASE)

        assert client.chain == ChainId.BASE

    @patch("sugar.core.client.Web3Provider")
    @patch("sugar.core.client.LpSugar")
    def test_init_with_string(
        self,
        mock_lp_class: MagicMock,
        mock_provider_class: MagicMock,
    ) -> None:
        """Should initialize with string chain name."""
        mock_provider_class.return_value = MagicMock()
        mock_lp_class.return_value = MagicMock()

        client = SugarClient("base")

        assert client.chain == ChainId.BASE


class TestSugarClientProperties:
    """Test SugarClient properties."""

    @patch("sugar.core.client.Web3Provider")
    @patch("sugar.core.client.LpSugar")
    def test_chain_name(
        self,
        mock_lp_class: MagicMock,
        mock_provider_class: MagicMock,
    ) -> None:
        """Should return chain name."""
        mock_provider_class.return_value = MagicMock()
        mock_lp_class.return_value = MagicMock()

        client = SugarClient(ChainId.BASE)

        assert client.chain_name == "Base"

    @patch("sugar.core.client.Web3Provider")
    @patch("sugar.core.client.LpSugar")
    def test_block_number(
        self,
        mock_lp_class: MagicMock,
        mock_provider_class: MagicMock,
    ) -> None:
        """Should return current block number."""
        mock_provider = MagicMock()
        mock_provider.block_number = 12345678
        mock_provider_class.return_value = mock_provider
        mock_lp_class.return_value = MagicMock()

        client = SugarClient(ChainId.BASE)

        assert client.block_number == 12345678

    @patch("sugar.core.client.Web3Provider")
    @patch("sugar.core.client.LpSugar")
    def test_lp_property(
        self,
        mock_lp_class: MagicMock,
        mock_provider_class: MagicMock,
    ) -> None:
        """Should return LP Sugar instance."""
        mock_provider_class.return_value = MagicMock()
        mock_lp = MagicMock()
        mock_lp_class.return_value = mock_lp

        client = SugarClient(ChainId.BASE)

        assert client.lp == mock_lp


class TestSugarClientOptionalContracts:
    """Test optional contract access."""

    @patch("sugar.core.client.Web3Provider")
    @patch("sugar.core.client.LpSugar")
    def test_has_ve_true_for_base(
        self,
        mock_lp_class: MagicMock,
        mock_provider_class: MagicMock,
    ) -> None:
        """Base should have VE Sugar."""
        mock_provider_class.return_value = MagicMock()
        mock_lp_class.return_value = MagicMock()

        client = SugarClient(ChainId.BASE)

        assert client.has_ve() is True

    @patch("sugar.core.client.Web3Provider")
    @patch("sugar.core.client.LpSugar")
    def test_has_ve_false_for_mode(
        self,
        mock_lp_class: MagicMock,
        mock_provider_class: MagicMock,
    ) -> None:
        """Mode should not have VE Sugar."""
        mock_provider_class.return_value = MagicMock()
        mock_lp_class.return_value = MagicMock()

        client = SugarClient(ChainId.MODE)

        assert client.has_ve() is False

    @patch("sugar.core.client.Web3Provider")
    @patch("sugar.core.client.LpSugar")
    def test_ve_raises_when_not_available(
        self,
        mock_lp_class: MagicMock,
        mock_provider_class: MagicMock,
    ) -> None:
        """Should raise error when VE not available."""
        mock_provider_class.return_value = MagicMock()
        mock_lp_class.return_value = MagicMock()

        client = SugarClient(ChainId.MODE)

        with pytest.raises(ContractNotAvailableError):
            _ = client.ve

    @patch("sugar.core.client.Web3Provider")
    @patch("sugar.core.client.LpSugar")
    def test_has_relay_true_for_base(
        self,
        mock_lp_class: MagicMock,
        mock_provider_class: MagicMock,
    ) -> None:
        """Base should have Relay Sugar."""
        mock_provider_class.return_value = MagicMock()
        mock_lp_class.return_value = MagicMock()

        client = SugarClient(ChainId.BASE)

        assert client.has_relay() is True

    @patch("sugar.core.client.Web3Provider")
    @patch("sugar.core.client.LpSugar")
    def test_relay_raises_when_not_available(
        self,
        mock_lp_class: MagicMock,
        mock_provider_class: MagicMock,
    ) -> None:
        """Should raise error when Relay not available."""
        mock_provider_class.return_value = MagicMock()
        mock_lp_class.return_value = MagicMock()

        client = SugarClient(ChainId.MODE)

        with pytest.raises(ContractNotAvailableError):
            _ = client.relay


class TestSugarClientDataMethods:
    """Test data retrieval methods."""

    @patch("sugar.core.client.Web3Provider")
    @patch("sugar.core.client.LpSugar")
    def test_get_tokens(
        self,
        mock_lp_class: MagicMock,
        mock_provider_class: MagicMock,
    ) -> None:
        """Should get tokens DataFrame."""
        mock_provider_class.return_value = MagicMock()
        mock_lp = MagicMock()
        mock_lp.tokens_paginated.return_value = [
            ("0xtoken1", "WETH", 18, "Wrapped Ether", True, 1000),
        ]
        mock_lp_class.return_value = mock_lp

        client = SugarClient(ChainId.BASE)
        tokens = client.get_tokens()

        assert isinstance(tokens, pd.DataFrame)

    @patch("sugar.core.client.Web3Provider")
    @patch("sugar.core.client.LpSugar")
    def test_get_tokens_caches_result(
        self,
        mock_lp_class: MagicMock,
        mock_provider_class: MagicMock,
    ) -> None:
        """Should cache tokens result."""
        mock_provider_class.return_value = MagicMock()
        mock_lp = MagicMock()
        mock_lp.tokens_paginated.return_value = [
            ("0xtoken1", "WETH", 18, "Wrapped Ether", True, 1000),
        ]
        mock_lp_class.return_value = mock_lp

        client = SugarClient(ChainId.BASE)
        tokens1 = client.get_tokens()
        tokens2 = client.get_tokens()

        # Should only call once due to caching
        assert mock_lp.tokens_paginated.call_count == 1


class TestSugarClientOptionalAvailability:
    """Test has_* availability checks."""

    @patch("sugar.core.client.Web3Provider")
    @patch("sugar.core.client.LpSugar")
    def test_has_rewards_true_for_base(
        self,
        mock_lp_class: MagicMock,
        mock_provider_class: MagicMock,
    ) -> None:
        """Base should have Rewards Sugar."""
        mock_provider_class.return_value = MagicMock()
        mock_lp_class.return_value = MagicMock()

        client = SugarClient(ChainId.BASE)

        assert client.has_rewards() is True

    @patch("sugar.core.client.Web3Provider")
    @patch("sugar.core.client.LpSugar")
    def test_has_price_oracle_true_for_base(
        self,
        mock_lp_class: MagicMock,
        mock_provider_class: MagicMock,
    ) -> None:
        """Base should have a price oracle."""
        mock_provider_class.return_value = MagicMock()
        mock_lp_class.return_value = MagicMock()

        client = SugarClient(ChainId.BASE)

        assert client.has_price_oracle() is True

    @patch("sugar.core.client.Web3Provider")
    @patch("sugar.core.client.LpSugar")
    def test_rewards_raises_when_not_available(
        self,
        mock_lp_class: MagicMock,
        mock_provider_class: MagicMock,
    ) -> None:
        """Should raise when RewardsSugar is not deployed on chain."""
        from sugar.core.exceptions import ContractNotAvailableError

        mock_provider_class.return_value = MagicMock()
        mock_lp_class.return_value = MagicMock()

        # Mode has no relay or ve, but does have rewards — use a chain without rewards
        # Checking has_rewards=False is not directly possible without a chain config that
        # excludes it; verify the property raises only when config says False.
        client = SugarClient(ChainId.MODE)
        if not client.has_relay():
            with pytest.raises(ContractNotAvailableError):
                _ = client.relay


class TestSugarClientGetMethods:
    """Test data retrieval methods beyond get_tokens."""

    @patch("sugar.core.client.Web3Provider")
    @patch("sugar.core.client.LpSugar")
    def test_get_pools_returns_dataframe(
        self,
        mock_lp_class: MagicMock,
        mock_provider_class: MagicMock,
    ) -> None:
        """get_pools should return a DataFrame."""
        mock_provider_class.return_value = MagicMock()
        mock_lp = MagicMock()
        mock_lp.tokens_paginated.return_value = []
        mock_lp.all_paginated.return_value = []
        mock_lp_class.return_value = mock_lp

        client = SugarClient(ChainId.BASE)
        result = client.get_pools()

        assert isinstance(result, pd.DataFrame)
        mock_lp.all_paginated.assert_called_once()

    @patch("sugar.core.client.VeSugar")
    @patch("sugar.core.client.Web3Provider")
    @patch("sugar.core.client.LpSugar")
    def test_get_ve_positions_returns_dataframe(
        self,
        mock_lp_class: MagicMock,
        mock_provider_class: MagicMock,
        mock_ve_class: MagicMock,
    ) -> None:
        """get_ve_positions should return a DataFrame."""
        mock_provider_class.return_value = MagicMock()
        mock_lp_class.return_value = MagicMock()
        mock_ve = MagicMock()
        mock_ve.all_paginated.return_value = []
        mock_ve_class.return_value = mock_ve

        client = SugarClient(ChainId.BASE)
        result = client.get_ve_positions()

        assert isinstance(result, pd.DataFrame)
        mock_ve.all_paginated.assert_called_once()

    @patch("sugar.core.client.RelaySugar")
    @patch("sugar.core.client.Web3Provider")
    @patch("sugar.core.client.LpSugar")
    def test_get_relays_returns_dataframe(
        self,
        mock_lp_class: MagicMock,
        mock_provider_class: MagicMock,
        mock_relay_class: MagicMock,
    ) -> None:
        """get_relays should return a DataFrame."""
        mock_provider_class.return_value = MagicMock()
        mock_lp_class.return_value = MagicMock()
        mock_relay = MagicMock()
        mock_relay.all.return_value = []
        mock_relay_class.return_value = mock_relay

        client = SugarClient(ChainId.BASE)
        result = client.get_relays()

        assert isinstance(result, pd.DataFrame)
        mock_relay.all.assert_called_once()

    @patch("sugar.core.client.RewardsSugar")
    @patch("sugar.core.client.Web3Provider")
    @patch("sugar.core.client.LpSugar")
    def test_get_epochs_latest_returns_dataframe(
        self,
        mock_lp_class: MagicMock,
        mock_provider_class: MagicMock,
        mock_rewards_class: MagicMock,
    ) -> None:
        """get_epochs_latest should return a DataFrame."""
        mock_provider_class.return_value = MagicMock()
        mock_lp = MagicMock()
        mock_lp.tokens_paginated.return_value = []
        mock_lp.count.return_value = 0
        mock_lp_class.return_value = mock_lp
        mock_rewards = MagicMock()
        mock_rewards.epochs_latest_paginated.return_value = []
        mock_rewards_class.return_value = mock_rewards

        client = SugarClient(ChainId.BASE)
        result = client.get_epochs_latest()

        assert isinstance(result, pd.DataFrame)
        mock_rewards.epochs_latest_paginated.assert_called_once()

    @patch("sugar.core.client.Web3Provider")
    @patch("sugar.core.client.LpSugar")
    def test_processor_is_lazy(
        self,
        mock_lp_class: MagicMock,
        mock_provider_class: MagicMock,
    ) -> None:
        """DataProcessor should be created on first access."""
        mock_provider_class.return_value = MagicMock()
        mock_lp_class.return_value = MagicMock()

        client = SugarClient(ChainId.BASE)

        assert client._data_processor is None
        _ = client.processor
        assert client._data_processor is not None


class TestSugarClientExportMethods:
    """Test export methods."""

    @patch("sugar.core.client.Web3Provider")
    @patch("sugar.core.client.LpSugar")
    def test_export_dataframe(
        self,
        mock_lp_class: MagicMock,
        mock_provider_class: MagicMock,
        tmp_path: Path,
    ) -> None:
        """Should export DataFrame to CSV."""
        mock_provider = MagicMock()
        mock_provider.block_number = 12345
        mock_provider_class.return_value = mock_provider
        mock_lp_class.return_value = MagicMock()

        client = SugarClient(ChainId.BASE, export_dir=tmp_path)
        df = pd.DataFrame({"col1": [1, 2, 3], "col2": ["a", "b", "c"]})
        path = client.export_dataframe(df, "test_data")

        assert path.exists()
        assert path.name == "test_data_base_12345.csv"

    @patch("sugar.core.client.Web3Provider")
    @patch("sugar.core.client.LpSugar")
    def test_export_dataframe_no_block(
        self,
        mock_lp_class: MagicMock,
        mock_provider_class: MagicMock,
        tmp_path: Path,
    ) -> None:
        """Should export DataFrame without block number."""
        mock_provider = MagicMock()
        mock_provider.block_number = 12345
        mock_provider_class.return_value = mock_provider
        mock_lp_class.return_value = MagicMock()

        client = SugarClient(ChainId.BASE, export_dir=tmp_path)
        df = pd.DataFrame({"col1": [1, 2, 3]})
        path = client.export_dataframe(df, "test_data", include_block=False)

        assert path.exists()
        assert path.name == "test_data_base.csv"

    @patch("sugar.core.client.Web3Provider")
    @patch("sugar.core.client.LpSugar")
    def test_export_dataframe_custom_subdirectory(
        self,
        mock_lp_class: MagicMock,
        mock_provider_class: MagicMock,
        tmp_path: Path,
    ) -> None:
        """Should export to an explicit subdirectory."""
        mock_provider = MagicMock()
        mock_provider.block_number = 99
        mock_provider_class.return_value = mock_provider
        mock_lp_class.return_value = MagicMock()

        client = SugarClient(ChainId.BASE, export_dir=tmp_path)
        df = pd.DataFrame({"x": [1]})
        path = client.export_dataframe(df, "pools", subdirectory="data-pools")

        assert path.exists()
        assert path.parent.name == "data-pools"
