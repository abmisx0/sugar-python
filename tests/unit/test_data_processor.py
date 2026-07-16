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


class TestProcessLpAll:
    """Test process_lp_all method."""

    def _lp_tuple(self, lp="0xpool1", symbol="vAMM-WETH/USDC"):
        """Build a 32-field LP tuple matching COLUMNS_LP."""
        return (
            lp, symbol, 18, 1_000_000, -1, 0, 0,
            "0xweth", 100 * 10**18, 50 * 10**18,
            "0xusdc", 200_000 * 10**6, 100_000 * 10**6,
            "0xgauge", 50_000, True,
            "0xfee", "0xbribe", "0xfactory",
            10 * 10**18, "0xvelo", 100 * 10**18,
            30, 0, 1 * 10**18, 2_000 * 10**6,
            False, False, 1_704_067_200, "0xnfpm", "0xalm", "0xroot",
        )

    def test_processes_lp_tuples(self, processor: DataProcessor) -> None:
        """Should process LP tuples into DataFrame."""
        result = processor.process_lp_all([self._lp_tuple()])

        assert isinstance(result, pd.DataFrame)
        assert len(result) == 1
        assert "lp" in result.columns
        assert "symbol" in result.columns
        assert result.iloc[0]["lp"] == "0xpool1"

    def test_deduplicates_by_lp_address(self, processor: DataProcessor) -> None:
        """Should drop duplicate LP addresses."""
        result = processor.process_lp_all([
            self._lp_tuple("0xpool1"),
            self._lp_tuple("0xpool1"),  # duplicate
            self._lp_tuple("0xpool2"),
        ])

        assert len(result) == 2

    def test_cleans_tether_symbol(self, processor: DataProcessor) -> None:
        """Should replace ₮ with T in symbols."""
        result = processor.process_lp_all([self._lp_tuple(symbol="vAMM-WETH/USD₮")])

        assert result.iloc[0]["symbol"] == "vAMM-WETH/USDT"

    def test_cleans_vamm_v2_symbol(self, processor: DataProcessor) -> None:
        """Should replace vAMMV2 with vAMM in symbols."""
        result = processor.process_lp_all([self._lp_tuple(symbol="vAMMV2-WETH/USDC")])

        assert result.iloc[0]["symbol"] == "vAMM-WETH/USDC"

    def test_cleans_samm_v2_symbol(self, processor: DataProcessor) -> None:
        """Should replace sAMMV2 with sAMM in symbols."""
        result = processor.process_lp_all([self._lp_tuple(symbol="sAMMV2-USDC/DAI")])

        assert result.iloc[0]["symbol"] == "sAMM-USDC/DAI"

    def test_handles_tuple_without_root_column(self, processor: DataProcessor) -> None:
        """Should handle 31-field tuples (no root column)."""
        short_tuple = self._lp_tuple()[:-1]  # drop root
        result = processor.process_lp_all([short_tuple])

        assert isinstance(result, pd.DataFrame)
        assert len(result) == 1
        assert "root" not in result.columns

    def test_empty_data(self, processor: DataProcessor) -> None:
        """Should return empty DataFrame for empty input."""
        result = processor.process_lp_all([])

        assert isinstance(result, pd.DataFrame)
        assert len(result) == 0


