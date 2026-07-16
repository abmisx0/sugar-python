"""Core module for Sugar Python library."""

from sugar.core.client import SugarClient
from sugar.core.exceptions import (
    ContractNotAvailableError,
    PriceNotAvailableError,
    SugarError,
)
from sugar.core.pagination import paginate
from sugar.core.web3_provider import Web3Provider

__all__ = [
    "SugarClient",
    "Web3Provider",
    "paginate",
    "SugarError",
    "ContractNotAvailableError",
    "PriceNotAvailableError",
]
