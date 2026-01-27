"""LpSugar contract wrapper."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from sugar.contracts.base import BaseContract

if TYPE_CHECKING:
    from sugar.core.web3_provider import Web3Provider

logger = logging.getLogger(__name__)

# Zero address constant
ZERO_ADDRESS = "0x0000000000000000000000000000000000000000"


class LpSugar(BaseContract):
    """
    Wrapper for the LpSugar contract.

    Provides methods to query liquidity pool data, token information,
    and user positions.
    """

    ABI_NAME = "lp_sugar"

    def __init__(
        self,
        provider: Web3Provider,
        address: str,
        connectors: tuple[str, ...] = (),
    ) -> None:
        """
        Initialize LpSugar contract wrapper.

        Args:
            provider: Web3Provider instance.
            address: LpSugar contract address.
            connectors: Connector token addresses for price queries.
        """
        super().__init__(provider, address)
        self._connectors = connectors

    @property
    def connectors(self) -> tuple[str, ...]:
        """Connector token addresses."""
        return self._connectors

    def count(self) -> int:
        """
        Get total number of liquidity pools.

        Returns:
            Total pool count.
        """
        return self._call("count")

    def all(
        self,
        limit: int = 500,
        offset: int = 0,
        filter_type: int = 0,
    ) -> list[tuple]:
        """
        Fetch LP data for a single page.

        Args:
            limit: Maximum number of pools to fetch.
            offset: Starting offset.
            filter_type: Filter type (0 = all, 1 = v2 only, 2 = CL only).

        Returns:
            List of LP data tuples.
        """
        return self._call("all", limit, offset, filter_type)

    def all_paginated(
        self,
        limit: int = 500,
        filter_type: int = 0,
    ) -> list[tuple]:
        """
        Fetch all LP data with automatic pagination.

        Args:
            limit: Items per page.
            filter_type: Filter type (0 = all, 1 = v2 only, 2 = CL only).

        Returns:
            List of all LP data tuples.
        """
        return self._paginate("all", limit, extra_args=(filter_type,))

    def by_index(self, index: int) -> tuple:
        """
        Fetch LP data by index.

        Args:
            index: Pool index.

        Returns:
            LP data tuple.
        """
        return self._call("byIndex", index)

    def by_address(self, pool_address: str) -> tuple:
        """
        Fetch LP data by pool address.

        Args:
            pool_address: Pool contract address.

        Returns:
            LP data tuple.
        """
        return self._call("byAddress", pool_address)

    def tokens(
        self,
        limit: int = 1000,
        offset: int = 0,
        account: str = ZERO_ADDRESS,
        connectors: tuple[str, ...] | None = None,
    ) -> list[tuple]:
        """
        Fetch token metadata for a single page.

        Args:
            limit: Maximum number of tokens to fetch.
            offset: Starting offset.
            account: Account address for balance queries (zero address for none).
            connectors: Connector tokens (uses instance connectors if None).

        Returns:
            List of token data tuples.
        """
        if connectors is None:
            connectors = self._connectors
        return self._call("tokens", limit, offset, account, list(connectors))

    def tokens_paginated(
        self,
        limit: int = 1000,
        account: str = ZERO_ADDRESS,
        connectors: tuple[str, ...] | None = None,
    ) -> list[tuple]:
        """
        Fetch all token metadata with automatic pagination.

        Args:
            limit: Items per page.
            account: Account address for balance queries.
            connectors: Connector tokens (uses instance connectors if None).

        Returns:
            List of all token data tuples.
        """
        if connectors is None:
            connectors = self._connectors

        all_results: list[tuple] = []
        offset = 0

        while True:
            result = self.tokens(limit, offset, account, connectors)

            # Stop if only connectors returned (no new tokens)
            if len(result) == len(connectors):
                break

            all_results.extend(result)
            offset += limit
            logger.debug(f"tokens: fetched {len(result)} items, offset now {offset}")

        return all_results

    def positions(
        self,
        account: str,
        limit: int = 100,
        offset: int = 0,
    ) -> list[tuple]:
        """
        Fetch positions for an account.

        Args:
            account: Account address.
            limit: Maximum number of positions to fetch.
            offset: Starting offset.

        Returns:
            List of position data tuples.
        """
        return self._call("positions", limit, offset, account)

    def positions_paginated(
        self,
        account: str,
        limit: int = 100,
    ) -> list[tuple]:
        """
        Fetch all positions for an account with automatic pagination.

        Args:
            account: Account address.
            limit: Items per page.

        Returns:
            List of all position data tuples.
        """
        return self._paginate("positions", limit, extra_args=(account,))

    def positions_unstaked_concentrated(
        self,
        account: str,
        limit: int = 100,
        offset: int = 0,
    ) -> list[tuple]:
        """
        Fetch unstaked concentrated liquidity positions for an account.

        This is for pre-Superchain deployments.

        Args:
            account: Account address.
            limit: Maximum number of positions to fetch.
            offset: Starting offset.

        Returns:
            List of position data tuples.
        """
        return self._call("positionsUnstakedConcentrated", limit, offset, account)

    def for_swaps(
        self,
        limit: int = 500,
        offset: int = 0,
    ) -> list[tuple]:
        """
        Fetch minimal LP data optimized for swap routing.

        Args:
            limit: Maximum number of pools to fetch.
            offset: Starting offset.

        Returns:
            List of minimal LP data tuples (lp, type, token0, token1, factory, pool_fee).
        """
        return self._call("forSwaps", limit, offset)
