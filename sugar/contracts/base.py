"""Base contract class for Sugar contract wrappers."""

from __future__ import annotations

import json
import logging
import re
from collections.abc import Callable
from pathlib import Path
from typing import TYPE_CHECKING, Any

from web3 import Web3
from web3.contract import Contract

if TYPE_CHECKING:
    from sugar.core.web3_provider import Web3Provider

logger = logging.getLogger(__name__)

# Path to ABI files
ABI_DIR = Path(__file__).parent.parent / "config" / "abis"

# Global progress callback for RPC calls
# Signature: callback(chain: str, sugar_type: str, method: str, offset: int | None)
_progress_callback: Callable[[str, str, str, int | None], None] | None = None


def set_progress_callback(
    callback: Callable[[str, str, str, int | None], None] | None,
) -> None:
    """Set a global callback for RPC call progress."""
    global _progress_callback
    _progress_callback = callback


def get_progress_callback() -> Callable[[str, str, str, int | None], None] | None:
    """Get the current progress callback."""
    return _progress_callback


_ADDRESS_RE = re.compile(r"^0x[0-9a-fA-F]{40}$")


def _checksum_addresses(value: Any) -> Any:
    """Checksum any address-shaped string argument.

    web3.py rejects mixed/lower-case addresses; Sugar callers routinely pass
    lower-case account/token addresses, so normalize them (recursively for the
    connector lists) before encoding the call.
    """
    if isinstance(value, str) and _ADDRESS_RE.match(value):
        return Web3.to_checksum_address(value)
    if isinstance(value, list):
        return [_checksum_addresses(v) for v in value]
    if isinstance(value, tuple):
        return tuple(_checksum_addresses(v) for v in value)
    return value


def _clean_rpc_error(exc: Exception) -> str:
    """Return a short, human-readable error string — strips raw ABI payload bytes."""
    msg = str(exc)
    # web3.py decode errors append "with return data: b'...'" — drop that part
    cutoff = msg.find(" with return data: b'")
    if cutoff > 0:
        msg = msg[:cutoff] + " (raw payload omitted)"
    # Hard-cap so nothing enormous slips through
    if len(msg) > 300:
        msg = msg[:300] + "..."
    return msg


def load_abi(name: str) -> list[dict]:
    """Load ABI from JSON file."""
    abi_path = ABI_DIR / f"{name}.json"
    with open(abi_path) as f:
        return json.load(f)


class BaseContract:
    """Base class for Sugar contract wrappers."""

    ABI_NAME: str = ""  # Override in subclass
    SUGAR_TYPE: str = ""  # Override in subclass (e.g., "Lp", "Rewards", "Ve", "Relay")

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

    def _report_progress(self, method: str, offset: int | None = None) -> None:
        """Report RPC call progress — logs, or delegates to callback if set."""
        chain = self._provider.config.name if hasattr(self._provider, "config") else "unknown"
        sugar_type = self.SUGAR_TYPE or self.__class__.__name__
        callback = get_progress_callback()
        if callback:
            callback(chain, sugar_type, method, offset)
        else:
            if offset is not None:
                logger.info(f"RPC: {chain} | {sugar_type} | {method}(offset={offset})")
            else:
                logger.info(f"RPC: {chain} | {sugar_type} | {method}()")

    def _call(self, method: str, *args: Any, _skip_progress: bool = False) -> Any:
        """
        Call a contract method.

        Args:
            method: Method name.
            *args: Method arguments.
            _skip_progress: Internal flag to skip progress reporting (used by paginated methods).

        Returns:
            Method result.
        """
        if not _skip_progress:
            self._report_progress(method)
        func = getattr(self._contract.functions, method)
        args = tuple(_checksum_addresses(a) for a in args)
        try:
            result = func(*args).call()
        except Exception as e:
            logger.error(f"RPC ERROR: {method}(): {_clean_rpc_error(e)}")
            raise
        return result

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
        extra_args = tuple(_checksum_addresses(a) for a in extra_args)
        retries = 0
        max_retries = 3  # bounded retries at the same offset for transient errors

        while True:
            try:
                self._report_progress(method, offset)
                # Call contract directly instead of through _call to avoid double reporting
                func = getattr(self._contract.functions, method)
                result = func(limit, offset, *extra_args).call()
                retries = 0

                if not result:
                    if not all_results:
                        logger.warning(f"{method}() returned empty on first page")
                    break

                all_results.extend(result)
                # Increment offset by limit (pagination is index-based, not result-based)
                offset += limit

            except Exception as e:
                retries += 1
                logger.error(f"RPC ERROR: {method}(offset={offset}): {_clean_rpc_error(e)}")
                if retries >= max_retries:
                    # Do NOT silently return partial data — a truncated page set
                    # read as complete is worse than a clear failure.
                    from sugar.core.exceptions import PaginationError

                    raise PaginationError(
                        method,
                        offset,
                        f"failed after {retries} retries at offset {offset}",
                    ) from e

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
        # Count only consecutive *skips without a successful fetch* — halving
        # retries at the same offset don't burn the budget (otherwise a couple
        # of adjacent bad IDs would abort the whole scan). A genuinely dead RPC
        # keeps skipping without success and trips this bound.
        skips_without_progress = 0
        max_skips_without_progress = 25

        while True:
            try:
                self._report_progress(method, offset)
                # Call contract directly instead of through _call to avoid double reporting
                func = getattr(self._contract.functions, method)
                result = func(current_limit, offset).call()
                skips_without_progress = 0

                if not result:
                    break

                all_results.extend(result)

                # Next offset is last item's ID + 1
                last_id = result[-1][id_index]
                offset = last_id + 1
                current_limit = limit  # Reset limit after success

                logger.debug(f"{method}: fetched {len(result)} items, next ID {offset}")

            except Exception as e:
                logger.error(f"RPC ERROR: {method}(id={offset}): {_clean_rpc_error(e)}")
                # Reduce limit (retry same offset, doesn't count as a skip) or,
                # once at limit 1, skip the offending ID.
                if current_limit > 1:
                    current_limit = max(1, current_limit // 2)
                    logger.info(f"Reducing limit to {current_limit}")
                else:
                    offset += 1
                    current_limit = limit
                    skips_without_progress += 1
                    logger.info(f"Skipping to ID {offset}")
                    if skips_without_progress >= max_skips_without_progress:
                        from sugar.core.exceptions import PaginationError

                        raise PaginationError(
                            method,
                            offset,
                            f"aborted after {skips_without_progress} consecutive "
                            "skips without progress",
                        ) from e

        return all_results
