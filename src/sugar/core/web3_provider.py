"""Web3 connection management for Sugar Python library."""

from __future__ import annotations

import logging
import os
import dotenv
from web3 import Web3
from web3.contract import Contract

from sugar.config.chains import ChainConfig
from sugar.core.exceptions import RpcConnectionError

logger = logging.getLogger(__name__)


class Web3Provider:
    """Manages Web3 connections for different chains."""

    def __init__(self, chain_config: ChainConfig) -> None:
        """
        Initialize Web3 provider for a specific chain.

        Args:
            chain_config: Configuration for the target chain.

        Raises:
            RpcConnectionError: If connection to the RPC endpoint fails.
        """
        dotenv.load_dotenv()
        self._config = chain_config
        self._web3: Web3 | None = None

    @property
    def config(self) -> ChainConfig:
        """Get the chain configuration."""
        return self._config

    @property
    def web3(self) -> Web3:
        """Get the Web3 instance, initializing if needed."""
        if self._web3 is None:
            self._web3 = self._create_connection()
        return self._web3

    def _create_connection(self) -> Web3:
        """Create and validate Web3 connection."""
        rpc_url = os.environ.get(self._config.rpc_env_var)
        if not rpc_url:
            raise RpcConnectionError(
                self._config.name,
                f"Environment variable {self._config.rpc_env_var} not set",
            )

        web3 = Web3(Web3.HTTPProvider(rpc_url))

        if not web3.is_connected():
            raise RpcConnectionError(
                self._config.name,
                f"Failed to connect to RPC at {rpc_url}",
            )

        logger.info(f"Connected to {self._config.name} (chain ID: {self._config.chain_id.value})")
        return web3

    @property
    def block_number(self) -> int:
        """Get the current block number."""
        return self.web3.eth.block_number

    def create_contract(self, address: str, abi: list[dict]) -> Contract:
        """
        Create a contract instance.

        Args:
            address: Contract address.
            abi: Contract ABI.

        Returns:
            Web3 contract instance.
        """
        return self.web3.eth.contract(
            address=Web3.to_checksum_address(address),
            abi=abi,
        )

    def from_wei(self, value: int, unit: str = "ether") -> float:
        """Convert wei to specified unit."""
        return float(self.web3.from_wei(value, unit))

    def to_wei(self, value: float | int, unit: str = "ether") -> int:
        """Convert specified unit to wei."""
        return self.web3.to_wei(value, unit)
