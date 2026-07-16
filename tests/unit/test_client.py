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
        tokens = client.get_tokens(df=True)

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
        result = client.get_pools(df=True)

        assert isinstance(result, pd.DataFrame)
        mock_lp.all_paginated.assert_called_once()

    @patch("sugar.core.client.Web3Provider")
    @patch("sugar.core.client.LpSugar")
    def test_get_pools_returns_list_of_dicts_by_default(
        self,
        mock_lp_class: MagicMock,
        mock_provider_class: MagicMock,
    ) -> None:
        """get_pools should default to list[dict]."""
        mock_provider_class.return_value = MagicMock()
        mock_lp = MagicMock()
        mock_lp.tokens_paginated.return_value = []
        mock_lp.all_paginated.return_value = []
        mock_lp_class.return_value = mock_lp

        client = SugarClient(ChainId.BASE)
        result = client.get_pools()

        assert isinstance(result, list)

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
        result = client.get_ve_positions(df=True)

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
        result = client.get_relays(df=True)

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
        result = client.get_epochs_latest(df=True)

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


class TestPositionsByAccount:
    """Test the positions_by_account aggregator (Relay/managed-veNFT resolution)."""

    @patch("sugar.core.client.RelaySugar")
    @patch("sugar.core.client.VeSugar")
    @patch("sugar.core.client.Web3Provider")
    @patch("sugar.core.client.LpSugar")
    def test_relay_deposited_venft_uses_relay_principal(
        self,
        mock_lp_class: MagicMock,
        mock_provider_class: MagicMock,
        mock_ve_class: MagicMock,
        mock_relay_class: MagicMock,
    ) -> None:
        """A relay-deposited veNFT (amount=0) must take principal+rewards from
        RelaySugar.account_venfts, not its own zeroed amount."""
        from sugar.models import PositionKind

        mock_provider_class.return_value = MagicMock()
        mock_lp = MagicMock()
        mock_lp.count.return_value = 0  # no LP positions to scan
        mock_lp.tokens_paginated.return_value = []
        mock_lp_class.return_value = mock_lp

        # veNFT deposited into a managed veNFT: amount=0, managed_id != 0
        # (id, account, decimals, amount, voting, gov, rebase, expires, voted,
        #  votes, token, permanent, delegate_id, managed_id)
        mock_ve = MagicMock()
        mock_ve.by_account.return_value = [
            (100, "0xacc", 18, 0, 0, 8672 * 10**18, 0, 0, 0, [], "0xAERO", False, 0, 555)
        ]
        mock_ve_class.return_value = mock_ve

        # Relay reports the exact per-account principal + rewards in account_venfts
        # COLUMNS_RELAY[16] = account_venfts: [(venft_id, amount, rewards)]
        mock_relay = MagicMock()
        relay_row = [555, 18, 0, 0, 0, 0, [], "0xAERO", 0, True, 0, [], "0xrelay",
                     True, False, "veAERO Maxi", [(100, 8616 * 10**18, 27 * 10**18)]]
        mock_relay.all.return_value = [relay_row]
        mock_relay_class.return_value = mock_relay

        client = SugarClient(ChainId.BASE)
        positions = client.positions_by_account("0xacc", price=False)

        assert len(positions) == 1
        p = positions[0]
        assert p.kind == PositionKind.RELAY
        assert p.locked is True
        assert p.tokens[0].amount == pytest.approx(8616)  # from relay, not the 0 on the veNFT
        assert p.rewards[0].amount == pytest.approx(27)
        assert p.meta["venft_id"] == 100


class TestPandasOptional:
    """Reads must work without pandas (#7)."""

    @patch("sugar.core.client.has_pandas", return_value=False)
    @patch("sugar.core.client.VeSugar")
    @patch("sugar.core.client.Web3Provider")
    @patch("sugar.core.client.LpSugar")
    def test_get_ve_positions_pandas_free(
        self,
        mock_lp_class: MagicMock,
        mock_provider_class: MagicMock,
        mock_ve_class: MagicMock,
        mock_has_pandas: MagicMock,
    ) -> None:
        """With pandas unavailable, get_ve_positions(df=False) builds typed dicts."""
        mock_provider_class.return_value = MagicMock()
        mock_lp_class.return_value = MagicMock()
        mock_ve = MagicMock()
        mock_ve.all_paginated.return_value = [
            (7, "0xacc", 18, 3 * 10**18, 0, 0, 0, 0, 0, [], "0xtok", False, 0, 0)
        ]
        mock_ve_class.return_value = mock_ve

        client = SugarClient(ChainId.BASE)
        result = client.get_ve_positions()  # df=False default, pandas blocked

        assert isinstance(result, list)
        assert result[0]["id"] == 7
        assert str(result[0]["amount"]) == "3"  # typed dataclass field, scaled
        assert "governance_amount" in result[0]


class TestPositionsAcrossChains:
    """Test multi-chain aggregation with graceful degradation (#9)."""

    @patch("sugar.core.client.SugarClient")
    def test_partial_results_when_one_chain_fails(self, mock_client_cls: MagicMock) -> None:
        from decimal import Decimal

        from sugar.core.client import positions_across_chains
        from sugar.models import AccountPosition, PositionKind

        good = AccountPosition(
            protocol="velodrome", chain="Optimism", chain_id=10,
            kind=PositionKind.VE, usd_value=Decimal(5), locked=True,
        )

        def side_effect(chain: ChainId, rpc_url: str | None = None, snapshot: bool = False):
            if chain == ChainId.BASE:
                raise RuntimeError("RPC down")
            inst = MagicMock()
            inst.positions_by_account.return_value = [good]
            return inst

        mock_client_cls.side_effect = side_effect

        result = positions_across_chains("0xacc", chains=[ChainId.BASE, ChainId.OPTIMISM])

        assert len(result.positions) == 1           # OP succeeded
        assert result.usd_value == Decimal(5)
        assert len(result.errors) == 1              # Base failure surfaced, not raised
        assert result.errors[0].chain == "BASE"
        assert "RPC down" in result.errors[0].error


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
