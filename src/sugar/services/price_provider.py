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

# Batch size for oracle price queries (to avoid RPC errors)
ORACLE_BATCH_SIZE = 15


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

    Uses batch getManyRatesToEthWithCustomConnectors for efficient pricing.
    Converts ETH prices to USD using stablecoin rates.
    """

    # Known stablecoin addresses per chain (for ETH/USD conversion)
    STABLECOINS = {
        # Base
        "0x833589fcd6edb6e08f4c7c32d4f71b54bda02913": "USDC",  # Base USDC
        # Optimism
        "0x0b2c639c533813f4aa9d7837caf62653d097ff85": "USDC",  # OP USDC
        "0x94b008aa00579c1307b0ef2c499ad98a8ce58e58": "USDT",  # OP USDT
    }

    # WETH address (same on all OP Stack chains)
    WETH_ADDRESS = "0x4200000000000000000000000000000000000006"

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
        # Cache for individual token prices (ETH-denominated)
        self._eth_price_cache: dict[str, Decimal] = {}
        # Cached ETH/USD rate
        self._eth_usd_rate: Decimal | None = None
        self._eth_usd_timestamp: float = 0
        self._eth_usd_ttl = 60  # seconds

    def _get_eth_usd_rate(self) -> Decimal:
        """
        Get the ETH/USD rate using the first connector (stablecoin).

        The first connector in the list is always a stablecoin (USDC),
        so 1 stablecoin / ETH gives us ETH price in USD terms.
        """
        # Check cache
        if (
            self._eth_usd_rate is not None
            and time.time() - self._eth_usd_timestamp < self._eth_usd_ttl
        ):
            return self._eth_usd_rate

        # Use the first connector (USDC) to get ETH price
        # The rate returned is: how many USDC for 1 ETH
        connectors = self._oracle.connectors
        if not connectors:
            # Fallback: assume ETH = $3000 if no connectors
            return Decimal("3000")

        stablecoin = connectors[0]  # First connector is USDC

        try:
            # Get USDC/ETH rate (how many ETH for 1 USDC)
            rates = self._oracle.get_many_rates_to_eth(
                src_tokens=[stablecoin],
                use_wrappers=False,
                threshold=10,
            )
            if rates and rates[0] > 0:
                # rates[0] = how many ETH for 1 USDC
                # So ETH/USD = 1 / rates[0]
                self._eth_usd_rate = Decimal("1") / rates[0]
                self._eth_usd_timestamp = time.time()
                logger.debug(f"ETH/USD rate: {self._eth_usd_rate}")
                return self._eth_usd_rate
        except Exception as e:
            logger.debug(f"Failed to get ETH/USD rate: {e}")

        # Fallback
        return Decimal("3000")

    def get_price_usd(self, token_address: str) -> Decimal | None:
        """Get token price in USD via oracle (uses cache)."""
        token_lower = token_address.lower()

        # If token is a stablecoin, return 1
        if token_lower in self.STABLECOINS:
            return Decimal("1.0")

        # If token is WETH, return ETH/USD rate
        if token_lower == self.WETH_ADDRESS.lower():
            return self._get_eth_usd_rate()

        # Check cache for ETH-denominated price
        if token_lower in self._eth_price_cache:
            eth_price = self._eth_price_cache[token_lower]
            if eth_price > 0:
                return eth_price * self._get_eth_usd_rate()
            return None

        # Not in cache - fetch individually (should be rare after batch prefetch)
        try:
            rates = self._oracle.get_many_rates_to_eth(
                src_tokens=[token_address],
                use_wrappers=False,
                threshold=10,
            )
            if rates and rates[0] > 0:
                self._eth_price_cache[token_lower] = rates[0]
                return rates[0] * self._get_eth_usd_rate()
        except Exception as e:
            logger.debug(f"Oracle price fetch failed for {token_address}: {e}")

        return None

    def prefetch_prices(self, token_addresses: list[str]) -> None:
        """
        Batch prefetch prices for multiple tokens.

        Uses getManyRatesToEthWithCustomConnectors with batches of 15 tokens.
        Results are cached for subsequent get_price_usd calls.

        Args:
            token_addresses: List of token addresses to prefetch.
        """
        # Filter out already cached tokens and stablecoins
        tokens_to_fetch = []
        for addr in token_addresses:
            addr_lower = addr.lower()
            if addr_lower in self._eth_price_cache:
                continue
            if addr_lower in self.STABLECOINS:
                continue
            if addr_lower == self.WETH_ADDRESS.lower():
                continue
            tokens_to_fetch.append(addr)

        if not tokens_to_fetch:
            return

        # Fetch ETH/USD rate first (will be needed for all conversions)
        self._get_eth_usd_rate()

        # Batch fetch in groups of ORACLE_BATCH_SIZE
        for i in range(0, len(tokens_to_fetch), ORACLE_BATCH_SIZE):
            batch = tokens_to_fetch[i : i + ORACLE_BATCH_SIZE]
            try:
                rates = self._oracle.get_many_rates_to_eth(
                    src_tokens=batch,
                    use_wrappers=False,
                    threshold=10,
                )
                # Cache the results
                for j, addr in enumerate(batch):
                    if j < len(rates):
                        self._eth_price_cache[addr.lower()] = rates[j]
            except Exception as e:
                logger.warning(f"Batch price fetch failed for {len(batch)} tokens: {e}")
                # Cache zeros for failed tokens so we don't retry
                for addr in batch:
                    self._eth_price_cache[addr.lower()] = Decimal(0)

    def clear_cache(self) -> None:
        """Clear the price cache."""
        self._eth_price_cache.clear()
        self._eth_usd_rate = None


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
    1. On-chain Spot Price Oracle (with batch prefetching)
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

    def prefetch_prices(self, token_addresses: list[str]) -> None:
        """
        Batch prefetch prices for multiple tokens.

        This should be called before processing pools to minimize RPC calls.
        Only the oracle source supports batch prefetching.

        Args:
            token_addresses: List of token addresses to prefetch.
        """
        if self._oracle:
            self._oracle.prefetch_prices(token_addresses)

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
        # Prefetch all tokens first
        self.prefetch_prices(token_addresses)

        # Then get individual prices (will use cache)
        results: dict[str, PriceResult | None] = {}
        for address in token_addresses:
            results[address] = self.get_price_usd(address)

        return results

    def clear_cache(self) -> None:
        """Clear the price cache."""
        self._cache.clear()
        if self._oracle:
            self._oracle.clear_cache()
