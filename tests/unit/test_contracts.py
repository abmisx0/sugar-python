"""Tests for contract wrappers."""

from __future__ import annotations

from typing import Any
from unittest.mock import MagicMock, patch


class TestLpSugar:
    """Test LpSugar contract wrapper."""

    @patch("sugar.contracts.base.load_abi")
    @patch("sugar.contracts.base.Web3.to_checksum_address")
    def test_count(
        self, mock_checksum: MagicMock, mock_load_abi: MagicMock
    ) -> None:
        """Should call count function."""
        from sugar.contracts.lp_sugar import LpSugar

        mock_checksum.return_value = "0xcontract"
        mock_load_abi.return_value = []

        mock_provider = MagicMock()
        mock_contract = MagicMock()
        mock_provider.web3.eth.contract.return_value = mock_contract
        mock_contract.functions.count.return_value.call.return_value = 100

        lp = LpSugar(mock_provider, "0xcontract", ())
        count = lp.count()

        assert count == 100

    @patch("sugar.contracts.base.load_abi")
    @patch("sugar.contracts.base.Web3.to_checksum_address")
    def test_all(
        self, mock_checksum: MagicMock, mock_load_abi: MagicMock
    ) -> None:
        """Should call all function with limit and offset."""
        from sugar.contracts.lp_sugar import LpSugar

        mock_checksum.return_value = "0xcontract"
        mock_load_abi.return_value = []

        mock_provider = MagicMock()
        mock_contract = MagicMock()
        mock_provider.web3.eth.contract.return_value = mock_contract
        mock_data = [("0xpool1",), ("0xpool2",)]
        mock_contract.functions.all.return_value.call.return_value = mock_data

        lp = LpSugar(mock_provider, "0xcontract", ())
        result = lp.all(limit=100, offset=0)

        assert result == mock_data

    @patch("sugar.contracts.base.load_abi")
    @patch("sugar.contracts.base.Web3.to_checksum_address")
    def test_positions_paginated_scans_past_empty_pages(
        self, mock_checksum: MagicMock, mock_load_abi: MagicMock
    ) -> None:
        """positions() paginates over pool space, so early empty pages must not
        stop the scan — the position lives in a later page."""
        from sugar.contracts.lp_sugar import LpSugar

        mock_checksum.return_value = "0xcontract"
        mock_load_abi.return_value = []

        mock_provider = MagicMock()
        mock_contract = MagicMock()
        mock_provider.web3.eth.contract.return_value = mock_contract
        # 300 pools -> 3 pages at limit=100; the position is only in page 2.
        mock_contract.functions.count.return_value.call.return_value = 300
        the_pos = (42, "0xlp")
        mock_contract.functions.positions.return_value.call.side_effect = [[], [the_pos], []]

        lp = LpSugar(mock_provider, "0xcontract", ())
        result = lp.positions_paginated("0xaccount", limit=100)

        assert result == [the_pos]  # found despite the first page being empty

    @patch("sugar.contracts.base.load_abi")
    @patch("sugar.contracts.base.Web3.to_checksum_address")
    def test_by_index(
        self, mock_checksum: MagicMock, mock_load_abi: MagicMock
    ) -> None:
        """Should get pool by index."""
        from sugar.contracts.lp_sugar import LpSugar

        mock_checksum.return_value = "0xcontract"
        mock_load_abi.return_value = []

        mock_provider = MagicMock()
        mock_contract = MagicMock()
        mock_provider.web3.eth.contract.return_value = mock_contract
        mock_data = ("0xpool1",)
        mock_contract.functions.byIndex.return_value.call.return_value = mock_data

        lp = LpSugar(mock_provider, "0xcontract", ())
        result = lp.by_index(0)

        assert result == mock_data

    @patch("sugar.contracts.base.load_abi")
    @patch("sugar.contracts.base.Web3.to_checksum_address")
    def test_by_address(
        self, mock_checksum: MagicMock, mock_load_abi: MagicMock
    ) -> None:
        """Should get pool by address."""
        from sugar.contracts.lp_sugar import LpSugar

        mock_checksum.return_value = "0xcontract"
        mock_load_abi.return_value = []

        mock_provider = MagicMock()
        mock_contract = MagicMock()
        mock_provider.web3.eth.contract.return_value = mock_contract
        mock_data = ("0xpool1",)
        mock_contract.functions.byAddress.return_value.call.return_value = mock_data

        lp = LpSugar(mock_provider, "0xcontract", ())
        result = lp.by_address("0xpool1")

        assert result == mock_data


