"""Tests for contract wrappers."""

from __future__ import annotations

from typing import Any
from unittest.mock import MagicMock, patch

import pytest


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