class TestProcessVeAll:
    """Test process_ve_all method."""

    def _ve_tuple(self, venft_id=1):
        """Build a 14-field veNFT tuple matching COLUMNS_VENFT."""
        return (
            venft_id,               # id
            "0xowner",              # account
            18,                     # decimals
            1_000 * 10**18,         # amount
            900 * 10**18,           # voting_amount
            800 * 10**18,           # governance_amount
            100 * 10**18,           # rebase_amount
            1_735_689_600,          # expires_at
            1_704_067_200,          # voted_at
            [("0xpool1", 400 * 10**18)],  # votes
            "0xtoken",              # token
            False,                  # permanent
            0,                      # delegate_id
            0,                      # managed_id
        )

    def test_processes_venft_tuples(self, processor: DataProcessor) -> None:
        """Should process veNFT tuples into DataFrame indexed by id."""
        result = processor.process_ve_all([self._ve_tuple()])

        assert isinstance(result, pd.DataFrame)
        assert len(result) == 1
        assert result.index.name == "id"
        assert 1 in result.index

    def test_converts_wei_amounts(self, processor: DataProcessor) -> None:
        """Should convert wei amounts to decimal floats."""
        result = processor.process_ve_all([self._ve_tuple()])

        assert result.loc[1, "amount"] == pytest.approx(1000.0)
        assert result.loc[1, "voting_amount"] == pytest.approx(900.0)
        assert result.loc[1, "governance_amount"] == pytest.approx(800.0)

    def test_normalises_vote_weights(self, processor: DataProcessor) -> None:
        """Should convert vote amounts to fractional weights (0–1)."""
        result = processor.process_ve_all([self._ve_tuple()])
        votes = result.loc[1, "votes"]

        assert len(votes) == 1
        pool_addr, weight = votes[0]
        assert pool_addr == "0xpool1"
        assert 0.0 < weight <= 1.0

    def test_deduplicates_by_id(self, processor: DataProcessor) -> None:
        """Should drop duplicate veNFT IDs."""
        result = processor.process_ve_all([self._ve_tuple(1), self._ve_tuple(1)])

        assert len(result) == 1

    def test_empty_data(self, processor: DataProcessor) -> None:
        """Should return empty DataFrame for empty input."""
        result = processor.process_ve_all([])

        assert isinstance(result, pd.DataFrame)
        assert len(result) == 0


class TestProcessRelayAll:
    """Test process_relay_all method."""

    def _relay_tuple(self, inactive=False, name=b"Test Relay\x00\x00\x00\x00\x00\x00"):
        """Build a 17-field relay tuple matching COLUMNS_RELAY."""
        return (
            1,                              # venft_id
            18,                             # decimals
            1_000 * 10**18,                 # amount
            900 * 10**18,                   # voting_amount
            800 * 10**18,                   # used_voting_amount
            1_704_067_200,                  # voted_at
            [("0xpool1", 400 * 10**18)],    # votes
            "0xtoken",                      # token
            50 * 10**18,                    # compounded
            0,                              # withdrawable
            1_704_067_200,                  # run_at
            ["0xmanager"],                  # managers (address[])
            "0xrelay",                      # relay
            False,                          # compounder
            inactive,                       # inactive
            name,                           # name
            [],                             # account_venfts
        )

    def test_processes_relay_tuples(self, processor: DataProcessor) -> None:
        """Should process relay tuples into DataFrame indexed by venft_id."""
        result = processor.process_relay_all([self._relay_tuple()])

        assert isinstance(result, pd.DataFrame)
        assert result.index.name == "venft_id"
        assert 1 in result.index

    def test_decodes_bytes_name(self, processor: DataProcessor) -> None:
        """Should decode bytes32 name to a clean string."""
        result = processor.process_relay_all([self._relay_tuple()])

        assert result.loc[1, "name"] == "Test Relay"

    def test_strips_null_padding_from_name(self, processor: DataProcessor) -> None:
        """Should strip null bytes from decoded name (bytes type)."""
        result = processor.process_relay_all([self._relay_tuple(name=b"Short\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00")])

        assert result.loc[1, "name"] == "Short"
        assert "\x00" not in result.loc[1, "name"]

    def test_strips_null_padding_from_string_name(self, processor: DataProcessor) -> None:
        """Should strip null bytes from str name (web3.py returns str for ABI type 'string')."""
        result = processor.process_relay_all([self._relay_tuple(name="Grey Wolf\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00")])

        assert result.loc[1, "name"] == "Grey Wolf"
        assert "\x00" not in result.loc[1, "name"]

    def test_converts_wei_amounts(self, processor: DataProcessor) -> None:
        """Should convert amount and compounded from wei."""
        result = processor.process_relay_all([self._relay_tuple()])

        assert result.loc[1, "amount"] == pytest.approx(1000.0)
        assert result.loc[1, "compounded"] == pytest.approx(50.0)

    def test_filters_inactive_relays_by_default(self, processor: DataProcessor) -> None:
        """Should exclude inactive relays when filter_inactive=True."""
        raw = [self._relay_tuple(inactive=False), self._relay_tuple(inactive=True)]
        # Two rows with same venft_id won't work, use distinct IDs via direct tuple
        active = self._relay_tuple(inactive=False)
        inactive = list(self._relay_tuple(inactive=True))
        inactive[0] = 2  # venft_id = 2
        result = processor.process_relay_all([active, tuple(inactive)], filter_inactive=True)

        assert 1 in result.index
        assert 2 not in result.index

    def test_includes_inactive_when_requested(self, processor: DataProcessor) -> None:
        """Should include inactive relays when filter_inactive=False."""
        t = list(self._relay_tuple(inactive=True))
        result = processor.process_relay_all([tuple(t)], filter_inactive=False)

        assert len(result) == 1

    def test_empty_data(self, processor: DataProcessor) -> None:
        """Should return empty DataFrame for empty input."""
        result = processor.process_relay_all([])

        assert isinstance(result, pd.DataFrame)
        assert len(result) == 0