class TestVeSugar:
    """Test VeSugar contract wrapper."""

    @patch("sugar.contracts.base.load_abi")
    @patch("sugar.contracts.base.Web3.to_checksum_address")
    def test_all(
        self, mock_checksum: MagicMock, mock_load_abi: MagicMock
    ) -> None:
        """Should call all function with limit and id."""
        from sugar.contracts.ve_sugar import VeSugar

        mock_checksum.return_value = "0xcontract"
        mock_load_abi.return_value = []

        mock_provider = MagicMock()
        mock_contract = MagicMock()
        mock_provider.web3.eth.contract.return_value = mock_contract
        mock_data = [(1, "0xowner")]
        mock_contract.functions.all.return_value.call.return_value = mock_data

        ve = VeSugar(mock_provider, "0xcontract")
        result = ve.all(limit=100, offset=1)

        assert result == mock_data

    @patch("sugar.contracts.base.load_abi")
    @patch("sugar.contracts.base.Web3.to_checksum_address")
    def test_by_account(
        self, mock_checksum: MagicMock, mock_load_abi: MagicMock
    ) -> None:
        """Should get veNFTs by account."""
        from sugar.contracts.ve_sugar import VeSugar

        mock_checksum.return_value = "0xcontract"
        mock_load_abi.return_value = []

        mock_provider = MagicMock()
        mock_contract = MagicMock()
        mock_provider.web3.eth.contract.return_value = mock_contract
        mock_data = [(1,), (2,)]
        mock_contract.functions.byAccount.return_value.call.return_value = mock_data

        ve = VeSugar(mock_provider, "0xcontract")
        result = ve.by_account("0xaccount")

        assert result == mock_data

    @patch("sugar.contracts.base.load_abi")
    @patch("sugar.contracts.base.Web3.to_checksum_address")
    def test_all_paginated_aborts_on_persistent_rpc_failure(
        self, mock_checksum: MagicMock, mock_load_abi: MagicMock
    ) -> None:
        """_paginate_by_id must not loop forever when every call fails."""
        import pytest

        from sugar.contracts.ve_sugar import VeSugar
        from sugar.core.exceptions import PaginationError

        mock_checksum.return_value = "0xcontract"
        mock_load_abi.return_value = []

        mock_provider = MagicMock()
        mock_contract = MagicMock()
        mock_provider.web3.eth.contract.return_value = mock_contract
        mock_contract.functions.all.return_value.call.side_effect = Exception("RPC down")

        ve = VeSugar(mock_provider, "0xcontract")
        with pytest.raises(PaginationError):
            ve.all_paginated()

    @patch("sugar.contracts.base.load_abi")
    @patch("sugar.contracts.base.Web3.to_checksum_address")
    def test_by_id(
        self, mock_checksum: MagicMock, mock_load_abi: MagicMock
    ) -> None:
        """Should get veNFT by ID."""
        from sugar.contracts.ve_sugar import VeSugar

        mock_checksum.return_value = "0xcontract"
        mock_load_abi.return_value = []

        mock_provider = MagicMock()
        mock_contract = MagicMock()
        mock_provider.web3.eth.contract.return_value = mock_contract
        mock_data = (1, "0xowner")
        mock_contract.functions.byId.return_value.call.return_value = mock_data

        ve = VeSugar(mock_provider, "0xcontract")
        result = ve.by_id(1)

        assert result == mock_data


class TestRelaySugar:
    """Test RelaySugar contract wrapper."""

    @patch("sugar.contracts.base.load_abi")
    @patch("sugar.contracts.base.Web3.to_checksum_address")
    def test_all(
        self, mock_checksum: MagicMock, mock_load_abi: MagicMock
    ) -> None:
        """Should call all function."""
        from sugar.contracts.relay_sugar import RelaySugar

        mock_checksum.return_value = "0xcontract"
        mock_load_abi.return_value = []

        mock_provider = MagicMock()
        mock_contract = MagicMock()
        mock_provider.web3.eth.contract.return_value = mock_contract
        mock_data = [(1, "0xrelay", "name")]
        mock_contract.functions.all.return_value.call.return_value = mock_data

        relay = RelaySugar(mock_provider, "0xcontract")
        result = relay.all()

        assert result == mock_data


