"""RewardsSugar contract wrapper."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from sugar.contracts.base import BaseContract

if TYPE_CHECKING:
    from sugar.core.web3_provider import Web3Provider

logger = logging.getLogger(__name__)


class RewardsSugar(BaseContract):
    """
    Wrapper for the RewardsSugar contract.

    Provides methods to query pool epoch rewards and veNFT claimable rewards.
    """

    ABI_NAME = "rewards_sugar"

    def __init__(
        self,
        provider: Web3Provider,
        address: str,
    ) -> None:
        """
        Initialize RewardsSugar contract wrapper.

        Args:
            provider: Web3Provider instance.
            address: RewardsSugar contract address.
        """
        super().__init__(provider, address)

    def epochs_latest(
        self,
        limit: int = 500,
        offset: int = 0,
    ) -> list[tuple]:
        """
        Fetch latest epoch data for all pools.

        Args:
            limit: Maximum number of epochs to fetch.
            offset: Starting offset.

        Returns:
            List of epoch data tuples (ts, lp, votes, emissions, bribes, fees).
        """
        return self._call("epochsLatest", limit, offset)

    def epochs_latest_paginated(
        self,
        limit: int = 500,
        max_offset: int | None = None,
    ) -> list[tuple]:
        """
        Fetch all latest epoch data with automatic pagination.

        Note: epochsLatest paginates by pool index, and pools with gauges
        may be sparse, so we need to paginate through all pool indices
        (not just until we get an empty result).

        Args:
            limit: Items per page.
            max_offset: Maximum offset to paginate to. If None, will try to
                detect the pool count from the contract.

        Returns:
            List of all epoch data tuples.
        """
        all_results: list[tuple] = []
        offset = 0
        empty_count = 0

        while True:
            try:
                result = self.epochs_latest(limit, offset)

                if result:
                    all_results.extend(result)
                    empty_count = 0
                else:
                    empty_count += 1
                    # Stop after multiple consecutive empty results
                    # This handles gaps in the data while still stopping eventually
                    if empty_count > 10:
                        break

                offset += limit

                # Safety limit to prevent infinite loop
                if max_offset and offset >= max_offset:
                    break
                if offset > 50000:  # Hard limit
                    break

            except Exception as e:
                logger.warning(f"epochs_latest pagination error at offset {offset}: {e}")
                break

        return all_results

    def epochs_by_address(
        self,
        pool_address: str,
        limit: int = 50,
        offset: int = 0,
    ) -> list[tuple]:
        """
        Fetch epoch history for a specific pool.

        Args:
            pool_address: Pool contract address.
            limit: Maximum number of epochs to fetch.
            offset: Starting offset.

        Returns:
            List of epoch data tuples for the pool.
        """
        return self._call("epochsByAddress", limit, offset, pool_address)

    def epochs_by_address_paginated(
        self,
        pool_address: str,
        limit: int = 50,
    ) -> list[tuple]:
        """
        Fetch all epoch history for a pool with automatic pagination.

        Args:
            pool_address: Pool contract address.
            limit: Items per page.

        Returns:
            List of all epoch data tuples for the pool.
        """
        return self._paginate("epochsByAddress", limit, extra_args=(pool_address,))

    def rewards(
        self,
        venft_id: int,
        limit: int = 100,
        offset: int = 0,
    ) -> list[tuple]:
        """
        Fetch claimable rewards for a veNFT.

        Args:
            venft_id: veNFT token ID.
            limit: Maximum number of rewards to fetch.
            offset: Starting offset.

        Returns:
            List of reward data tuples (venft_id, lp, amount, token, fee, bribe).
        """
        return self._call("rewards", limit, offset, venft_id)

    def rewards_paginated(
        self,
        venft_id: int,
        limit: int = 100,
    ) -> list[tuple]:
        """
        Fetch all claimable rewards for a veNFT with automatic pagination.

        Args:
            venft_id: veNFT token ID.
            limit: Items per page.

        Returns:
            List of all reward data tuples.
        """
        return self._paginate("rewards", limit, extra_args=(venft_id,))

    def rewards_by_address(
        self,
        venft_id: int,
        pool_address: str,
    ) -> list[tuple]:
        """
        Fetch claimable rewards for a veNFT from a specific pool.

        Args:
            venft_id: veNFT token ID.
            pool_address: Pool contract address.

        Returns:
            List of reward data tuples for the pool.
        """
        return self._call("rewardsByAddress", venft_id, pool_address)

    def for_root(self, root_pool: str) -> tuple[str, str, str]:
        """
        Get fee and bribe addresses for a root pool.

        Args:
            root_pool: Root pool address.

        Returns:
            Tuple of (fee_address, bribe_address, unknown).
        """
        return self._call("forRoot", root_pool)
