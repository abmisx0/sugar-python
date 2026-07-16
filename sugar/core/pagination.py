"""Generic pagination utilities for Sugar contract calls."""

from __future__ import annotations

import logging
from collections.abc import Callable, Iterator
from typing import TypeVar

from sugar.core.exceptions import PaginationError

logger = logging.getLogger(__name__)

T = TypeVar("T")


def paginate(
    fetch_fn: Callable[[int, int], list[T]],
    limit: int = 500,
    start_offset: int = 0,
    max_retries: int = 3,
    reduce_limit_on_error: bool = True,
) -> Iterator[list[T]]:
    """
    Generic pagination iterator for contract calls.

    Args:
        fetch_fn: Function that takes (limit, offset) and returns a list of results.
        limit: Maximum number of items to fetch per call.
        start_offset: Starting offset for pagination.
        max_retries: Maximum number of retries on error.
        reduce_limit_on_error: Whether to reduce limit on error and retry.

    Yields:
        List of items from each page.

    Raises:
        PaginationError: If pagination fails after all retries.
    """
    offset = start_offset
    current_limit = limit
    retries = 0

    while True:
        try:
            result = fetch_fn(current_limit, offset)

            if not result:
                logger.debug(f"Pagination complete at offset {offset}")
                break

            yield result

            offset += len(result)
            current_limit = limit  # Reset limit after successful call
            retries = 0

            logger.debug(f"Fetched {len(result)} items, next offset: {offset}")

        except Exception as e:
            retries += 1
            logger.warning(f"Pagination error at offset {offset}: {e}")

            if retries >= max_retries:
                raise PaginationError(
                    method="paginate",
                    offset=offset,
                    details=f"Failed after {max_retries} retries: {e}",
                ) from e

            if reduce_limit_on_error and current_limit > 1:
                current_limit = max(1, current_limit // 2)
                logger.info(f"Reducing limit to {current_limit} and retrying")
            else:
                logger.info(f"Retrying with same limit ({retries}/{max_retries})")


def paginate_by_id(
    fetch_fn: Callable[[int, int], list[tuple]],
    id_index: int = 0,
    limit: int = 500,
    start_id: int = 1,
    max_retries: int = 3,
    reduce_limit_on_error: bool = True,
) -> Iterator[list[tuple]]:
    """
    Pagination iterator that uses the last item's ID as the next offset.

    This is useful for VeSugar.all() which uses ID-based pagination.

    Args:
        fetch_fn: Function that takes (limit, offset) and returns a list of tuples.
        id_index: Index of the ID field in the result tuple.
        limit: Maximum number of items to fetch per call.
        start_id: Starting ID for pagination.
        max_retries: Maximum number of retries on error.
        reduce_limit_on_error: Whether to reduce limit on error and retry.

    Yields:
        List of items from each page.

    Raises:
        PaginationError: If pagination fails after all retries.
    """
    offset = start_id
    current_limit = limit
    retries = 0

    while True:
        try:
            result = fetch_fn(current_limit, offset)

            if not result:
                logger.debug(f"ID-based pagination complete at ID {offset}")
                break

            yield result

            # Get next offset from last item's ID
            last_id = result[-1][id_index]
            offset = last_id + 1
            current_limit = limit  # Reset limit after successful call
            retries = 0

            logger.debug(f"Fetched {len(result)} items, next ID: {offset}")

        except Exception as e:
            retries += 1
            logger.warning(f"Pagination error at ID {offset}: {e}")

            if retries >= max_retries:
                raise PaginationError(
                    method="paginate_by_id",
                    offset=offset,
                    details=f"Failed after {max_retries} retries: {e}",
                ) from e

            if reduce_limit_on_error and current_limit > 1:
                current_limit = max(1, current_limit // 2)
                logger.info(f"Reducing limit to {current_limit} and retrying")
            else:
                # Try skipping the problematic ID
                offset += 1
                current_limit = limit
                logger.info(f"Skipping to ID {offset}")


def collect_paginated(
    fetch_fn: Callable[[int, int], list[T]],
    limit: int = 500,
    start_offset: int = 0,
    max_items: int | None = None,
) -> list[T]:
    """
    Collect all results from paginated calls into a single list.

    Args:
        fetch_fn: Function that takes (limit, offset) and returns a list of results.
        limit: Maximum number of items to fetch per call.
        start_offset: Starting offset for pagination.
        max_items: Maximum total items to collect (None for unlimited).

    Returns:
        List of all collected items.
    """
    results: list[T] = []

    for page in paginate(fetch_fn, limit, start_offset):
        results.extend(page)

        if max_items is not None and len(results) >= max_items:
            results = results[:max_items]
            break

    return results


def collect_paginated_by_id(
    fetch_fn: Callable[[int, int], list[tuple]],
    id_index: int = 0,
    limit: int = 500,
    start_id: int = 1,
    max_items: int | None = None,
) -> list[tuple]:
    """
    Collect all results from ID-based paginated calls into a single list.

    Args:
        fetch_fn: Function that takes (limit, offset) and returns a list of tuples.
        id_index: Index of the ID field in the result tuple.
        limit: Maximum number of items to fetch per call.
        start_id: Starting ID for pagination.
        max_items: Maximum total items to collect (None for unlimited).

    Returns:
        List of all collected items.
    """
    results: list[tuple] = []

    for page in paginate_by_id(fetch_fn, id_index, limit, start_id):
        results.extend(page)

        if max_items is not None and len(results) >= max_items:
            results = results[:max_items]
            break

    return results
