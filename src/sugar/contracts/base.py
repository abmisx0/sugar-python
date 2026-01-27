"""Base contract class for Sugar contract wrappers."""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import TYPE_CHECKING, Any

from web3 import Web3
from web3.contract import Contract

if TYPE_CHECKING:
    from sugar.core.web3_provider import Web3Provider

logger = logging.getLogger(__name__)

# Path to ABI files
ABI_DIR = Path(__file__).parent.parent / "config" / "abis"


def load_abi(name: str) -> list[dict]:
    """Load ABI from JSON file."""
    abi_path = ABI_DIR / f"{name}.json"
    with open(abi_path) as f:
        return json.load(f)


class BaseContract:
    """Base class for Sugar contract wrappers."""

    ABI_NAME: str = ""  # Override in subclass

    def __init__(
        self,
        provider: Web3Provider,
        address: str,
        abi: list[dict] | None = None,
    ) -> None:
        """
        Initialize contract wrapper.

        Args:
            provider: Web3Provider instance.
            address: Contract address.
            abi: Contract ABI (optional, will load from file if not provided).
        """
        self._provider = provider
        self._address = Web3.to_checksum_address(address)

        if abi is None:
            if not self.ABI_NAME:
                raise ValueError(f"ABI_NAME not set for {self.__class__.__name__}")
            abi = load_abi(self.ABI_NAME)

        self._contract: Contract = provider.web3.eth.contract(
            address=self._address,
            abi=abi,
        )

    @property
    def address(self) -> str:
        """Contract address."""
        return self._address

    @property
    def web3(self) -> Web3:
        """Web3 instance."""
        return self._provider.web3

    @property
    def contract(self) -> Contract:
        """Web3 contract instance."""
        return self._contract

    def _call(self, method: str, *args: Any) -> Any:
        """
        Call a contract method.

        Args:
            method: Method name.
            *args: Method arguments.

        Returns:
            Method result.
        """
        func = getattr(self._contract.functions, method)
        return func(*args).call()

    def _paginate(
        self,
        method: str,
        limit: int,
        start_offset: int = 0,
        extra_args: tuple = (),
    ) -> list[tuple]:
        """
        Paginate through contract results.

        Args:
            method: Method name.
            limit: Items per page.
            start_offset: Starting offset.
            extra_args: Additional arguments after limit/offset.

        Returns:
            List of all results.
        """
        all_results: list[tuple] = []
        offset = start_offset

        while True:
            try:
                func = getattr(self._contract.functions, method)
                result = func(limit, offset, *extra_args).call()

                if not result:
                    break

                all_results.extend(result)
                offset += limit
                logger.debug(f"{method}: fetched {len(result)} items, offset now {offset}")

            except Exception as e:
                logger.warning(f"Pagination error in {method} at offset {offset}: {e}")
                break

        return all_results

    def _paginate_by_id(
        self,
        method: str,
        limit: int,
        start_id: int = 1,
        id_index: int = 0,
    ) -> list[tuple]:
        """
        Paginate through contract results using ID-based pagination.

        Used for VeSugar.all() which uses the last item's ID as next offset.

        Args:
            method: Method name.
            limit: Items per page.
            start_id: Starting ID.
            id_index: Index of ID field in result tuple.

        Returns:
            List of all results.
        """
        all_results: list[tuple] = []
        offset = start_id
        current_limit = limit

        while True:
            try:
                func = getattr(self._contract.functions, method)
                result = func(current_limit, offset).call()

                if not result:
                    break

                all_results.extend(result)

                # Next offset is last item's ID + 1
                last_id = result[-1][id_index]
                offset = last_id + 1
                current_limit = limit  # Reset limit after success

                logger.debug(f"{method}: fetched {len(result)} items, next ID {offset}")

            except Exception as e:
                logger.warning(f"ID pagination error in {method} at ID {offset}: {e}")
                # Reduce limit or skip ID on error
                if current_limit > 1:
                    current_limit = max(1, current_limit // 2)
                    logger.info(f"Reducing limit to {current_limit}")
                else:
                    offset += 1
                    current_limit = limit
                    logger.info(f"Skipping to ID {offset}")

        return all_results
