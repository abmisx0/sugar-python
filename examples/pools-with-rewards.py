#!/usr/bin/env python3
"""
Example: Get pools with rewards data.

This demonstrates the combined LP + rewards data functionality
that fetches pool data along with latest epoch rewards and prices
the fees and incentives in USD.
"""

from sugar import SugarClient, ChainId, set_progress_callback


def rpc_progress_callback(
    chain: str, sugar_type: str, method: str, offset: int | None
) -> None:
    """Print RPC call progress."""
    if offset is not None:
        print(f"  RPC: {chain} | {sugar_type} | {method}(offset={offset})", flush=True)
    else:
        print(f"  RPC: {chain} | {sugar_type} | {method}()", flush=True)


def get_pools_with_rewards(chain: ChainId | str, only_with_rewards: bool = True) -> None:
    """Get combined pool and rewards data."""
    # Enable RPC progress callback
    set_progress_callback(rpc_progress_callback)

    client = SugarClient(chain)

    if not client.has_rewards():
        print(f"Rewards Sugar not available on {client.chain_name}")
        return

    print(f"\n{'='*70}", flush=True)
    print(f"Fetching combined LP + rewards data for {client.chain_name}", flush=True)
    print(f"{'='*70}", flush=True)
    print(
        "This includes pool info, latest epoch rewards, and USD-priced fees/incentives",
        flush=True,
    )
    if only_with_rewards:
        print("Note: Only pools with epoch rewards will be included", flush=True)
    else:
        print("Note: All pools will be included (some may not have rewards)", flush=True)

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

    combined_df = client.processor.combine_lp_with_rewards(
        lp_df, epochs_df, tokens_df, only_with_rewards=only_with_rewards
    )

    print(f"       Processed {len(combined_df)} pools with USD pricing")

    # Summary
    print(f"\n{'='*70}")
    print("SUMMARY")
    print(f"{'='*70}")
    print(f"Total pools: {total_pools}")
    print(f"Pools with rewards: {pools_with_rewards}")
    print(f"Pools in result: {len(combined_df)}")
    if only_with_rewards:
        print("  (Only pools with rewards are included)")
    else:
        missing = total_pools - pools_with_rewards
        print(f"  ({missing} pools without rewards included)")

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

    # Export to CSV
    print(f"\n{'='*70}")
    path = client.export_dataframe(combined_df, "pools_with_rewards")
    print(f"Combined data exported to: {path}")
    print(f"{'='*70}\n")

    # Disable callback after use
    set_progress_callback(None)


if __name__ == "__main__":
    # By default, only pools with rewards are included
    # Set only_with_rewards=False to include all pools
    get_pools_with_rewards(ChainId.BASE)
