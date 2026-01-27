"""Price provider service with fallback support."""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass
from decimal import Decimal
from typing import TYPE_CHECKING, Protocol

import requests

from sugar.core.exceptions import PriceNotAvailableError

if TYPE_CHECKING:
    from sugar.config.chains import ChainId
    from sugar.contracts.price_oracle import SpotPriceOracle

logger = logging.getLogger(__name__)


@dataclass
class PriceResult:
    """Result of a price query."""

    price: Decimal
    source: str  # "oracle", "coingecko", or "defillama"
    timestamp: int


class PriceSource(Protocol):
    """Protocol for price sources."""

    def get_price_usd(self, token_address: str) -> Decimal | None:
        """Get token price in USD."""
        ...


class OraclePriceSource:
    """
    Price source using on-chain Spot Price Oracle.

    Uses ETH price as intermediate to calculate USD prices.
    """

    # Known stablecoin addresses per chain (for ETH/USD conversion)
    STABLECOINS = {
        # Base
        "0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913": "USDC",  # Base USDC
        # Optimism
        "0x0b2C639c533813f4Aa9D7837CAf62653d097Ff85": "USDC",  # OP USDC
        "0x94b008aA00579c1307B0EF2c499aD98a8ce58e58": "USDT",  # OP USDT
    }

    def __init__(
        self,
        oracle: SpotPriceOracle,
        usdc_address: str | None = None,
    ) -> None:
        """
        Initialize oracle price source.

        Args:
            oracle: SpotPriceOracle contract wrapper.
            usdc_address: USDC address on this chain for USD conversion.
        """
        self._oracle = oracle
        self._usdc_address = usdc_address

    def get_price_usd(self, token_address: str) -> Decimal | None:
        """Get token price in USD via oracle."""
        try:
            # If token is a stablecoin, return 1
            if token_address.lower() in [a.lower() for a in self.STABLECOINS]:
                return Decimal("1.0")

            # If we have a USDC address, get direct rate
            if self._usdc_address:
                try:
                    rate = self._oracle.get_rate(token_address, self._usdc_address)
                    if rate > 0:
                        return rate
                except Exception:
                    pass

            # Fallback: get rate to ETH and multiply by ETH/USD
            eth_rate = self._oracle.get_rate_to_eth(token_address)
            if eth_rate == 0:
                return None

            # Get ETH/USD price if we have USDC address
            if self._usdc_address:
                eth_usd = self._oracle.get_rate(
                    "0x4200000000000000000000000000000000000006",  # WETH
                    self._usdc_address,
                )
                return eth_rate * eth_usd

            return eth_rate  # Return ETH-denominated if no USD conversion

        except Exception as e:
            logger.debug(f"Oracle price fetch failed for {token_address}: {e}")
            return None


class CoinGeckoPriceSource:
    """
    Price source using CoinGecko API.

    Free tier has rate limits (~10-50 req/min).
    """

    BASE_URL = "https://api.coingecko.com/api/v3"

    # Chain ID to CoinGecko platform mapping
    PLATFORM_MAP = {
        10: "optimistic-ethereum",
        8453: "base",
        34443: "mode-network",
        1135: "lisk",
        252: "fraxtal",
        42220: "celo",
    }

    def __init__(self, chain_id: ChainId) -> None:
        """
        Initialize CoinGecko price source.

        Args:
            chain_id: Chain ID for platform mapping.
        """
        self._chain_id = chain_id.value
        self._platform = self.PLATFORM_MAP.get(self._chain_id, "ethereum")
        self._session = requests.Session()
        self._cache: dict[str, tuple[Decimal, float]] = {}
        self._cache_ttl = 60  # seconds

    def get_price_usd(self, token_address: str) -> Decimal | None:
        """Get token price in USD from CoinGecko."""
        # Check cache
        cache_key = token_address.lower()
        if cache_key in self._cache:
            price, timestamp = self._cache[cache_key]
            if time.time() - timestamp < self._cache_ttl:
                return price

        try:
            url = f"{self.BASE_URL}/simple/token_price/{self._platform}"
            params = {
                "contract_addresses": token_address,
                "vs_currencies": "usd",
            }

            response = self._session.get(url, params=params, timeout=10)
            response.raise_for_status()

            data = response.json()
            if token_address.lower() in data:
                price = Decimal(str(data[token_address.lower()]["usd"]))
                self._cache[cache_key] = (price, time.time())
                return price

            return None

        except Exception as e:
            logger.debug(f"CoinGecko price fetch failed for {token_address}: {e}")
            return None


