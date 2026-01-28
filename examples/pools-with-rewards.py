#!/usr/bin/env python3
"""
Example: Get pools with rewards data.

This demonstrates the combined LP + rewards data functionality
that fetches pool data along with latest epoch rewards and prices
the fees and incentives in USD.

Usage:
    python pools-with-rewards.py              # Default: Base chain only
    python pools-with-rewards.py --aero       # Aerodrome: Base chain only
    python pools-with-rewards.py --velo       # Velodrome: All other chains
    python pools-with-rewards.py --all        # All chains (Aero + Velo)
"""

import argparse
from pathlib import Path

import pandas as pd

from sugar import SugarClient, ChainId, set_progress_callback

# Aerodrome = Base only
AERO_CHAINS = [ChainId.BASE]

# Velodrome = All other chains
VELO_CHAINS = [
    ChainId.OPTIMISM,
    ChainId.MODE,
    ChainId.LISK,
    ChainId.FRAXTAL,
    ChainId.INK,
    ChainId.SONEIUM,
    ChainId.METAL,
    ChainId.CELO,
    ChainId.SUPERSEED,
    ChainId.SWELL,
    ChainId.UNICHAIN,
]


def rpc_progress_callback(
    chain: str, sugar_type: str, method: str, offset: int | None
) -> None:
    """Print RPC call progress."""
    if offset is not None:
        print(f"  RPC: {chain} | {sugar_type} | {method}(offset={offset})", flush=True)
    else:
        print(f"  RPC: {chain} | {sugar_type} | {method}()", flush=True)


def get_pools_with_rewards_for_chain(chain: ChainId) -> pd.DataFrame | None:
    """Get combined pool and rewards data for a single chain.

    Returns DataFrame with chain column added, or None if chain has no rewards.
    """
    client = SugarClient(chain)

    if not client.has_rewards():
        print(f"Rewards Sugar not available on {client.chain_name}")
        return None

    print(f"\n{'='*70}", flush=True)
    print(f"Fetching combined LP + rewards data for {client.chain_name}", flush=True)
    print(f"{'='*70}", flush=True)
    print(
        "This includes pool info, latest epoch rewards, and USD-priced fees/incentives",
        flush=True,
    )

    # Step 1: Get tokens
    print("\n[1/4] Fetching token metadata...", flush=True)
    tokens_df = client.get_tokens(listed_only=True)
    print(f"       Found {len(tokens_df)} listed tokens", flush=True)

    # Step 2: Get all pools
    print("\n[2/4] Fetching all liquidity pools...", flush=True)
    lp_df = client.get_pools()
    total_pools = len(lp_df)
    print(f"       Found {total_pools} total pools", flush=True)

    # Step 3: Get epoch rewards
    print("\n[3/4] Fetching latest epoch rewards...", flush=True)
    epochs_df = client.get_epochs_latest()
    pools_with_rewards = len(epochs_df)
    print(f"       Found {pools_with_rewards} pools with epoch rewards", flush=True)

    # Step 4: Combine and price data
    print("\n[4/4] Combining data and calculating USD prices...", flush=True)

    combined_df = client.processor.combine_lp_with_rewards(lp_df, epochs_df, tokens_df)

    print(f"       Processed {len(combined_df)} pools with USD pricing")

    # Add chain column
    combined_df["chain"] = client.chain_name

    # Summary
    print(f"\n{'='*70}")
    print("SUMMARY")
    print(f"{'='*70}")
    print(f"Total pools: {total_pools}")
    print(f"Pools with rewards: {pools_with_rewards}")
    print(f"Pools in result: {len(combined_df)}")

    # Show available USD columns
    usd_columns = [c for c in combined_df.columns if "usd" in c.lower()]
    print(f"\nUSD-priced columns available: {usd_columns}")

    # Show sample of top pools by votes
    if len(combined_df) > 0 and "votes" in combined_df.columns:
        print("\nTop 5 pools by votes:")
        top_pools = combined_df.nlargest(5, "votes")
        for idx, (_, pool) in enumerate(top_pools.iterrows(), 1):
            symbol = pool.get("symbol", "Unknown")
            votes = pool.get("votes", 0)
            tvl_usd = pool.get("tvl_usd", 0)
            incentives_usd = pool.get("incentives_usd", 0)
            gauge_fees_usd = pool.get("gauge_fees_usd", 0)
            print(
                f"  {idx}. {symbol}: {votes:,.0f} votes | "
                f"TVL: ${float(tvl_usd or 0):,.2f} | "
                f"Incentives: ${float(incentives_usd or 0):,.2f} | "
                f"Gauge Fees: ${float(gauge_fees_usd or 0):,.2f}"
            )

    return combined_df


