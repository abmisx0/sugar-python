"""Main SugarClient facade for Sugar Python library."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import TYPE_CHECKING

import pandas as pd

from sugar.config.chains import CHAIN_CONFIGS, ChainConfig, ChainId, get_chain_config
from sugar.contracts.lp_sugar import LpSugar
from sugar.contracts.price_oracle import SpotPriceOracle
from sugar.contracts.relay_sugar import RelaySugar
from sugar.contracts.rewards_sugar import RewardsSugar
from sugar.contracts.ve_sugar import VeSugar
from sugar.core.exceptions import ContractNotAvailableError
from sugar.core.web3_provider import Web3Provider
from sugar.services.data_processor import DataProcessor
from sugar.services.export import ExportService
from sugar.services.price_provider import (
    CoinGeckoPriceSource,
    DefiLlamaPriceSource,
    OraclePriceSource,
    PriceProvider,
)

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)


class SugarClient:
    """
    Main facade for interacting with Sugar Protocol contracts.

    Provides a unified interface to all Sugar contracts with automatic
    chain configuration, price fetching, and data processing.

    Example:
        >>> from sugar import SugarClient, ChainId
        >>> client = SugarClient(ChainId.BASE)
        >>> pools = client.lp.all_paginated()
        >>> client.get_pools_with_rewards()
    """

    def __init__(
        self,
        chain: ChainId | str,
        export_dir: str | Path = ".",
    ) -> None:
        """
        Initialize SugarClient for a specific chain.

        Args:
            chain: Chain identifier (ChainId enum or string like "base", "op").
            export_dir: Base directory for data exports.

        Raises:
            ValueError: If chain is not supported.
            RpcConnectionError: If RPC connection fails.
        """
        self._config = get_chain_config(chain)
        self._provider = Web3Provider(self._config)
        self._export = ExportService(export_dir)

        # Initialize LP Sugar (always available)
        self._lp = LpSugar(
            self._provider,
            self._config.lp_sugar_address,
            self._config.connectors,
        )

        # Lazy-initialized optional contracts
        self._ve: VeSugar | None = None
        self._relay: RelaySugar | None = None
        self._rewards: RewardsSugar | None = None
        self._price_oracle: SpotPriceOracle | None = None
        self._price_provider: PriceProvider | None = None
        self._data_processor: DataProcessor | None = None

        # Cached data
        self._tokens_df: pd.DataFrame | None = None

        logger.info(f"SugarClient initialized for {self._config.name}")

    @property
    def chain(self) -> ChainId:
        """Current chain ID."""
        return self._config.chain_id

    @property
    def chain_name(self) -> str:
        """Current chain name."""
        return self._config.name

    @property
    def config(self) -> ChainConfig:
        """Current chain configuration."""
        return self._config

    @property
    def block_number(self) -> int:
        """Current block number."""
        return self._provider.block_number

    @property
    def lp(self) -> LpSugar:
        """LpSugar contract - always available."""
        return self._lp

    @property
    def ve(self) -> VeSugar:
        """
        VeSugar contract.

        Raises:
            ContractNotAvailableError: If VeSugar is not deployed on this chain.
        """
        if not self._config.has_ve:
            raise ContractNotAvailableError("VeSugar", self._config.name)

        if self._ve is None:
            self._ve = VeSugar(
                self._provider,
                self._config.ve_sugar_address,  # type: ignore
            )
        return self._ve

    @property
    def relay(self) -> RelaySugar:
        """
        RelaySugar contract.

        Raises:
            ContractNotAvailableError: If RelaySugar is not deployed on this chain.
        """
        if not self._config.has_relay:
            raise ContractNotAvailableError("RelaySugar", self._config.name)

        if self._relay is None:
            self._relay = RelaySugar(
                self._provider,
                self._config.relay_sugar_address,  # type: ignore
            )
        return self._relay

    @property
    def rewards(self) -> RewardsSugar:
        """
        RewardsSugar contract.

        Raises:
            ContractNotAvailableError: If RewardsSugar is not deployed on this chain.
        """
        if not self._config.has_rewards:
            raise ContractNotAvailableError("RewardsSugar", self._config.name)

        if self._rewards is None:
            self._rewards = RewardsSugar(
                self._provider,
                self._config.rewards_sugar_address,  # type: ignore
            )
        return self._rewards

    @property
    def prices(self) -> PriceProvider:
        """Price provider with fallback chain."""
        if self._price_provider is None:
            self._price_provider = self._create_price_provider()
        return self._price_provider

    @property
    def processor(self) -> DataProcessor:
        """Data processor service."""
        if self._data_processor is None:
            self._data_processor = DataProcessor(self.prices, self._provider)
        return self._data_processor

    def has_ve(self) -> bool:
        """Check if VeSugar is available on this chain."""
        return self._config.has_ve

    def has_relay(self) -> bool:
        """Check if RelaySugar is available on this chain."""
        return self._config.has_relay

    def has_rewards(self) -> bool:
        """Check if RewardsSugar is available on this chain."""
        return self._config.has_rewards

    def has_price_oracle(self) -> bool:
        """Check if Spot Price Oracle is available on this chain."""
        return self._config.has_price_oracle

    def _create_price_provider(self) -> PriceProvider:
        """Create price provider with all available sources."""
        oracle_source = None
        coingecko_source = None
        defillama_source = None

        # Create on-chain oracle source if available
        if self._config.has_price_oracle:
            if self._price_oracle is None:
                self._price_oracle = SpotPriceOracle(
                    self._provider,
                    self._config.price_oracle_address,  # type: ignore
                    self._config.connectors,
                )

            # Get USDC address from connectors if available
            usdc_address = None
            for connector in self._config.connectors:
                # Common USDC addresses
                if connector.lower() in [
                    "0x833589fcd6edb6e08f4c7c32d4f71b54bda02913",  # Base USDC
                    "0x0b2c639c533813f4aa9d7837caf62653d097ff85",  # OP USDC
                ]:
                    usdc_address = connector
                    break

            oracle_source = OraclePriceSource(self._price_oracle, usdc_address)

        # Create CoinGecko source
        coingecko_source = CoinGeckoPriceSource(self._config.chain_id)

        # Create DefiLlama source
        defillama_source = DefiLlamaPriceSource(self._config.chain_id)

        return PriceProvider(
            oracle=oracle_source,
            coingecko=coingecko_source,
            defillama=defillama_source,
        )

    def get_tokens(
        self, listed_only: bool = True, refresh: bool = False
    ) -> pd.DataFrame:
        """
        Get token metadata.

        Args:
            listed_only: Whether to filter for listed tokens only.
            refresh: Whether to refresh cached data.

        Returns:
            DataFrame with token metadata indexed by address.
        """
        if self._tokens_df is None or refresh:
            raw_data = self._lp.tokens_paginated()
            self._tokens_df = self.processor.process_tokens(raw_data, listed_only=False)

        if listed_only:
            return self._tokens_df[self._tokens_df["listed"]]
        return self._tokens_df

    def get_pools(self, filter_type: int = 0) -> pd.DataFrame:
        """
        Get all liquidity pools.

        Args:
            filter_type: Filter type (0 = all, 1 = v2 only, 2 = CL only).

        Returns:
            DataFrame with pool data.
        """
        # Ensure tokens are loaded for symbol lookup
        tokens_df = self.get_tokens(listed_only=False)

        raw_data = self._lp.all_paginated(filter_type=filter_type)
        return self.processor.process_lp_all(raw_data, tokens_df)

    def get_ve_positions(self) -> pd.DataFrame:
        """
        Get all veNFT positions.

        Returns:
            DataFrame with veNFT data indexed by ID.

        Raises:
            ContractNotAvailableError: If VeSugar is not available.
        """
        raw_data = self.ve.all_paginated()
        return self.processor.process_ve_all(raw_data)

    def get_relays(self, filter_inactive: bool = True) -> pd.DataFrame:
        """
        Get all relay data.

        Args:
            filter_inactive: Whether to filter out inactive relays.

        Returns:
            DataFrame with relay data indexed by venft_id.

        Raises:
            ContractNotAvailableError: If RelaySugar is not available.
        """
        raw_data = self.relay.all()
        return self.processor.process_relay_all(
            raw_data, filter_inactive=filter_inactive
        )

    def get_epochs_latest(self) -> pd.DataFrame:
        """
        Get latest epoch rewards for all pools.

        Returns:
            DataFrame with epoch data.

        Raises:
            ContractNotAvailableError: If RewardsSugar is not available.
        """
        tokens_df = self.get_tokens(listed_only=False)
        # Use pool count to inform pagination limit
        pool_count = self._lp.count()
        raw_data = self.rewards.epochs_latest_paginated(max_offset=pool_count)
        return self.processor.process_epochs_latest(raw_data, tokens_df)

    def get_pools_with_rewards(self, only_with_rewards: bool = True) -> pd.DataFrame:
        """
        Get combined LP and epoch rewards data with priced fees/bribes.

        This is the main convenience method that combines:
        - LpSugar.all() pool data
        - RewardsSugar.epochsLatest() reward data
        - Priced bribes and fees in USD

        Args:
            only_with_rewards: If True (default), only include pools that have
                epoch rewards data. This is faster as it reduces the number of
                pools to process. If False, include all pools.

        Returns:
            Combined DataFrame with pool info and priced rewards.

        Raises:
            ContractNotAvailableError: If RewardsSugar is not available.
        """
        tokens_df = self.get_tokens(listed_only=True)
        lp_df = self.get_pools()
        epochs_df = self.get_epochs_latest()

        return self.processor.combine_lp_with_rewards(
            lp_df, epochs_df, tokens_df, only_with_rewards=only_with_rewards
        )

    def export_dataframe(
        self,
        df: pd.DataFrame,
        name: str,
        subdirectory: str = "data",
        include_block: bool = True,
        index: bool = True,
    ) -> Path:
        """
        Export any DataFrame to CSV with standard naming.

        This is a generalized export function for any DataFrame.

        Args:
            df: DataFrame to export.
            name: Base name for the file (e.g., "pools", "tokens").
            subdirectory: Subdirectory within export dir (default: "data").
            include_block: Whether to include block number in filename.
            index: Whether to include DataFrame index in output.

        Returns:
            Path to exported file.
        """
        chain = self._config.name.lower()
        if include_block:
            filename = f"{name}_{chain}_{self.block_number}.csv"
        else:
            filename = f"{name}_{chain}.csv"

        return self._export.to_csv(df, filename, subdirectory=subdirectory, index=index)
