"""RelaySugar contract wrapper."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from sugar.contracts.base import BaseContract

if TYPE_CHECKING:
    from sugar.core.web3_provider import Web3Provider

logger = logging.getLogger(__name__)

# Zero address constant
ZERO_ADDRESS = "0x0000000000000000000000000000000000000000"


class RelaySugar(BaseContract):
    """
    Wrapper for the RelaySugar contract.

    Provides methods to query relay (autocompounder/autoconverter) data.
    """

    ABI_NAME = "relay_sugar"
    SUGAR_TYPE = "Relay"

    def __init__(
        self,
        provider: Web3Provider,
        address: str,
    ) -> None:
        """
        Initialize RelaySugar contract wrapper.

        Args:
            provider: Web3Provider instance.
            address: RelaySugar contract address.
        """
        super().__init__(provider, address)

    def all(self, account: str = ZERO_ADDRESS) -> list[tuple]:
        """
        Fetch all relay data.

        Args:
            account: Account address to include account-specific veNFT data.
                    Use zero address to exclude account data.

        Returns:
            List of relay data tuples.
        """
        return self._call("all", account)

    def voter(self) -> str:
        """
        Get the Voter contract address.

        Returns:
            Voter contract address.
        """
        return self._call("voter")

    def ve(self) -> str:
        """
        Get the VotingEscrow contract address.

        Returns:
            VotingEscrow contract address.
        """
        return self._call("ve")

    def token(self) -> str:
        """
        Get the governance token address.

        Returns:
            Token contract address.
        """
        return self._call("token")
