"""Tests for caching utilities."""

from __future__ import annotations

import time
from unittest.mock import MagicMock

import pytest

from sugar.utils.cache import ttl_cache


class TestTtlCache:
    """Test TTL cache decorator."""

    def test_caches_result(self) -> None:
        """Should cache function result."""
        call_count = 0

        @ttl_cache(ttl_seconds=60)
        def expensive_function(x: int) -> int:
            nonlocal call_count
            call_count += 1
            return x * 2

        result1 = expensive_function(5)
        result2 = expensive_function(5)

        assert result1 == 10
        assert result2 == 10
        assert call_count == 1  # Only called once

    def test_different_args_not_cached(self) -> None:
        """Should not cache different arguments."""
        call_count = 0

        @ttl_cache(ttl_seconds=60)
        def expensive_function(x: int) -> int:
            nonlocal call_count
            call_count += 1
            return x * 2

        result1 = expensive_function(5)
        result2 = expensive_function(10)

        assert result1 == 10
        assert result2 == 20
        assert call_count == 2

    def test_cache_expires(self) -> None:
        """Should expire cache after TTL."""
        call_count = 0

        @ttl_cache(ttl_seconds=0.1)  # 100ms TTL
        def expensive_function(x: int) -> int:
            nonlocal call_count
            call_count += 1
            return x * 2

        result1 = expensive_function(5)
        time.sleep(0.15)  # Wait for cache to expire
        result2 = expensive_function(5)

        assert result1 == 10
        assert result2 == 10
        assert call_count == 2  # Called twice after expiry

    def test_cache_with_kwargs(self) -> None:
        """Should cache based on kwargs too."""
        call_count = 0

        @ttl_cache(ttl_seconds=60)
        def expensive_function(x: int, multiplier: int = 2) -> int:
            nonlocal call_count
            call_count += 1
            return x * multiplier

        result1 = expensive_function(5, multiplier=2)
        result2 = expensive_function(5, multiplier=2)
        result3 = expensive_function(5, multiplier=3)

        assert result1 == 10
        assert result2 == 10
        assert result3 == 15
        assert call_count == 2  # 2 different kwarg combinations

    def test_cache_preserves_function_name(self) -> None:
        """Should preserve the original function name."""

        @ttl_cache(ttl_seconds=60)
        def my_function() -> str:
            return "hello"

        assert my_function.__name__ == "my_function"

    def test_cache_with_no_args(self) -> None:
        """Should cache function with no arguments."""
        call_count = 0

        @ttl_cache(ttl_seconds=60)
        def no_args_function() -> str:
            nonlocal call_count
            call_count += 1
            return "result"

        result1 = no_args_function()
        result2 = no_args_function()

        assert result1 == "result"
        assert result2 == "result"
        assert call_count == 1

    def test_default_ttl(self) -> None:
        """Should use default TTL of 300 seconds."""

        @ttl_cache()
        def func() -> str:
            return "test"

        # Just verify it works with default TTL
        result = func()
        assert result == "test"

    def test_cache_with_none_result(self) -> None:
        """Should cache None results."""
        call_count = 0

        @ttl_cache(ttl_seconds=60)
        def returns_none() -> None:
            nonlocal call_count
            call_count += 1
            return None

        result1 = returns_none()
        result2 = returns_none()

        assert result1 is None
        assert result2 is None
        assert call_count == 1
