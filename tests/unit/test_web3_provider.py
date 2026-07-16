"""Tests for Web3Provider."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from sugar.config.chains import CHAIN_CONFIGS, ChainId
from sugar.core.exceptions import RpcConnectionError
from sugar.core.web3_provider import Web3Provider


class TestWeb3ProviderInit:
    """Test Web3Provider initialization."""

    def test_raises_when_rpc_env_var_missing(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Should raise RpcConnectionError when RPC env var is not set."""
        monkeypatch.delenv("RPC_LINK_BASE", raising=False)
        config = CHAIN_CONFIGS[ChainId.BASE]

        # Suppress dotenv so it cannot reload the var from a local .env file
        with patch("sugar.core.web3_provider.dotenv.load_dotenv"):
            provider = Web3Provider(config)

        with pytest.raises(RpcConnectionError):
            _ = provider.web3

    @patch("sugar.core.web3_provider.Web3")
    def test_creates_connection_with_env_var(
        self, mock_web3_class: MagicMock, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Should connect successfully when RPC env var is set."""
        monkeypatch.setenv("RPC_LINK_BASE", "https://mock-base-rpc.example.com")
        mock_web3 = MagicMock()
        mock_web3.is_connected.return_value = True
        mock_web3_class.return_value = mock_web3

        config = CHAIN_CONFIGS[ChainId.BASE]
        provider = Web3Provider(config)

        assert provider.web3 is mock_web3

    @patch("sugar.core.web3_provider.Web3")
    def test_uses_injected_rpc_url_when_env_missing(
        self, mock_web3_class: MagicMock, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Should use an explicit rpc_url even when the env var is unset."""
        monkeypatch.delenv("RPC_LINK_BASE", raising=False)
        mock_web3 = MagicMock()
        mock_web3.is_connected.return_value = True
        mock_web3_class.return_value = mock_web3

        config = CHAIN_CONFIGS[ChainId.BASE]
        with patch("sugar.core.web3_provider.dotenv.load_dotenv"):
            provider = Web3Provider(config, rpc_url="https://injected-rpc.example.com")

        assert provider.web3 is mock_web3
        mock_web3_class.HTTPProvider.assert_called_once_with("https://injected-rpc.example.com")

    @patch("sugar.core.web3_provider.Web3")
    def test_injected_rpc_url_takes_precedence_over_env(
        self, mock_web3_class: MagicMock, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """An explicit rpc_url should win over the env var."""
        monkeypatch.setenv("RPC_LINK_BASE", "https://env-rpc.example.com")
        mock_web3 = MagicMock()
        mock_web3.is_connected.return_value = True
        mock_web3_class.return_value = mock_web3

        config = CHAIN_CONFIGS[ChainId.BASE]
        provider = Web3Provider(config, rpc_url="https://injected-rpc.example.com")

        _ = provider.web3
        mock_web3_class.HTTPProvider.assert_called_once_with("https://injected-rpc.example.com")

    @patch("sugar.core.web3_provider.Web3")
    def test_raises_when_not_connected(
        self, mock_web3_class: MagicMock, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Should raise RpcConnectionError when Web3 cannot connect."""
        monkeypatch.setenv("RPC_LINK_BASE", "https://dead-rpc.example.com")
        mock_web3 = MagicMock()
        mock_web3.is_connected.return_value = False
        mock_web3_class.return_value = mock_web3

        config = CHAIN_CONFIGS[ChainId.BASE]
        provider = Web3Provider(config)

        with pytest.raises(RpcConnectionError):
            _ = provider.web3

    @patch("sugar.core.web3_provider.Web3")
    def test_connection_is_reused(
        self, mock_web3_class: MagicMock, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Should reuse the same Web3 connection on repeated access."""
        monkeypatch.setenv("RPC_LINK_BASE", "https://mock-base-rpc.example.com")
        mock_web3 = MagicMock()
        mock_web3.is_connected.return_value = True
        mock_web3_class.return_value = mock_web3

        config = CHAIN_CONFIGS[ChainId.BASE]
        provider = Web3Provider(config)

        web3_a = provider.web3
        web3_b = provider.web3

        assert web3_a is web3_b
        mock_web3_class.assert_called_once()


class TestWeb3ProviderProperties:
    """Test Web3Provider properties."""

    @patch("sugar.core.web3_provider.Web3")
    def test_block_number(
        self, mock_web3_class: MagicMock, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Should return the current block number from the node."""
        monkeypatch.setenv("RPC_LINK_BASE", "https://mock-base-rpc.example.com")
        mock_web3 = MagicMock()
        mock_web3.is_connected.return_value = True
        mock_web3.eth.block_number = 99_999_999
        mock_web3_class.return_value = mock_web3

        config = CHAIN_CONFIGS[ChainId.BASE]
        provider = Web3Provider(config)

        assert provider.block_number == 99_999_999

    @patch("sugar.core.web3_provider.Web3")
    def test_config_property(
        self, mock_web3_class: MagicMock, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Should expose the chain config it was initialised with."""
        monkeypatch.setenv("RPC_LINK_BASE", "https://mock-base-rpc.example.com")
        mock_web3_class.return_value = MagicMock(is_connected=lambda: True)

        config = CHAIN_CONFIGS[ChainId.BASE]
        provider = Web3Provider(config)

        assert provider.config is config
        assert provider.config.name == "Base"