class TestCombineLpWithRewards:
    """Test combine_lp_with_rewards method."""

    def _make_lp_df(self):
        return pd.DataFrame({
            "lp": ["0xpool1", "0xpool2"],
            "symbol": ["vAMM-A/B", "vAMM-C/D"],
            "token0": ["0xtokA", "0xtokC"],
            "token1": ["0xtokB", "0xtokD"],
            "reserve0": [100 * 10**18, 200 * 10**18],
            "reserve1": [100 * 10**18, 200 * 10**18],
            "token0_fees": [1 * 10**18, 2 * 10**18],
            "token1_fees": [1 * 10**18, 2 * 10**18],
        })

    def _make_epochs_df(self):
        return pd.DataFrame({
            "lp": ["0xpool1"],
            "votes": [1000.0],
            "emissions": [10.0],
            "incentives": [[]],
            "fees": [[]],
        })

    def test_inner_join_returns_only_pools_with_rewards(self, processor: DataProcessor) -> None:
        """Should only include pools that have epoch rewards (inner join)."""
        result = processor.combine_lp_with_rewards(
            self._make_lp_df(), self._make_epochs_df(), only_with_rewards=True
        )

        assert len(result) == 1
        assert result.iloc[0]["lp"] == "0xpool1"

    def test_left_join_includes_all_pools(self, processor: DataProcessor) -> None:
        """Should include all pools including those without rewards (left join)."""
        result = processor.combine_lp_with_rewards(
            self._make_lp_df(), self._make_epochs_df(), only_with_rewards=False
        )

        assert len(result) == 2

    def test_no_usd_columns_without_price_provider(self) -> None:
        """Should not add USD columns when no price provider is set."""
        processor_no_prices = DataProcessor(price_provider=None)
        result = processor_no_prices.combine_lp_with_rewards(
            self._make_lp_df(), self._make_epochs_df()
        )

        assert "tvl_usd" not in result.columns
        assert "incentives_usd" not in result.columns

    def test_adds_usd_columns_with_price_provider(self, mock_price_provider: MagicMock) -> None:
        """Should add USD pricing columns when price provider is available."""
        import time

        from sugar.services.price_provider import PriceResult

        mock_price_provider.get_price_usd.return_value = PriceResult(
            price=Decimal("1.0"), source="mock", timestamp=int(time.time())
        )
        mock_price_provider.prefetch_prices.return_value = None
        mock_price_provider.set_tokens_df.return_value = None

        tokens_df = pd.DataFrame(
            {"symbol": ["TokA", "TokB"], "decimals": [18, 18]},
            index=["0xtokA", "0xtokB"],
        )
        processor_with_prices = DataProcessor(price_provider=mock_price_provider)
        result = processor_with_prices.combine_lp_with_rewards(
            self._make_lp_df(), self._make_epochs_df(), tokens_df=tokens_df
        )

        assert "tvl_usd" in result.columns
        assert "incentives_usd" in result.columns
        assert "gauge_fees_usd" in result.columns


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
