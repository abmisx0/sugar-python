"""
Multi-chain aggregator for Sugar data.
Fetches LP and Rewards data across all chains and combines into unified DataFrames.
"""

import os
import time
import requests
import pandas as pd
from decimal import Decimal
from typing import Optional
from concurrent.futures import ThreadPoolExecutor, as_completed

from sugar import Sugar
from chains import CHAINS, list_chains
import config


# 1inch OffchainOracle addresses (spot price aggregator)
# https://github.com/1inch/spot-price-aggregator
SPOT_ORACLE_ADDRESSES = {
    "op": "0x00000000000D6FFc74A8feb35aF5827bf57f6786",
    "base": "0x00000000000D6FFc74A8feb35aF5827bf57f6786",
    "unichain": "0x00000000000D6FFc74A8feb35aF5827bf57f6786",
    # Other chains may not have the oracle deployed
}

# USDC addresses for USD conversion (used as quote token)
USDC_ADDRESSES = {
    "op": "0x0b2C639c533813f4Aa9D7837CAf62653d097Ff85",
    "base": "0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913",
    "mode": "0xd988097fb8612cc24eeC14542bC03424c656005f",
    "lisk": "0xF242275d3a6527d877f2c927a82D9b057609cc71",
    "fraxtal": "0xDcc0F2D8F90FDe85b10aC1c8Ab57dc0AE946A543",
    "ink": "0xF1815bd50389c46847f0Bda824eC8da914045D14",
    "soneium": "0xBA9986D2381edf1DA03B0B9c1f8b00dC4AacC369",
    "superseed": "0x08052a94b1c0Bd6FED95F57a6f8BFE51d6040B3b",
    "swell": "0x082ECA5aC396670A85E0892a9BBF920B4C191bc0",
    "unichain": "0x078D782b760474a361dDA0AF3839290b0EF57AD6",
    "celo": "0xcebA9300f2b948710d2653dD7B07f33A8B32118C",
    "metal": "0xb8d74e8b46D02aCE72F7A8B3F80C9607dBa9B5F4",
}

# DeFiLlama chain IDs for fallback pricing
LLAMA_CHAIN_IDS = {
    "op": "optimism",
    "base": "base",
    "mode": "mode",
    "lisk": "lisk",
    "fraxtal": "fraxtal",
    "metal": "metal",
    "ink": "ink",
    "soneium": "soneium",
    "superseed": "superseed",
    "swell": "swell",
    "unichain": "unichain",
    "celo": "celo",
}

# Spot price oracle ABI (1inch OffchainOracle)
SPOT_ORACLE_ABI = '[{"inputs":[{"internalType":"contract IERC20","name":"srcToken","type":"address"},{"internalType":"contract IERC20","name":"dstToken","type":"address"},{"internalType":"bool","name":"useWrappers","type":"bool"}],"name":"getRate","outputs":[{"internalType":"uint256","name":"weightedRate","type":"uint256"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"contract IERC20","name":"srcToken","type":"address"},{"internalType":"bool","name":"useSrcWrappers","type":"bool"}],"name":"getRateToEth","outputs":[{"internalType":"uint256","name":"weightedRate","type":"uint256"}],"stateMutability":"view","type":"function"}]'


