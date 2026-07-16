"""Sugar Python - Library for Velodrome/Aerodrome Sugar Protocol."""

from sugar.config.chains import ChainId
from sugar.contracts.base import set_progress_callback
from sugar.core.client import SugarClient, positions_across_chains
from sugar.core.exceptions import (
    ContractNotAvailableError,
    PriceNotAvailableError,
    SugarError,
)
from sugar.models import (
    AccountPosition,
    ChainError,
    Portfolio,
    PositionKind,
    Relay,
    Token,
    TokenAmount,
    VeNFT,
    to_dict,
)
from sugar.services.snapshot import SnapshotStore
from sugar.utils.logging import setup_logging

__version__ = "0.2.0"
__all__ = [
    "SugarClient",
    "ChainId",
    "SnapshotStore",
    "SugarError",
    "ContractNotAvailableError",
    "PriceNotAvailableError",
    "set_progress_callback",
    "setup_logging",
    # Typed models
    "AccountPosition",
    "ChainError",
    "Portfolio",
    "PositionKind",
    "Relay",
    "Token",
    "TokenAmount",
    "VeNFT",
    "to_dict",
    # Multi-chain aggregation
    "positions_across_chains",
]
