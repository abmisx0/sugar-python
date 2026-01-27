"""Sugar Python - Library for Velodrome/Aerodrome Sugar Protocol."""

from sugar.config.chains import ChainId
from sugar.core.client import SugarClient
from sugar.core.exceptions import (
    ContractNotAvailableError,
    PriceNotAvailableError,
    SugarError,
)

__version__ = "0.1.0"
__all__ = [
    "SugarClient",
    "ChainId",
    "SugarError",
    "ContractNotAvailableError",
    "PriceNotAvailableError",
]