class MultiChainSugar:
    """Aggregates Sugar data across multiple chains."""
    
    def __init__(self, chains: Optional[list[str]] = None):
        """
        Initialize multi-chain aggregator.
        
        Args:
            chains: List of chain keys to use. Defaults to all chains.
        """
        self.chain_keys = chains or list_chains()
        self.sugars: dict[str, Sugar] = {}
        self.token_prices: dict[str, dict[str, float]] = {}  # chain -> {address: price_usd}
        self._init_chains()
    
    def _init_chains(self):
        """Initialize Sugar instances for each chain."""
        for chain in self.chain_keys:
            try:
                self.sugars[chain] = Sugar(chain)
                print(f"✓ {chain}: connected")
            except Exception as e:
                print(f"✗ {chain}: {e}")
    
    def fetch_lp_all(
        self,
        limit: int = 500,
        parallel: bool = False,  # Sequential by default to avoid rate limits
        active_only: bool = True,
        delay: float = 0.5,
        max_retries: int = 3,
    ) -> pd.DataFrame:
        """
        Fetch LpSugar.all() from all chains and combine into one DataFrame.
        
        Args:
            limit: Max pools per pagination call
            parallel: Whether to fetch chains in parallel
            active_only: Only include pools with active gauges (gauge_alive=True)
            delay: Delay between pagination calls (seconds)
            max_retries: Max retries on rate limit errors
            
        Returns:
            Combined DataFrame with chain_id and chain_name columns
        """
        results = []
        
        def fetch_chain(chain: str) -> Optional[pd.DataFrame]:
            try:
                sugar = self.sugars.get(chain)
                if not sugar:
                    return None
                
                print(f"Fetching LPs from {chain}...")
                
                # Paginated fetch with retry logic
                all_lps = []
                offset = 0
                retries = 0
                
                while True:
                    try:
                        batch = sugar.lp.functions.all(limit, offset, 0).call()
                        
                        if not batch:
                            break
                        
                        all_lps.extend(batch)
                        print(f"  {chain}: fetched {len(all_lps)} pools (offset={offset})")
                        
                        if len(batch) < limit:
                            # Last page
                            break
                        
                        offset += limit
                        retries = 0  # Reset retries on success
                        time.sleep(delay)  # Rate limit protection
                        
                    except Exception as e:
                        error_str = str(e).lower()
                        if "429" in error_str or "rate" in error_str or "too many" in error_str:
                            retries += 1
                            if retries <= max_retries:
                                wait_time = delay * (2 ** retries)  # Exponential backoff
                                print(f"  {chain}: rate limited, waiting {wait_time}s (retry {retries}/{max_retries})")
                                time.sleep(wait_time)
                                continue
                        print(f"  {chain} error at offset {offset}: {e}")
                        break
                
                if not all_lps:
                    return None
                
                # Create DataFrame
                chain_config = CHAINS[chain]
                df = pd.DataFrame(all_lps, columns=config.COLUMNS_LP)
                df["chain_id"] = chain_config["chain_id"]
                df["chain_name"] = chain_config["name"]
                df["chain_key"] = chain
                
                # Filter to active gauges only
                if active_only:
                    df = df[df["gauge_alive"] == True].copy()
                
                print(f"  {chain}: {len(df)} pools" + (" (active gauges)" if active_only else ""))
                return df
                
            except Exception as e:
                print(f"  {chain} error: {e}")
                return None
        
        if parallel:
            with ThreadPoolExecutor(max_workers=4) as executor:
                futures = {executor.submit(fetch_chain, c): c for c in self.sugars.keys()}
                for future in as_completed(futures):
                    df = future.result()
                    if df is not None:
                        results.append(df)
        else:
            for chain in self.sugars.keys():
                df = fetch_chain(chain)
                if df is not None:
                    results.append(df)
        
        if not results:
            return pd.DataFrame()
        
        return pd.concat(results, ignore_index=True)
    
    def fetch_rewards_epochs_latest(
        self,
        limit: int = 200,
        parallel: bool = False,  # Sequential by default
        delay: float = 0.5,
        max_retries: int = 3,
    ) -> pd.DataFrame:
        """
        Fetch RewardsSugar.epochsLatest() from all chains and combine.
        Only returns pools with active gauges (by design of the contract).
        
        Args:
            limit: Max epochs to fetch per pagination call
            parallel: Whether to fetch chains in parallel
            delay: Delay between pagination calls (seconds)
            max_retries: Max retries on rate limit errors
            
        Returns:
            Combined DataFrame with chain info and parsed bribes/fees
        """
        results = []
        
        def fetch_chain(chain: str) -> Optional[pd.DataFrame]:
            try:
                sugar = self.sugars.get(chain)
                if not sugar or not sugar.rewards:
                    return None
                
                print(f"Fetching epochs from {chain}...")
                
                # Paginated fetch with retry logic
                all_epochs = []
                offset = 0
                retries = 0
                
                while True:
                    try:
                        batch = sugar.rewards.functions.epochsLatest(limit, offset).call()
                        
                        if not batch:
                            break
                        
                        all_epochs.extend(batch)
                        print(f"  {chain}: fetched {len(all_epochs)} epochs (offset={offset})")
                        
                        if len(batch) < limit:
                            # Last page
                            break
                        
                        offset += limit
                        retries = 0
                        time.sleep(delay)
                        
                    except Exception as e:
                        error_str = str(e).lower()
                        if "429" in error_str or "rate" in error_str or "too many" in error_str:
                            retries += 1
                            if retries <= max_retries:
                                wait_time = delay * (2 ** retries)
                                print(f"  {chain}: rate limited, waiting {wait_time}s (retry {retries}/{max_retries})")
                                time.sleep(wait_time)
                                continue
                        print(f"  {chain} error at offset {offset}: {e}")
                        break
                
                if not all_epochs:
                    return None
                
                # Create DataFrame
                chain_config = CHAINS[chain]
                df = pd.DataFrame(all_epochs, columns=config.COLUMNS_REWARDS_EPOCH)
                df["chain_id"] = chain_config["chain_id"]
                df["chain_name"] = chain_config["name"]
                df["chain_key"] = chain
                
                # Convert wei values
                df["votes"] = df["votes"].apply(lambda x: float(sugar.w3.from_wei(x, "ether")))
                df["emissions"] = df["emissions"].apply(lambda x: float(sugar.w3.from_wei(x, "ether")))
                
                print(f"  {chain}: {len(df)} epochs (active gauges)")
                return df
                
            except Exception as e:
                print(f"  {chain} error: {e}")
                return None
        
        if parallel:
            with ThreadPoolExecutor(max_workers=4) as executor:
                futures = {executor.submit(fetch_chain, c): c for c in self.sugars.keys()}
                for future in as_completed(futures):
                    df = future.result()
                    if df is not None:
                        results.append(df)
        else:
            for chain in self.sugars.keys():
                df = fetch_chain(chain)
                if df is not None:
                    results.append(df)
        
        if not results:
            return pd.DataFrame()
        
        return pd.concat(results, ignore_index=True)
    
    def _get_spot_oracle_prices_batch(self, chain: str, token_addrs: list[str]) -> dict[str, float]:
        """
        Get token prices from 1inch spot price oracle for multiple tokens.
        Returns dict of {token_addr: price_usd}.
        """
        sugar = self.sugars.get(chain)
        if not sugar:
            return {}
        
        oracle_addr = SPOT_ORACLE_ADDRESSES.get(chain)
        usdc_addr = USDC_ADDRESSES.get(chain)
        
        if not oracle_addr or not usdc_addr:
            return {}
        
        prices = {}
        oracle = sugar.w3.eth.contract(
            address=sugar.w3.to_checksum_address(oracle_addr),
            abi=SPOT_ORACLE_ABI
        )
        
        for token_addr in token_addrs:
            try:
                # Get token decimals (cached)
                src_decimals = self._get_token_decimals(chain, token_addr)
                dst_decimals = 6  # USDC always 6 decimals
                
                # Get rate: token -> USDC
                rate = oracle.functions.getRate(
                    sugar.w3.to_checksum_address(token_addr),
                    sugar.w3.to_checksum_address(usdc_addr),
                    True  # useWrappers
                ).call()
                
                if rate > 0:
                    # Price = rate * 10^srcDecimals / 10^18 / 10^dstDecimals
                    price = rate * (10 ** src_decimals) / (10 ** 18) / (10 ** dst_decimals)
                    if price > 0:
                        prices[token_addr.lower()] = price
                        
            except Exception:
                # Oracle doesn't have this token
                pass
        
        return prices
    
    def fetch_token_prices(self, df: pd.DataFrame) -> dict[str, dict[str, float]]:
        """
        Fetch token prices using:
        1. Spot price oracle (1inch) - primary
        2. DeFiLlama API - fallback
        3. $0 for unknown tokens
        
        Args:
            df: DataFrame with bribes/fees columns containing token addresses
            
        Returns:
            Dict of chain -> {token_address: price_usd}
        """
        # Collect all unique tokens per chain
        tokens_by_chain: dict[str, set[str]] = {}
        
        for _, row in df.iterrows():
            chain = row["chain_key"]
            if chain not in tokens_by_chain:
                tokens_by_chain[chain] = set()
            
            for col in ["bribes", "fees"]:
                if col in row and row[col]:
                    for token_addr, amount in row[col]:
                        if token_addr and token_addr != "0x0000000000000000000000000000000000000000":
                            tokens_by_chain[chain].add(token_addr.lower())
        
        prices: dict[str, dict[str, float]] = {}
        
        for chain, tokens in tokens_by_chain.items():
            if not tokens:
                continue
                
            prices[chain] = {}
            token_list = list(tokens)
            
            # Step 1: Try spot price oracle (batch)
            oracle_available = chain in SPOT_ORACLE_ADDRESSES
            if oracle_available:
                print(f"  {chain}: fetching {len(token_list)} prices from spot oracle...", flush=True)
                oracle_prices = self._get_spot_oracle_prices_batch(chain, token_list)
                prices[chain].update(oracle_prices)
                print(f"  {chain}: got {len(prices[chain])}/{len(token_list)} from oracle", flush=True)
            
            # Step 2: DeFiLlama fallback for missing tokens
            missing_tokens = [t for t in token_list if t not in prices[chain]]
            if missing_tokens:
                llama_chain = LLAMA_CHAIN_IDS.get(chain)
                if llama_chain:
                    print(f"  {chain}: fetching {len(missing_tokens)} prices from DeFiLlama...")
                    coins = [f"{llama_chain}:{addr}" for addr in missing_tokens]
                    
                    batch_size = 100
                    for i in range(0, len(coins), batch_size):
                        batch = coins[i:i+batch_size]
                        
                        try:
                            url = "https://coins.llama.fi/prices/current/" + ",".join(batch)
                            resp = requests.get(url, timeout=15)
                            
                            if resp.status_code == 200:
                                data = resp.json()
                                for coin_id, price_data in data.get("coins", {}).items():
                                    if "price" in price_data:
                                        addr = coin_id.split(":")[-1].lower()
                                        prices[chain][addr] = price_data["price"]
                            
                            time.sleep(0.3)
                            
                        except Exception as e:
                            print(f"  {chain}: DeFiLlama error: {e}")
            
            # Step 3: Unknown tokens get $0 (not $1)
            still_missing = [t for t in token_list if t not in prices[chain]]
            if still_missing:
                print(f"  {chain}: {len(still_missing)} tokens without price (set to $0)")
                for addr in still_missing:
                    prices[chain][addr] = 0.0
        
        self.token_prices = prices
        return prices
    
    def _get_token_decimals(self, chain: str, token_addr: str) -> int:
        """Get token decimals, default to 18 if unavailable."""
        sugar = self.sugars.get(chain)
        if not sugar:
            return 18
        
        # Check cache
        cache_key = f"{chain}:{token_addr.lower()}"
        if not hasattr(self, '_decimals_cache'):
            self._decimals_cache = {}
        if cache_key in self._decimals_cache:
            return self._decimals_cache[cache_key]
        
        try:
            # ERC20 decimals() call
            erc20_abi = '[{"inputs":[],"name":"decimals","outputs":[{"type":"uint8"}],"stateMutability":"view","type":"function"}]'
            contract = sugar.w3.eth.contract(
                address=sugar.w3.to_checksum_address(token_addr),
                abi=erc20_abi
            )
            decimals = contract.functions.decimals().call()
            self._decimals_cache[cache_key] = decimals
            return decimals
        except:
            return 18  # Default
    
    def price_rewards_data(
        self,
        df: pd.DataFrame,
        fetch_prices: bool = True,
    ) -> pd.DataFrame:
        """
        Add USD pricing to bribes and fees columns.
        Uses spot price oracle + DeFiLlama for pricing.
        
        Args:
            df: DataFrame from fetch_rewards_epochs_latest()
            fetch_prices: Whether to fetch fresh prices
            
        Returns:
            DataFrame with additional columns: bribes_usd, fees_usd
        """
        if fetch_prices:
            print("Fetching token prices...")
            self.fetch_token_prices(df)
        
        def calculate_usd_value(items: list, chain: str) -> float:
            """Calculate total USD value of a list of (token_addr, amount_wei) tuples."""
            if not items:
                return 0.0
            
            total_usd = 0.0
            chain_prices = self.token_prices.get(chain, {})
            
            for token_addr, amount_wei in items:
                if not token_addr or token_addr == "0x0000000000000000000000000000000000000000":
                    continue
                
                token_addr_lower = token_addr.lower()
                
                # Get price (0 if unknown)
                price = chain_prices.get(token_addr_lower, 0.0)
                if price <= 0:
                    continue
                
                # Get token decimals and convert amount
                decimals = self._get_token_decimals(chain, token_addr)
                amount = amount_wei / (10 ** decimals)
                
                total_usd += amount * price
            
            return round(total_usd, 2)
        
        # Calculate USD values
        bribes_usd = []
        fees_usd = []
        
        for _, row in df.iterrows():
            chain = row["chain_key"]
            
            bribes_usd.append(calculate_usd_value(row.get("bribes", []), chain))
            fees_usd.append(calculate_usd_value(row.get("fees", []), chain))
        
        df["bribes_usd"] = bribes_usd
        df["fees_usd"] = fees_usd
        df["total_incentives_usd"] = df["bribes_usd"] + df["fees_usd"]
        
        return df
    
    def fetch_all_data(
        self,
        include_lps: bool = True,
        include_epochs: bool = True,
        price_rewards: bool = True,
        active_gauges_only: bool = True,
    ) -> dict[str, pd.DataFrame]:
        """
        Fetch all data from all chains.
        
        Args:
            include_lps: Whether to fetch LP data
            include_epochs: Whether to fetch epoch/rewards data
            price_rewards: Whether to price bribes/fees in USD
            active_gauges_only: Only include pools with active gauges
        
        Returns:
            Dict with 'lps' and 'epochs' DataFrames
        """
        result = {}
        
        if include_lps:
            print("\n=== Fetching LP Data ===")
            result["lps"] = self.fetch_lp_all(active_only=active_gauges_only)
        
        if include_epochs:
            print("\n=== Fetching Epoch/Rewards Data ===")
            epochs_df = self.fetch_rewards_epochs_latest()
            
            if price_rewards and not epochs_df.empty:
                print("\n=== Pricing Rewards ===")
                epochs_df = self.price_rewards_data(epochs_df)
            
            result["epochs"] = epochs_df
        
        return result


