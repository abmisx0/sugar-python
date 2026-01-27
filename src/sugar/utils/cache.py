"""Caching utilities for Sugar Python library."""

import time
from functools import lru_cache, wraps
from typing import Callable, ParamSpec, TypeVar

P = ParamSpec("P")
R = TypeVar("R")


def ttl_cache(ttl_seconds: int = 300) -> Callable[[Callable[P, R]], Callable[P, R]]:
    """
    Time-to-live cache decorator.

    Caches function results for a specified duration. After TTL expires,
    the next call will re-execute the function.

    Args:
        ttl_seconds: Cache lifetime in seconds. Default is 300 (5 minutes).

    Returns:
        Decorated function with TTL caching.

    Example:
        >>> @ttl_cache(ttl_seconds=60)
        ... def fetch_data() -> dict:
        ...     '''Fetch some data.'''
        ...     return {"key": "value"}
    """

    def decorator(func: Callable[P, R]) -> Callable[P, R]:
        cache: dict[tuple, tuple[float, R]] = {}

        @wraps(func)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            # Create cache key from args and kwargs
            key = (args, tuple(sorted(kwargs.items())))

            # Check if cached and not expired
            if key in cache:
                cached_time, cached_value = cache[key]
                if time.time() - cached_time < ttl_seconds:
                    return cached_value

            # Call function and cache result
            result = func(*args, **kwargs)
            cache[key] = (time.time(), result)
            return result

        return wrapper

    return decorator


def documented_cache(maxsize: int | None = None) -> Callable[[Callable[P, R]], Callable[P, R]]:
    """
    Decorator that wraps lru_cache while preserving the original function's docstring.

    Args:
        maxsize: Maximum size of the LRU cache. None means unlimited.

    Returns:
        Decorated function with LRU caching.

    Example:
        >>> @documented_cache(maxsize=32)
        ... def expensive_operation(x: int) -> int:
        ...     '''Compute something expensive.'''
        ...     return x * x
        >>> expensive_operation.__doc__
        'Compute something expensive.'
    """

    def decorator(func: Callable[P, R]) -> Callable[P, R]:
        @wraps(func)
        @lru_cache(maxsize=maxsize)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            return func(*args, **kwargs)

        return wrapper

    return decorator


def clear_cache(func: Callable) -> None:
    """
    Clear the LRU cache for a function decorated with documented_cache.

    Args:
        func: Function with LRU cache to clear.
    """
    if hasattr(func, "cache_clear"):
        func.cache_clear()


def cache_info(func: Callable) -> dict:
    """
    Get cache statistics for a function decorated with documented_cache.

    Args:
        func: Function with LRU cache.

    Returns:
        Dictionary with cache statistics (hits, misses, maxsize, currsize).
    """
    if hasattr(func, "cache_info"):
        info = func.cache_info()
        return {
            "hits": info.hits,
            "misses": info.misses,
            "maxsize": info.maxsize,
            "currsize": info.currsize,
        }
    return {}
