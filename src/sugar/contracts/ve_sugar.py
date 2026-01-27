"""VeSugar contract wrapper."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from sugar.contracts.base import BaseContract

if TYPE_CHECKING:
    from sugar.core.web3_provider import Web3Provider

logger = logging.getLogger(__name__)


class VeSugar(BaseContract):
    """
    Wrapper for the VeSugar contract.

    Provides methods to query vote-escrow NFT (veNFT) data.
    """

    ABI_NAME = "ve_sugar"

    def __init__(
        self,
        provider: Web3Provider,
        address: str,
    ) -> None:
        """
        Initialize VeSugar contract wrapper.

        Args:
            provider: Web3Provider instance.
            address: VeSugar contract address.
        """
        super().__init__(provider, address)

    def all(
        self,
        limit: int = 500,
        offset: int = 1,
    ) -> list[tuple]:
        """
        Fetch veNFT data for a single page.

        Note: VeSugar uses ID-based pagination where offset is the starting NFT ID.

        Args:
            limit: Maximum number of veNFTs to fetch.
            offset: Starting NFT ID (1-indexed).

        Returns:
            List of veNFT data tuples.
        """
        return self._call("all", limit, offset)

    def all_paginated(
        self,
        limit: int = 500,
        start_id: int = 1,
    ) -> list[tuple]:
        """
        Fetch all veNFT data with automatic pagination.

        Uses ID-based pagination where the next offset is the last item's ID + 1.

        Args:
            limit: Items per page.
            start_id: Starting NFT ID.

        Returns:
            List of all veNFT data tuples.
        """
        return self._paginate_by_id("all", limit, start_id, id_index=0)

    def by_account(self, account: str) -> list[tuple]:
        """
        Fetch all veNFTs owned by an account.

        Args:
            account: Account address.

        Returns:
            List of veNFT data tuples for the account.
        """
        return self._call("byAccount", account)

    def by_id(self, nft_id: int) -> tuple:
        """
        Fetch veNFT data by ID.

        Args:
            nft_id: veNFT token ID.

        Returns:
            veNFT data tuple.
        """
        return self._call("byId", nft_id)

    def voter(self) -> str:
        """
        Get the Voter contract address.

        Returns:
            Voter contract address.
        """
        return self._call("voter")

    def token(self) -> str:
        """
        Get the governance token address.

        Returns:
            Token contract address.
        """
        return self._call("token")

    def ve(self) -> str:
        """
        Get the VotingEscrow contract address.

        Returns:
            VotingEscrow contract address.
        """
        return self._call("ve")
