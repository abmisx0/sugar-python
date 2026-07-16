"""Services module for Sugar Python library."""

from typing import TYPE_CHECKING

from sugar.services.deployment import (
    DeploymentFetcher,
    fetch_all_deployments,
    fetch_chain_deployment,
    get_deployment_fetcher,
    get_sugar_addresses,
    parse_chain_deployment,
)
from sugar.services.price_provider import PriceProvider
from sugar.services.snapshot import SnapshotStore

if TYPE_CHECKING:
    from sugar.services.data_processor import DataProcessor
    from sugar.services.export import ExportService

__all__ = [
    "DataProcessor",
    "DeploymentFetcher",
    "ExportService",
    "PriceProvider",
    "SnapshotStore",
    "fetch_all_deployments",
    "fetch_chain_deployment",
    "get_deployment_fetcher",
    "get_sugar_addresses",
    "parse_chain_deployment",
]


def __getattr__(name: str):  # PEP 562: lazy so importing this package is pandas-free
    if name == "DataProcessor":
        from sugar.services.data_processor import DataProcessor

        return DataProcessor
    if name == "ExportService":
        from sugar.services.export import ExportService

        return ExportService
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