class TestRewardsSugar:
    """Test RewardsSugar contract wrapper."""

    @patch("sugar.contracts.base.load_abi")
    @patch("sugar.contracts.base.Web3.to_checksum_address")
    def test_epochs_latest(
        self, mock_checksum: MagicMock, mock_load_abi: MagicMock
    ) -> None:
        """Should call epochsLatest function."""
        from sugar.contracts.rewards_sugar import RewardsSugar

        mock_checksum.return_value = "0xcontract"
        mock_load_abi.return_value = []

        mock_provider = MagicMock()
        mock_contract = MagicMock()
        mock_provider.web3.eth.contract.return_value = mock_contract
        mock_data = [(1704067200, "0xpool")]
        mock_contract.functions.epochsLatest.return_value.call.return_value = mock_data

        rewards = RewardsSugar(mock_provider, "0xcontract")
        result = rewards.epochs_latest(limit=100, offset=0)

        assert result == mock_data

    @patch("sugar.contracts.base.load_abi")
    @patch("sugar.contracts.base.Web3.to_checksum_address")
    def test_epochs_by_address(
        self, mock_checksum: MagicMock, mock_load_abi: MagicMock
    ) -> None:
        """Should get epochs by pool address."""
        from sugar.contracts.rewards_sugar import RewardsSugar

        mock_checksum.return_value = "0xcontract"
        mock_load_abi.return_value = []

        mock_provider = MagicMock()
        mock_contract = MagicMock()
        mock_provider.web3.eth.contract.return_value = mock_contract
        mock_data = [(1704067200, "0xpool")]
        mock_contract.functions.epochsByAddress.return_value.call.return_value = mock_data

        rewards = RewardsSugar(mock_provider, "0xcontract")
        result = rewards.epochs_by_address(pool_address="0xpool", limit=100, offset=0)

        assert result == mock_data

    @patch("sugar.contracts.base.load_abi")
    @patch("sugar.contracts.base.Web3.to_checksum_address")
    def test_rewards(
        self, mock_checksum: MagicMock, mock_load_abi: MagicMock
    ) -> None:
        """Should get rewards for veNFT."""
        from sugar.contracts.rewards_sugar import RewardsSugar

        mock_checksum.return_value = "0xcontract"
        mock_load_abi.return_value = []

        mock_provider = MagicMock()
        mock_contract = MagicMock()
        mock_provider.web3.eth.contract.return_value = mock_contract
        mock_data = [("0xtoken", 1000)]
        mock_contract.functions.rewards.return_value.call.return_value = mock_data

        rewards = RewardsSugar(mock_provider, "0xcontract")
        result = rewards.rewards(limit=100, offset=0, venft_id=1)

        assert result == mock_data


class TestSpotPriceOracle:
    """Test SpotPriceOracle contract wrapper."""

    @patch("sugar.contracts.base.load_abi")
    @patch("sugar.contracts.base.Web3.to_checksum_address")
    def test_get_rate(
        self, mock_checksum: MagicMock, mock_load_abi: MagicMock
    ) -> None:
        """Should get rate between tokens."""
        from sugar.contracts.price_oracle import SpotPriceOracle

        mock_checksum.return_value = "0xcontract"
        mock_load_abi.return_value = []

        mock_provider = MagicMock()
        mock_contract = MagicMock()
        mock_provider.web3.eth.contract.return_value = mock_contract
        mock_contract.functions.getRate.return_value.call.return_value = 2000 * 10**18

        oracle = SpotPriceOracle(mock_provider, "0xcontract", ())
        rate = oracle.get_rate("0xweth", "0xusdc", use_wrappers=True)

        # get_rate converts from wei to Decimal
        from decimal import Decimal
        assert rate == Decimal("2000")

    @patch("sugar.contracts.base.load_abi")
    @patch("sugar.contracts.base.Web3.to_checksum_address")
    def test_get_rate_to_eth(
        self, mock_checksum: MagicMock, mock_load_abi: MagicMock
    ) -> None:
        """Should get rate to ETH."""
        from sugar.contracts.price_oracle import SpotPriceOracle

        mock_checksum.return_value = "0xcontract"
        mock_load_abi.return_value = []

        mock_provider = MagicMock()
        mock_contract = MagicMock()
        mock_provider.web3.eth.contract.return_value = mock_contract
        mock_contract.functions.getRateToEth.return_value.call.return_value = 10**18

        oracle = SpotPriceOracle(mock_provider, "0xcontract", ())
        rate = oracle.get_rate_to_eth("0xusdc", use_wrappers=True)

        # get_rate_to_eth converts from wei to Decimal
        from decimal import Decimal
        assert rate == Decimal("1")

    @patch("sugar.contracts.base.load_abi")
    @patch("sugar.contracts.base.Web3.to_checksum_address")
    def test_get_many_rates_to_eth(
        self, mock_checksum: MagicMock, mock_load_abi: MagicMock
    ) -> None:
        """Should get multiple rates to ETH."""
        from sugar.contracts.price_oracle import SpotPriceOracle

        mock_checksum.return_value = "0xcontract"
        mock_load_abi.return_value = []

        mock_provider = MagicMock()
        mock_contract = MagicMock()
        mock_provider.web3.eth.contract.return_value = mock_contract
        mock_contract.functions.getManyRatesToEthWithCustomConnectors.return_value.call.return_value = [
            10**18,
            2000 * 10**18,
        ]

        oracle = SpotPriceOracle(mock_provider, "0xcontract", ("0xconnector",))
        rates = oracle.get_many_rates_to_eth(["0xusdc", "0xweth"])

        assert len(rates) == 2


