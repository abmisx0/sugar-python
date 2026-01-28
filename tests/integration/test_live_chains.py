"""Integration tests for live chain connectivity.

These tests require RPC endpoints to be configured in environment variables.
Run with: pytest tests/integration/ -m integration

To run: pytest -m integration
"""

from __future__ import annotations

import os

import pandas as pd
import pytest

from sugar import SugarClient, ChainId


# Skip all integration tests if no RPC configured
pytestmark = pytest.mark.integration


def rpc_available(chain: ChainId) -> bool:
    """Check if RPC is available for chain."""
    env_vars = {
        ChainId.BASE: "RPC_LINK_BASE",
        ChainId.OPTIMISM: "RPC_LINK_OP",
        ChainId.MODE: "RPC_LINK_MODE",
    }
    env_var = env_vars.get(chain)
    return env_var is not None and os.getenv(env_var) is not None


@pytest.fixture
def base_client() -> SugarClient | None:
    """Create Base client if RPC available."""
    if not rpc_available(ChainId.BASE):
        pytest.skip("BASE RPC not configured")
    return SugarClient(ChainId.BASE)


@pytest.fixture
def op_client() -> SugarClient | None:
    """Create Optimism client if RPC available."""
    if not rpc_available(ChainId.OPTIMISM):
        pytest.skip("OP RPC not configured")
    return SugarClient(ChainId.OPTIMISM)


class TestBaseChain:
    """Integration tests for Base chain."""

    def test_connection(self, base_client: SugarClient) -> None:
        """Should connect to Base chain."""
        assert base_client.chain == ChainId.BASE
        assert base_client.block_number > 0

    def test_lp_count(self, base_client: SugarClient) -> None:
        """Should get LP count."""
        count = base_client.lp.count()
        assert count > 0

    def test_lp_all_single_page(self, base_client: SugarClient) -> None:
        """Should fetch single page of LP data."""
        data = base_client.lp.all(limit=10, offset=0)
        assert len(data) == 10

    def test_tokens_fetch(self, base_client: SugarClient) -> None:
        """Should fetch tokens."""
        tokens = base_client.get_tokens()
        assert isinstance(tokens, pd.DataFrame)
        assert len(tokens) > 0

    def test_pools_fetch(self, base_client: SugarClient) -> None:
        """Should fetch pools."""
        pools = base_client.get_pools()
        assert isinstance(pools, pd.DataFrame)
        assert len(pools) > 0

    def test_ve_available(self, base_client: SugarClient) -> None:
        """Base should have VE Sugar."""
        assert base_client.has_ve()

    def test_ve_fetch(self, base_client: SugarClient) -> None:
        """Should fetch veNFT data."""
        # Fetch small sample
        data = base_client.ve.all(limit=10, _id=0)
        assert len(data) > 0

    def test_relay_available(self, base_client: SugarClient) -> None:
        """Base should have Relay Sugar."""
        assert base_client.has_relay()

    def test_relay_fetch(self, base_client: SugarClient) -> None:
        """Should fetch relay data."""
        relays = base_client.get_relays()
        assert isinstance(relays, pd.DataFrame)

    def test_rewards_available(self, base_client: SugarClient) -> None:
        """Base should have Rewards Sugar."""
        assert base_client.has_rewards()

    def test_epochs_fetch(self, base_client: SugarClient) -> None:
        """Should fetch epoch data."""
        # Fetch small sample
        data = base_client.rewards.epochs_latest(limit=10, offset=0)
        assert len(data) > 0

    def test_price_oracle_available(self, base_client: SugarClient) -> None:
        """Base should have price oracle."""
        assert base_client.has_price_oracle()


class TestOptimismChain:
    """Integration tests for Optimism chain."""

    def test_connection(self, op_client: SugarClient) -> None:
        """Should connect to Optimism chain."""
        assert op_client.chain == ChainId.OPTIMISM
        assert op_client.block_number > 0

    def test_lp_count(self, op_client: SugarClient) -> None:
        """Should get LP count."""
        count = op_client.lp.count()
        assert count > 0

    def test_ve_available(self, op_client: SugarClient) -> None:
        """Optimism should have VE Sugar."""
        assert op_client.has_ve()

    def test_relay_available(self, op_client: SugarClient) -> None:
        """Optimism should have Relay Sugar."""
        assert op_client.has_relay()


class TestCombinedData:
    """Integration tests for combined data methods."""

    @pytest.mark.slow
    def test_pools_with_rewards(self, base_client: SugarClient) -> None:
        """Should fetch combined pools with rewards.

        This test may be slow as it fetches all pool and reward data.
        """
        combined = base_client.get_pools_with_rewards()
        assert isinstance(combined, pd.DataFrame)
        assert len(combined) > 0


class TestPriceProvider:
    """Integration tests for price provider."""

    def test_price_fetch(self, base_client: SugarClient) -> None:
        """Should fetch token price."""
        # USDC on Base
        usdc_address = "0x833589fcd6edb6e08f4c7c32d4f71b54bda02913"
        price = base_client.prices.get_price_usd(usdc_address)

        # USDC should be close to $1
        if price is not None:
            assert 0.9 < float(price) < 1.1

    def test_batch_price_fetch(self, base_client: SugarClient) -> None:
        """Should fetch multiple token prices."""
        # USDC and WETH on Base
        addresses = [
            "0x833589fcd6edb6e08f4c7c32d4f71b54bda02913",  # USDC
            "0x4200000000000000000000000000000000000006",  # WETH
        ]
        prices = base_client.prices.get_prices_usd(addresses)

        assert len(prices) > 0


class TestExportFunctionality:
    """Integration tests for export functionality."""

    def test_export_tokens(self, base_client: SugarClient, tmp_path) -> None:
        """Should export tokens to file."""
        # Create client with temp export dir
        client = SugarClient(ChainId.BASE, export_dir=tmp_path)
        path = client.export_tokens()

        assert path.exists()
        df = pd.read_csv(path)
        assert len(df) > 0
