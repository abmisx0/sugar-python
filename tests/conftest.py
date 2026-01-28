"""Pytest configuration and fixtures for Sugar tests."""

from __future__ import annotations

from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from sugar.config.chains import CHAIN_CONFIGS, ChainConfig, ChainId


@pytest.fixture
def base_config() -> ChainConfig:
    """Get Base chain configuration."""
    return CHAIN_CONFIGS[ChainId.BASE]


@pytest.fixture
def op_config() -> ChainConfig:
    """Get Optimism chain configuration."""
    return CHAIN_CONFIGS[ChainId.OPTIMISM]


@pytest.fixture
def mock_web3() -> MagicMock:
    """Create mock Web3 instance."""
    mock = MagicMock()
    mock.eth.block_number = 12345678
    mock.is_connected.return_value = True
    return mock


@pytest.fixture
def mock_contract() -> MagicMock:
    """Create mock contract instance."""
    return MagicMock()


@pytest.fixture
def sample_lp_tuple() -> tuple[Any, ...]:
    """Sample LP data tuple from contract."""
    return (
        "0x1234567890123456789012345678901234567890",  # lp
        "symbol",  # symbol
        1,  # decimals
        True,  # stable
        10000000000000000000,  # total_supply (10 tokens)
        "0xtoken0",  # token0
        100000000000000000000,  # reserve0 (100)
        100000000000000000000,  # claimable0
        "0xtoken1",  # token1
        200000000000000000000,  # reserve1 (200)
        200000000000000000000,  # claimable1
        "0xgauge",  # gauge
        10000000000000000000,  # gauge_total_supply
        1000000000000000000,  # gauge_alive
        500000000000000000000,  # fee
        "0xbribe",  # bribe
        "0xfactory",  # factory
        1000000000000000000000,  # emissions
        10000000000000000000,  # emissions_token
        "0xpool_fee",  # pool_fee
        "0xunstaked_fee",  # unstaked_fee
        1000,  # pool_fee_percentage
        0,  # type (V2)
        168,  # tick
        5000000000000000000000,  # sqrt_ratio
    )


@pytest.fixture
def sample_token_tuple() -> tuple[Any, ...]:
    """Sample token data tuple from contract."""
    return (
        "0xtoken_address",  # token_address
        "WETH",  # symbol
        18,  # decimals
        "Wrapped Ether",  # name
        True,  # listed
        1000000000000000000000000,  # total_supply
    )


@pytest.fixture
def sample_venft_tuple() -> tuple[Any, ...]:
    """Sample veNFT data tuple from contract."""
    return (
        1,  # id
        "0xowner_address",  # account
        18,  # decimals
        1000000000000000000000,  # amount
        1704067200,  # voting_amount
        1800000000,  # rebase_amount
        1735689600,  # expires_at (timestamp)
        1704067200,  # voted_at
        (  # votes array
            (
                "0xpool1",
                1000000000000000000000,
            ),
        ),
        False,  # reset
        True,  # activated
        1704067200,  # activated_at
        True,  # active_permanent
        1704067200,  # active_permanent_at
        False,  # governance_voted
        1704067200,  # governance_voted_at
    )


@pytest.fixture
def sample_relay_tuple() -> tuple[Any, ...]:
    """Sample relay data tuple from contract."""
    return (
        1,  # venft_id
        "0xrelay_address",  # relay_address
        "Test Relay",  # name
        "relay",  # relay_type
        True,  # active
        "0xmanager",  # manager
        (  # used_votes array
            (
                "0xpool1",
                1000000000000000000000,
            ),
        ),
    )


@pytest.fixture
def sample_epoch_tuple() -> tuple[Any, ...]:
    """Sample epoch data tuple from contract."""
    return (
        1704067200,  # ts
        "0xpool_address",  # lp
        1000000000000000000000,  # votes
        1000000000000000000,  # emissions
        (  # incentives array (voting incentives)
            (
                "0xtoken1",
                1000000000000000000,
            ),
        ),
        (  # fees array
            (
                "0xtoken2",
                500000000000000000,
            ),
        ),
    )


@pytest.fixture
def mock_env_vars(monkeypatch: pytest.MonkeyPatch) -> None:
    """Set up mock environment variables."""
    monkeypatch.setenv("RPC_LINK_BASE", "https://mock-base-rpc.example.com")
    monkeypatch.setenv("RPC_LINK_OP", "https://mock-op-rpc.example.com")
    monkeypatch.setenv("RPC_LINK_MODE", "https://mock-mode-rpc.example.com")
