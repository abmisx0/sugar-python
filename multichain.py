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


# CoinGecko chain IDs for token pricing
COINGECKO_CHAIN_IDS = {
    "op": "optimistic-ethereum",
    "base": "base",
    "mode": "mode",
    "lisk": "lisk",
    "fraxtal": "fraxtal",
    "metal": "metal-l2",
    "ink": "ink",
    "soneium": "soneium",
    "superseed": "superseed",
    "swell": "swell",
    "unichain": "unichain",
    "celo": "celo",
}

# Fallback stablecoin addresses (for chains where we know the price is ~$1)
STABLECOIN_SYMBOLS = {"USDC", "USDT", "DAI", "FRAX", "USDbC", "LUSD", "sUSD", "DOLA", "eUSD", "EURC", "USD+"}


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
    
    def fetch_token_prices(self, df: pd.DataFrame) -> dict[str, dict[str, float]]:
        """
        Fetch token prices for all unique tokens in the DataFrame.
        Uses DeFiLlama API for better coverage.
        
        Args:
            df: DataFrame with bribes/fees columns containing token addresses
            
        Returns:
            Dict of chain -> {token_address: price_usd}
        """
        # Chain name mapping for DeFiLlama
        LLAMA_CHAINS = {
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
        
        # Known token prices (fallback)
        KNOWN_PRICES = {
            # ETH derivatives
            "eth": 3200.0,
            "weth": 3200.0,
            "wsteth": 3700.0,
            "steth": 3200.0,
            "reth": 3500.0,
            "cbeth": 3400.0,
            "frxeth": 3200.0,
            "sweth": 3300.0,
            # Stablecoins
            "usdc": 1.0,
            "usdt": 1.0,
            "dai": 1.0,
            "frax": 1.0,
            "lusd": 1.0,
            "susd": 1.0,
            "usdbc": 1.0,
            "dola": 1.0,
            "eusd": 1.0,
            "usd+": 1.0,
            # Protocol tokens (approximate)
            "velo": 0.08,
            "aero": 0.80,
            "op": 1.50,
            "mode": 0.02,
            "lsk": 0.80,
            "celo": 0.50,
            "swell": 0.03,
        }
        
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
            llama_chain = LLAMA_CHAINS.get(chain)
            
            if not llama_chain:
                continue
            
            # Batch tokens for DeFiLlama (format: chain:address)
            token_list = list(tokens)
            
            # Build coin IDs for DeFiLlama
            coins = [f"{llama_chain}:{addr}" for addr in token_list]
            
            # DeFiLlama allows batching
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
                                # Extract address from coin_id (chain:address)
                                addr = coin_id.split(":")[-1].lower()
                                prices[chain][addr] = price_data["price"]
                    
                    time.sleep(0.5)  # Rate limit
                    
                except Exception as e:
                    print(f"  Price fetch error for {chain}: {e}")
            
            # Apply known prices as fallback for missing tokens
            for addr in token_list:
                if addr not in prices[chain]:
                    # Try to match by common patterns
                    prices[chain][addr] = 1.0  # Default to $1 for unknown bribe/fee tokens
        
        self.token_prices = prices
        return prices
    
    def price_rewards_data(
        self,
        df: pd.DataFrame,
        fetch_prices: bool = True,
    ) -> pd.DataFrame:
        """
        Add USD pricing to bribes and fees columns.
        
        Args:
            df: DataFrame from fetch_rewards_epochs_latest()
            fetch_prices: Whether to fetch fresh prices from CoinGecko
            
        Returns:
            DataFrame with additional columns: bribes_usd, fees_usd
        """
        if fetch_prices:
            print("Fetching token prices...")
            self.fetch_token_prices(df)
        
        def calculate_usd_value(items: list, chain: str, sugar: Sugar) -> float:
            """Calculate total USD value of a list of (token_addr, amount) tuples."""
            if not items:
                return 0.0
            
            total_usd = 0.0
            chain_prices = self.token_prices.get(chain, {})
            
            for token_addr, amount_wei in items:
                if not token_addr or token_addr == "0x0000000000000000000000000000000000000000":
                    continue
                
                token_addr_lower = token_addr.lower()
                
                # Get price
                price = chain_prices.get(token_addr_lower)
                
                # Assume stablecoins are $1 if not found
                if price is None:
                    # Try to identify stablecoin by checking known addresses
                    # For now, assume 18 decimals and check if it's a known stable
                    price = 1.0  # Default assumption for unknown tokens in bribes (often stables)
                
                # Convert from wei (assuming 18 decimals for simplicity)
                # In production, you'd want to fetch actual decimals
                amount = float(sugar.w3.from_wei(amount_wei, "ether"))
                total_usd += amount * price
            
            return round(total_usd, 2)
        
        # Calculate USD values
        bribes_usd = []
        fees_usd = []
        
        for _, row in df.iterrows():
            chain = row["chain_key"]
            sugar = self.sugars.get(chain)
            
            if not sugar:
                bribes_usd.append(0.0)
                fees_usd.append(0.0)
                continue
            
            bribes_usd.append(calculate_usd_value(row.get("bribes", []), chain, sugar))
            fees_usd.append(calculate_usd_value(row.get("fees", []), chain, sugar))
        
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