def main():
    """Run multi-chain data fetch and export to CSV."""
    print("Initializing multi-chain Sugar...")
    mc = MultiChainSugar()
    
    print(f"\nConnected to {len(mc.sugars)} chains")
    
    # Fetch all data (active gauges only)
    data = mc.fetch_all_data(
        include_lps=True,
        include_epochs=True,
        price_rewards=True,
        active_gauges_only=True,
    )
    
    # Export to CSV
    output_dir = "data-multichain"
    os.makedirs(output_dir, exist_ok=True)
    
    if "lps" in data and not data["lps"].empty:
        lps_path = f"{output_dir}/all_chains_lps.csv"
        data["lps"].to_csv(lps_path, index=False)
        print(f"\n✓ Saved {len(data['lps'])} LPs to {lps_path}")
    
    if "epochs" in data and not data["epochs"].empty:
        epochs_path = f"{output_dir}/all_chains_epochs.csv"
        # Convert bribes/fees to string for CSV export
        export_df = data["epochs"].copy()
        export_df["bribes"] = export_df["bribes"].apply(str)
        export_df["fees"] = export_df["fees"].apply(str)
        export_df.to_csv(epochs_path, index=False)
        print(f"✓ Saved {len(data['epochs'])} epochs to {epochs_path}")
        
        # Summary stats
        print("\n=== Epoch Summary by Chain ===")
        summary = export_df.groupby("chain_name").agg({
            "lp": "count",
            "votes": "sum",
            "emissions": "sum",
            "bribes_usd": "sum",
            "fees_usd": "sum",
            "total_incentives_usd": "sum",
        }).round(2)
        summary.columns = ["pools", "total_votes", "total_emissions", "bribes_usd", "fees_usd", "total_usd"]
        print(summary.to_string())
    
    return data


if __name__ == "__main__":
    main()
