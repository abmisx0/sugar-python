"""Tests for SugarClient facade."""

from __future__ import annotations

from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, patch, PropertyMock

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


class TestSugarClientExportMethods:
    """Test export methods."""

    @patch("sugar.core.client.Web3Provider")
    @patch("sugar.core.client.LpSugar")
    def test_export_pools(
        self,
        mock_lp_class: MagicMock,
        mock_provider_class: MagicMock,
        tmp_path: Path,
    ) -> None:
        """Should export pools to CSV."""
        mock_provider = MagicMock()
        mock_provider.block_number = 12345
        mock_provider_class.return_value = mock_provider

        mock_lp = MagicMock()
        mock_lp.all_paginated.return_value = []
        mock_lp.tokens_paginated.return_value = []
        mock_lp_class.return_value = mock_lp

        client = SugarClient(ChainId.BASE, export_dir=tmp_path)
        path = client.export_pools()

        assert path.exists()
        assert "lp_all" in path.name

    @patch("sugar.core.client.Web3Provider")
    @patch("sugar.core.client.LpSugar")
    def test_export_tokens(
        self,
        mock_lp_class: MagicMock,
        mock_provider_class: MagicMock,
        tmp_path: Path,
    ) -> None:
        """Should export tokens to CSV."""
        mock_provider_class.return_value = MagicMock()

        mock_lp = MagicMock()
        mock_lp.tokens_paginated.return_value = [
            ("0xtoken1", "WETH", 18, "Wrapped Ether", True, 1000),
        ]
        mock_lp_class.return_value = mock_lp

        client = SugarClient(ChainId.BASE, export_dir=tmp_path)
        path = client.export_tokens()

        assert path.exists()
        assert "lp_tokens" in path.name
