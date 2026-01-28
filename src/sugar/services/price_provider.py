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
    import pandas as pd

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

    # Known stablecoin addresses per chain (normalized to lowercase)
    # These return $1.00 directly without oracle lookup
    STABLECOINS = {
        # Base
        "0x833589fcd6edb6e08f4c7c32d4f71b54bda02913",  # USDC
        "0xd9aaec86b65d86f6a7b5b1b0c42ffa531710b6ca",  # USDbC
        "0xb79dd08ea68a908a97220c76d19a6aa9cbde4376",  # USD+
        "0xcfa3ef56d303ae4faaba0592388f19d7c3399fb4",  # eUSD
        "0x4621b7a9c75199271f773ebd9a499dbd165c3191",  # DOLA
        "0x50c5725949a6f0c72e6c4a641f24049a917db0cb",  # DAI
        # Optimism
        "0x0b2c639c533813f4aa9d7837caf62653d097ff85",  # USDC
        "0x94b008aa00579c1307b0ef2c499ad98a8ce58e58",  # USDT
        "0x2e3d870790dc77a83dd1d18184acc7439a53f475",  # FRAX
        "0x73cb180bf0521828d8849bc8cf2b920918e23032",  # USD+
        "0xda10009cbd5d07dd0cecc66161fc93d7c9000da1",  # DAI
        "0xbfd291da8a403daaf7e5e9dc1ec0aceacd4848b9",  # USX
        "0x8c6f28f2f1a3c87f0f938b96d27520d9751ec8d9",  # sUSD
        "0xc40f949f8a4e094d1b49a23ea9241d289b7b2819",  # LUSD
        # Mode
        "0x1217bfe6c773eec6cc4a38b5dc45b92292b6e189",  # oUSDT
        # Lisk
        "0x43f2376d5d03553ae72f4a8093bbe9de4336eb08",  # USDT0
        # Soneium
        "0xba9986d2381edf1da03b0b9c1f8b00dc4aacc369",  # USDC.e
        # Unichain
        "0x078d782b760474a361dda0af3839290b0ef57ad6",  # USDC
        # Superseed
        "0x1217bfe6c773eec6cc4a38b5dc45b92292b6e189",  # oUSDT
        # Metal
        "0x51e85d70944256710cb141847f1a04f568c1db0e",  # USDC.e
        # Swell
        "0x5d3a1ff2b6bab83b63cd9ad0787074081a52ef34",  # USDe
        # Fraxtal
        "0xfc00000000000000000000000000000000000001",  # frxUSD
        "0xdcc0f2d8f90fde85b10ac1c8ab57dc0ae946a543",  # USDC
        # Celo
        "0x48065fbbe25f71c9282ddf5e1cd6d6a887483d5e",  # USDT
        # Ink
        "0x0200c29006150606b650577bbe7b6248f58470c1",  # USDT0
    }

    # WETH address (same on all OP Stack chains)
    WETH_ADDRESS = "0x4200000000000000000000000000000000000006"

    # Known token decimals (for oracle rate adjustment)
    # Maps lowercase address -> decimals
    # Only needed for tokens that don't have 18 decimals
    KNOWN_DECIMALS: dict[str, int] = {
        # 6 decimal tokens
        "0x833589fcd6edb6e08f4c7c32d4f71b54bda02913": 6,  # Base USDC
        "0xd9aaec86b65d86f6a7b5b1b0c42ffa531710b6ca": 6,  # Base USDbC
        "0x0b2c639c533813f4aa9d7837caf62653d097ff85": 6,  # OP USDC
        "0x94b008aa00579c1307b0ef2c499ad98a8ce58e58": 6,  # OP USDT
        "0x60a3e35cc302bfa44cb288bc5a4f316fdb1adb42": 6,  # Base EURC
        "0xba9986d2381edf1da03b0b9c1f8b00dc4aacc369": 6,  # Soneium USDC.e
        "0x078d782b760474a361dda0af3839290b0ef57ad6": 6,  # Unichain USDC
        "0x51e85d70944256710cb141847f1a04f568c1db0e": 6,  # Metal USDC.e
        "0xdcc0f2d8f90fde85b10ac1c8ab57dc0ae946a543": 6,  # Fraxtal USDC
        "0x1217bfe6c773eec6cc4a38b5dc45b92292b6e189": 6,  # Mode/Superseed oUSDT
        "0x43f2376d5d03553ae72f4a8093bbe9de4336eb08": 6,  # Lisk USDT0
        "0x48065fbbe25f71c9282ddf5e1cd6d6a887483d5e": 6,  # Celo USDT
        "0x0200c29006150606b650577bbe7b6248f58470c1": 6,  # Ink USDT0
        # 8 decimal tokens
        "0xcbb7c0000ab88b473b1f5afd9ef808440eed33bf": 8,  # Base cbBTC
        "0x03c7054bcb39f7b2e5b2c7acb37583e32d70cfa3": 8,  # Lisk WBTC
        "0x6f36dbd829de9b7e077db8a35b480d4329ceb331": 8,  # Superseed cbBTC
        "0x6c84a8f1c29108f47a79964b5fe888d4f4d0de40": 8,  # OP tBTC
        "0x73e0c0d45e048d25fc26fa3159b0aa04bfa4db98": 8,  # Ink kBTC
    }

    def __init__(
        self,
        oracle: SpotPriceOracle,
        usdc_address: str | None = None,
        tokens_df: "pd.DataFrame | None" = None,
    ) -> None:
        """
        Initialize oracle price source.

        Args:
            oracle: SpotPriceOracle contract wrapper.
            usdc_address: USDC address on this chain for USD conversion.
            tokens_df: Optional token metadata DataFrame with decimals column.
        """
        self._oracle = oracle
        self._usdc_address = usdc_address
        self._tokens_df = tokens_df
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
                # Adjust rate for stablecoin decimals (USDC is 6 decimals)
                adjusted_rate = self._adjust_rate_for_decimals(rates[0], stablecoin)
                # adjusted_rate = how many ETH for 1 USDC
                # So ETH/USD = 1 / adjusted_rate
                self._eth_usd_rate = Decimal("1") / adjusted_rate
                self._eth_usd_timestamp = time.time()
                logger.debug(f"ETH/USD rate: {self._eth_usd_rate}")
                return self._eth_usd_rate
        except Exception as e:
            logger.debug(f"Failed to get ETH/USD rate: {e}")

        # Fallback
        return Decimal("3000")

    def _is_stablecoin(self, token_address: str) -> bool:
        """Check if token is a known stablecoin."""
        return token_address.lower() in self.STABLECOINS

    def _get_token_decimals(self, token_address: str) -> int:
        """
        Get token decimals for oracle rate adjustment.

        Args:
            token_address: Token address.

        Returns:
            Token decimals (defaults to 18 if unknown).
        """
        addr_lower = token_address.lower()

        # Check known decimals first
        if addr_lower in self.KNOWN_DECIMALS:
            return self.KNOWN_DECIMALS[addr_lower]

        # Check tokens DataFrame if available
        if self._tokens_df is not None and token_address in self._tokens_df.index:
            try:
                return int(self._tokens_df.loc[token_address, "decimals"])
            except (KeyError, ValueError):
                pass

        # Default to 18 decimals
        return 18

    def _adjust_rate_for_decimals(
        self, rate: Decimal, token_address: str
    ) -> Decimal:
        """
        Adjust oracle rate for token decimals.

        The oracle returns rates assuming 10^18 smallest token units.
        For tokens with D decimals, we need to multiply by 10^(D-18).

        Args:
            rate: Raw rate from oracle (already divided by 10^18).
            token_address: Token address.

        Returns:
            Adjusted rate for 1 whole token.
        """
        decimals = self._get_token_decimals(token_address)
        if decimals == 18:
            return rate

        # Adjust for non-18 decimal tokens
        adjustment = Decimal(10) ** (decimals - 18)
        return rate * adjustment

    def set_tokens_df(self, tokens_df: "pd.DataFrame") -> None:
        """
        Set token metadata DataFrame for decimal lookups.

        Args:
            tokens_df: Token metadata DataFrame indexed by address.
        """
        self._tokens_df = tokens_df

    def get_price_usd(self, token_address: str) -> Decimal | None:
        """Get token price in USD via oracle (uses cache)."""
        token_lower = token_address.lower()

        # If token is a stablecoin, return 1
        if self._is_stablecoin(token_address):
            return Decimal("1.0")

        # If token is WETH, return ETH/USD rate
        if token_lower == self.WETH_ADDRESS.lower():
            return self._get_eth_usd_rate()

        # Check cache for ETH-denominated price (already decimal-adjusted)
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
                # Adjust rate for token decimals before caching
                adjusted_rate = self._adjust_rate_for_decimals(rates[0], token_address)
                self._eth_price_cache[token_lower] = adjusted_rate
                return adjusted_rate * self._get_eth_usd_rate()
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
            if self._is_stablecoin(addr):
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
                # Cache the results (adjusted for decimals)
                for j, addr in enumerate(batch):
                    if j < len(rates):
                        # Adjust rate for token decimals before caching
                        adjusted_rate = self._adjust_rate_for_decimals(rates[j], addr)
                        self._eth_price_cache[addr.lower()] = adjusted_rate
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
