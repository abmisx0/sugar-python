"""Sugar Python - Library for Velodrome/Aerodrome Sugar Protocol."""

from sugar.config.chains import ChainId
from sugar.contracts.base import set_progress_callback
from sugar.core.client import SugarClient
from sugar.core.exceptions import (
    ContractNotAvailableError,
    PriceNotAvailableError,
    SugarError,
)
from sugar.services.snapshot import SnapshotStore
from sugar.utils.logging import setup_logging

__version__ = "0.1.0"
__all__ = [
    "SugarClient",
    "ChainId",
    "SnapshotStore",
    "SugarError",
    "ContractNotAvailableError",
    "PriceNotAvailableError",
    "set_progress_callback",
    "setup_logging",
]
