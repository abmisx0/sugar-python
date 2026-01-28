"""Spot Price Oracle contract wrapper."""

from __future__ import annotations

import logging
from decimal import Decimal
from typing import TYPE_CHECKING

from sugar.contracts.base import BaseContract

if TYPE_CHECKING:
    from sugar.core.web3_provider import Web3Provider

logger = logging.getLogger(__name__)


class SpotPriceOracle(BaseContract):
    """
    Wrapper for the Velodrome Spot Price Aggregator contract.

    Provides methods to query token prices from on-chain DEX liquidity.

    IMPORTANT: This oracle should only be used off-chain to avoid
    price manipulation within transactions.
    """

    ABI_NAME = "price_oracle"
    SUGAR_TYPE = "PriceOracle"

    def __init__(
        self,
        provider: Web3Provider,
        address: str,
        connectors: tuple[str, ...] = (),
    ) -> None:
        """
        Initialize Spot Price Oracle contract wrapper.

        Args:
            provider: Web3Provider instance.
            address: Oracle contract address.
            connectors: Connector token addresses for routing.
        """
        super().__init__(provider, address)
        self._connectors = connectors

    @property
    def connectors(self) -> tuple[str, ...]:
        """Connector token addresses."""
        return self._connectors

    def get_rate(
        self,
        src_token: str,
        dst_token: str,
        use_wrappers: bool = True,
    ) -> Decimal:
        """
        Get exchange rate between two tokens.

        Args:
            src_token: Source token address.
            dst_token: Destination token address.
            use_wrappers: Whether to use wrapper contracts for wrapped tokens.

        Returns:
            Exchange rate as Decimal (1 src_token = X dst_token).
        """
        rate = self._call("getRate", src_token, dst_token, use_wrappers)
        return Decimal(rate) / Decimal(10**18)

    def get_rate_with_threshold(
        self,
        src_token: str,
        dst_token: str,
        use_wrappers: bool = True,
        threshold: int = 0,
    ) -> Decimal:
        """
        Get exchange rate with liquidity threshold filter.

        Args:
            src_token: Source token address.
            dst_token: Destination token address.
            use_wrappers: Whether to use wrapper contracts.
            threshold: Minimum liquidity threshold.

        Returns:
            Exchange rate as Decimal.
        """
        rate = self._call("getRateWithThreshold", src_token, dst_token, use_wrappers, threshold)
        return Decimal(rate) / Decimal(10**18)

    def get_rate_to_eth(
        self,
        src_token: str,
        use_wrappers: bool = True,
    ) -> Decimal:
        """
        Get exchange rate to ETH/native token.

        Args:
            src_token: Source token address.
            use_wrappers: Whether to use wrapper contracts.

        Returns:
            Exchange rate as Decimal (1 src_token = X ETH).
        """
        rate = self._call("getRateToEth", src_token, use_wrappers)
        return Decimal(rate) / Decimal(10**18)

    def get_rate_to_eth_with_threshold(
        self,
        src_token: str,
        use_wrappers: bool = True,
        threshold: int = 0,
    ) -> Decimal:
        """
        Get exchange rate to ETH with liquidity threshold filter.

        Args:
            src_token: Source token address.
            use_wrappers: Whether to use wrapper contracts.
            threshold: Minimum liquidity threshold.

        Returns:
            Exchange rate as Decimal.
        """
        rate = self._call("getRateToEthWithThreshold", src_token, use_wrappers, threshold)
        return Decimal(rate) / Decimal(10**18)

    def get_rate_to_eth_with_connectors(
        self,
        src_token: str,
        use_wrappers: bool = True,
        custom_connectors: tuple[str, ...] | None = None,
        threshold: int = 0,
    ) -> Decimal:
        """
        Get exchange rate to ETH using custom connector tokens.

        Args:
            src_token: Source token address.
            use_wrappers: Whether to use wrapper contracts.
            custom_connectors: Custom connector tokens (uses instance connectors if None).
            threshold: Minimum liquidity threshold.

        Returns:
            Exchange rate as Decimal.
        """
        if custom_connectors is None:
            custom_connectors = self._connectors

        rate = self._call(
            "getRateToEthWithCustomConnectors",
            src_token,
            use_wrappers,
            list(custom_connectors),
            threshold,
        )
        return Decimal(rate) / Decimal(10**18)

    def get_many_rates_to_eth(
        self,
        src_tokens: list[str],
        use_wrappers: bool = True,
        custom_connectors: tuple[str, ...] | None = None,
        threshold: int = 0,
    ) -> list[Decimal]:
        """
        Get exchange rates to ETH for multiple tokens in a single call.

        Args:
            src_tokens: List of source token addresses.
            use_wrappers: Whether to use wrapper contracts.
            custom_connectors: Custom connector tokens (uses instance connectors if None).
            threshold: Minimum liquidity threshold.

        Returns:
            List of exchange rates as Decimals.
        """
        if custom_connectors is None:
            custom_connectors = self._connectors

        rates = self._call(
            "getManyRatesToEthWithCustomConnectors",
            src_tokens,
            use_wrappers,
            list(custom_connectors),
            threshold,
        )
        return [Decimal(r) / Decimal(10**18) for r in rates]

    def get_rate_with_connectors(
        self,
        src_token: str,
        dst_token: str,
        use_wrappers: bool = True,
        custom_connectors: tuple[str, ...] | None = None,
        threshold: int = 0,
    ) -> Decimal:
        """
        Get exchange rate using custom connector tokens.

        Args:
            src_token: Source token address.
            dst_token: Destination token address.
            use_wrappers: Whether to use wrapper contracts.
            custom_connectors: Custom connector tokens.
            threshold: Minimum liquidity threshold.

        Returns:
            Exchange rate as Decimal.
        """
        if custom_connectors is None:
            custom_connectors = self._connectors

        rate = self._call(
            "getRateWithCustomConnectors",
            src_token,
            dst_token,
            use_wrappers,
            list(custom_connectors),
            threshold,
        )
        return Decimal(rate) / Decimal(10**18)