class DefiLlamaPriceSource:
    """
    Price source using DefiLlama API.

    No API key required, generous rate limits.
    """

    BASE_URL = "https://coins.llama.fi"

    # Chain ID to DefiLlama chain name mapping
    CHAIN_MAP = {
        10: "optimism",
        8453: "base",
        34443: "mode",
        1135: "lisk",
        252: "fraxtal",
        57073: "ink",
        1868: "soneium",
        1750: "metal",
        42220: "celo",
        5330: "superseed",
        1923: "swell",
        130: "unichain",
    }

    def __init__(self, chain_id: ChainId) -> None:
        """
        Initialize DefiLlama price source.

        Args:
            chain_id: Chain ID for chain name mapping.
        """
        self._chain_id = chain_id.value
        self._chain_name = self.CHAIN_MAP.get(self._chain_id, "ethereum")
        self._session = requests.Session()
        self._cache: dict[str, tuple[Decimal, float]] = {}
        self._cache_ttl = 60  # seconds

    def get_price_usd(self, token_address: str) -> Decimal | None:
        """Get token price in USD from DefiLlama."""
        # Check cache
        cache_key = token_address.lower()
        if cache_key in self._cache:
            price, timestamp = self._cache[cache_key]
            if time.time() - timestamp < self._cache_ttl:
                return price

        try:
            coin_id = f"{self._chain_name}:{token_address}"
            url = f"{self.BASE_URL}/prices/current/{coin_id}"

            response = self._session.get(url, timeout=10)
            response.raise_for_status()

            data = response.json()
            coins = data.get("coins", {})

            if coin_id in coins:
                price = Decimal(str(coins[coin_id]["price"]))
                self._cache[cache_key] = (price, time.time())
                return price

            return None

        except Exception as e:
            logger.debug(f"DefiLlama price fetch failed for {token_address}: {e}")
            return None


class PriceProvider:
    """
    Composite price provider with fallback chain.

    Priority:
    1. On-chain Spot Price Oracle
    2. CoinGecko API
    3. DefiLlama API
    """

    def __init__(
        self,
        oracle: OraclePriceSource | None = None,
        coingecko: CoinGeckoPriceSource | None = None,
        defillama: DefiLlamaPriceSource | None = None,
    ) -> None:
        """
        Initialize price provider.

        Args:
            oracle: On-chain oracle price source.
            coingecko: CoinGecko API price source.
            defillama: DefiLlama API price source.
        """
        self._oracle = oracle
        self._coingecko = coingecko
        self._defillama = defillama
        self._cache: dict[str, PriceResult] = {}
        self._cache_ttl = 60  # seconds

    def get_price_usd(
        self,
        token_address: str,
        raise_on_failure: bool = False,
    ) -> PriceResult | None:
        """
        Get token price in USD.

        Attempts each source in order until one succeeds.

        Args:
            token_address: Token contract address.
            raise_on_failure: Whether to raise exception if all sources fail.

        Returns:
            PriceResult or None if not found.

        Raises:
            PriceNotAvailableError: If raise_on_failure and all sources fail.
        """
        # Check cache
        cache_key = token_address.lower()
        if cache_key in self._cache:
            cached = self._cache[cache_key]
            if time.time() - cached.timestamp < self._cache_ttl:
                return cached

        sources_tried: list[str] = []

        # Try oracle first
        if self._oracle:
            sources_tried.append("oracle")
            price = self._oracle.get_price_usd(token_address)
            if price is not None:
                result = PriceResult(
                    price=price,
                    source="oracle",
                    timestamp=int(time.time()),
                )
                self._cache[cache_key] = result
                return result

        # Try CoinGecko second
        if self._coingecko:
            sources_tried.append("coingecko")
            price = self._coingecko.get_price_usd(token_address)
            if price is not None:
                result = PriceResult(
                    price=price,
                    source="coingecko",
                    timestamp=int(time.time()),
                )
                self._cache[cache_key] = result
                return result

        # Try DefiLlama third
        if self._defillama:
            sources_tried.append("defillama")
            price = self._defillama.get_price_usd(token_address)
            if price is not None:
                result = PriceResult(
                    price=price,
                    source="defillama",
                    timestamp=int(time.time()),
                )
                self._cache[cache_key] = result
                return result

        if raise_on_failure:
            raise PriceNotAvailableError(token_address, sources_tried)

        return None

    def get_prices_batch(
        self,
        token_addresses: list[str],
    ) -> dict[str, PriceResult | None]:
        """
        Get prices for multiple tokens.

        Args:
            token_addresses: List of token addresses.

        Returns:
            Dictionary mapping addresses to PriceResults.
        """
        results: dict[str, PriceResult | None] = {}

        for address in token_addresses:
            results[address] = self.get_price_usd(address)

        return results

    def clear_cache(self) -> None:
        """Clear the price cache."""
        self._cache.clear()