class TestBaseContractProgressReporting:
    """Test BaseContract RPC progress reporting."""

    def _make_lp(self):
        """Create a minimal LpSugar instance with a named provider."""
        from sugar.contracts.base import set_progress_callback
        from sugar.contracts.lp_sugar import LpSugar

        set_progress_callback(None)  # ensure clean state

        with patch("sugar.contracts.base.load_abi") as mock_load_abi, \
             patch("sugar.contracts.base.Web3.to_checksum_address") as mock_checksum:
            mock_load_abi.return_value = []
            mock_checksum.return_value = "0xcontract"

            mock_provider = MagicMock()
            mock_provider.config.name = "TestChain"
            mock_contract = MagicMock()
            mock_provider.web3.eth.contract.return_value = mock_contract
            mock_contract.functions.count.return_value.call.return_value = 0

            return LpSugar(mock_provider, "0xcontract", ()), mock_contract

    def test_logs_rpc_call_when_no_callback(self, caplog: Any) -> None:
        """Should log at INFO when no callback is registered."""
        import logging

        from sugar.contracts.base import set_progress_callback

        set_progress_callback(None)
        lp, mock_contract = self._make_lp()
        with caplog.at_level(logging.INFO, logger="sugar.contracts.base"):
            lp.count()

        assert "RPC:" in caplog.text
        assert "TestChain" in caplog.text
        assert "count" in caplog.text

    def test_calls_callback_instead_of_printing(self, capsys: Any) -> None:
        """Should call callback and NOT print when a callback is registered."""
        from sugar.contracts.base import set_progress_callback
        from sugar.contracts.lp_sugar import LpSugar

        recorded: list[tuple] = []

        def my_callback(chain, sugar_type, method, offset):
            recorded.append((chain, sugar_type, method, offset))

        with patch("sugar.contracts.base.load_abi") as mock_load_abi, \
             patch("sugar.contracts.base.Web3.to_checksum_address") as mock_checksum:
            mock_load_abi.return_value = []
            mock_checksum.return_value = "0xcontract"

            mock_provider = MagicMock()
            mock_provider.config.name = "TestChain"
            mock_contract = MagicMock()
            mock_provider.web3.eth.contract.return_value = mock_contract
            mock_contract.functions.count.return_value.call.return_value = 0

            lp = LpSugar(mock_provider, "0xcontract", ())

        set_progress_callback(my_callback)
        try:
            lp.count()

            captured = capsys.readouterr()
            assert captured.out == ""
            assert len(recorded) == 1
            assert recorded[0][0] == "TestChain"
            assert recorded[0][2] == "count"
        finally:
            set_progress_callback(None)

    def test_set_and_get_progress_callback(self) -> None:
        """set_progress_callback / get_progress_callback should round-trip."""
        from sugar.contracts.base import get_progress_callback, set_progress_callback

        cb = lambda *a: None
        set_progress_callback(cb)
        try:
            assert get_progress_callback() is cb
        finally:
            set_progress_callback(None)

        assert get_progress_callback() is None

    def test_logs_offset_when_provided(self, caplog: Any) -> None:
        """Progress output should include the offset for paginated calls."""
        import logging

        from sugar.contracts.base import set_progress_callback

        set_progress_callback(None)
        lp, mock_contract = self._make_lp()
        # _report_progress is also called in _paginate; trigger it directly
        mock_contract.functions.all.return_value.call.return_value = []
        with caplog.at_level(logging.INFO, logger="sugar.contracts.base"):
            lp._paginate("all", limit=100, start_offset=50)

        assert "offset=50" in caplog.text