def get_pools_with_rewards(
    chains: list[ChainId],
    export_name: str = "pools_with_rewards",
) -> None:
    """Get combined pool and rewards data for multiple chains."""
    # Enable RPC progress callback
    set_progress_callback(rpc_progress_callback)

    all_dfs: list[pd.DataFrame] = []

    for chain in chains:
        try:
            df = get_pools_with_rewards_for_chain(chain)
            if df is not None and len(df) > 0:
                all_dfs.append(df)
        except Exception as e:
            print(f"\nError fetching data for {chain.name}: {e}", flush=True)
            continue

    # Disable callback after all chains processed
    set_progress_callback(None)

    if not all_dfs:
        print("\nNo data fetched from any chain.")
        return

    # Combine all chain DataFrames
    combined_df = pd.concat(all_dfs, ignore_index=True)

    # Reorder columns to put chain first
    cols = combined_df.columns.tolist()
    if "chain" in cols:
        cols.remove("chain")
        cols = ["chain"] + cols
        combined_df = combined_df[cols]

    # Export combined data
    print(f"\n{'='*70}")
    print("COMBINED EXPORT")
    print(f"{'='*70}")
    print(f"Total chains: {len(all_dfs)}")
    print(f"Total pools: {len(combined_df)}")

    # Export to CSV (use first chain's client for export path)
    export_dir = Path("exports/data")
    export_dir.mkdir(parents=True, exist_ok=True)
    export_path = export_dir / f"{export_name}.csv"
    combined_df.to_csv(export_path, index=True)

    print(f"Combined data exported to: {export_path}")
    print(f"{'='*70}\n")


def main() -> None:
    """Main entry point with CLI argument parsing."""
    parser = argparse.ArgumentParser(
        description="Fetch pools with rewards data from Aerodrome/Velodrome chains."
    )
    parser.add_argument(
        "--aero",
        action="store_true",
        help="Fetch Aerodrome data (Base chain only)",
    )
    parser.add_argument(
        "--velo",
        action="store_true",
        help="Fetch Velodrome data (all chains except Base)",
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Fetch data from all chains (Aero + Velo)",
    )
    args = parser.parse_args()

    # Determine which chains to fetch
    chains: list[ChainId] = []
    export_name = "pools_with_rewards"

    if args.all:
        chains = AERO_CHAINS + VELO_CHAINS
        export_name = "pools_with_rewards_all"
    elif args.aero and args.velo:
        chains = AERO_CHAINS + VELO_CHAINS
        export_name = "pools_with_rewards_all"
    elif args.aero:
        chains = AERO_CHAINS
        export_name = "pools_with_rewards_aero"
    elif args.velo:
        chains = VELO_CHAINS
        export_name = "pools_with_rewards_velo"
    else:
        # Default: Base chain only
        chains = AERO_CHAINS
        export_name = "pools_with_rewards_aero"

    print(f"\nFetching data for {len(chains)} chain(s):")
    for chain in chains:
        print(f"  - {chain.name}")
    print()

    get_pools_with_rewards(chains, export_name)


if __name__ == "__main__":
    main()
# watch out foe XOP pricing
