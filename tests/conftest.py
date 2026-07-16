"""Pytest configuration and fixtures for Sugar tests."""

from __future__ import annotations

from typing import Any
from unittest.mock import MagicMock

import pytest

from sugar.config.chains import CHAIN_CONFIGS, ChainConfig, ChainId


@pytest.fixture(autouse=True)
def _isolate_snapshots(tmp_path: Any, monkeypatch: pytest.MonkeyPatch) -> None:
    """Keep auto-snapshots out of the repo by redirecting them to tmp."""
    monkeypatch.setenv("SUGAR_SNAPSHOT_DIR", str(tmp_path / "sugar-snapshots"))


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
def mock_env_vars(monkeypatch: pytest.MonkeyPatch) -> None:
    """Set up mock environment variables."""
    monkeypatch.setenv("RPC_LINK_BASE", "https://mock-base-rpc.example.com")
    monkeypatch.setenv("RPC_LINK_OP", "https://mock-op-rpc.example.com")
    monkeypatch.setenv("RPC_LINK_MODE", "https://mock-mode-rpc.example.com")
