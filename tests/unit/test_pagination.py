"""Tests for pagination utilities."""

from __future__ import annotations

from typing import Any

import pytest

from sugar.core.pagination import collect_paginated, paginate, paginate_by_id


class TestPaginate:
    """Test offset-based pagination."""

    def test_single_page(self) -> None:
        """Should yield single page when data fits."""
        data = [(1, "a"), (2, "b"), (3, "c")]

        def fetch_fn(limit: int, offset: int) -> list[tuple[Any, ...]]:
            return data[offset : offset + limit]

        pages = list(paginate(fetch_fn, limit=10))
        assert len(pages) == 1
        assert pages[0] == data

    def test_multiple_pages(self) -> None:
        """Should yield multiple pages when data exceeds limit."""
        data = [(i, f"item_{i}") for i in range(25)]

        def fetch_fn(limit: int, offset: int) -> list[tuple[Any, ...]]:
            return data[offset : offset + limit]

        pages = list(paginate(fetch_fn, limit=10))
        assert len(pages) == 3
        assert len(pages[0]) == 10
        assert len(pages[1]) == 10
        assert len(pages[2]) == 5

    def test_empty_data(self) -> None:
        """Should handle empty data."""

        def fetch_fn(limit: int, offset: int) -> list[tuple[Any, ...]]:
            return []

        pages = list(paginate(fetch_fn, limit=10))
        assert len(pages) == 0

    def test_exact_page_boundary(self) -> None:
        """Should handle data that exactly fills pages."""
        data = [(i,) for i in range(20)]

        def fetch_fn(limit: int, offset: int) -> list[tuple[Any, ...]]:
            return data[offset : offset + limit]

        pages = list(paginate(fetch_fn, limit=10))
        assert len(pages) == 2
        assert len(pages[0]) == 10
        assert len(pages[1]) == 10

    def test_custom_limit(self) -> None:
        """Should respect custom limit."""
        data = [(i,) for i in range(15)]

        def fetch_fn(limit: int, offset: int) -> list[tuple[Any, ...]]:
            return data[offset : offset + limit]

        pages = list(paginate(fetch_fn, limit=5))
        assert len(pages) == 3


class TestPaginateById:
    """Test ID-based pagination."""

    def test_single_page(self) -> None:
        """Should yield single page when data fits."""
        data = [(1, "a"), (2, "b"), (3, "c")]

        def fetch_fn(limit: int, _id: int) -> list[tuple[Any, ...]]:
            # Filter items with id > _id
            return [item for item in data if item[0] > _id][:limit]

        pages = list(paginate_by_id(fetch_fn, limit=10, start_id=0))
        assert len(pages) == 1
        assert pages[0] == data

    def test_empty_data(self) -> None:
        """Should handle empty data."""

        def fetch_fn(limit: int, _id: int) -> list[tuple[Any, ...]]:
            return []

        pages = list(paginate_by_id(fetch_fn, limit=10, start_id=0))
        assert len(pages) == 0

    def test_custom_start_id(self) -> None:
        """Should start from custom ID."""
        data = [(i,) for i in range(1, 11)]

        def fetch_fn(limit: int, _id: int) -> list[tuple[Any, ...]]:
            return [item for item in data if item[0] > _id][:limit]

        pages = list(paginate_by_id(fetch_fn, limit=10, start_id=5))
        assert len(pages) == 1
        assert pages[0] == [(6,), (7,), (8,), (9,), (10,)]


class TestCollectPaginated:
    """Test collect_paginated function."""

    def test_collects_all_results(self) -> None:
        """Should collect all paginated results into single list."""
        data = [(i,) for i in range(25)]

        def fetch_fn(limit: int, offset: int) -> list[tuple[Any, ...]]:
            return data[offset : offset + limit]

        result = collect_paginated(fetch_fn, limit=10)
        assert len(result) == 25
        assert result == data

    def test_empty_data(self) -> None:
        """Should return empty list for empty data."""

        def fetch_fn(limit: int, offset: int) -> list[tuple[Any, ...]]:
            return []

        result = collect_paginated(fetch_fn, limit=10)
        assert result == []
