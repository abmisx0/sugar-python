"""Example: Get pools with rewards and priced fees/bribes.

This script demonstrates the combined LP + Rewards functionality
that fetches pool data along with latest epoch rewards and prices
the fees and bribes in USD.
"""

from sugar import SugarClient, ChainId


def get_pools_with_rewards(chain: ChainId | str) -> None:
    """Get combined pool and rewards data."""
    client = SugarClient(chain)

    if not client.has_rewards():
        print(f"Rewards Sugar not available on {client.chain_name}")
        return

    print(f"Fetching combined LP + rewards data for {client.chain_name}...")
    print("This includes pool info, latest epoch rewards, and USD-priced fees/bribes")

    # Get combined data
    combined_df = client.get_pools_with_rewards()
    print(f"Found {len(combined_df)} pools")

    # Show sample of top pools by votes
    if len(combined_df) > 0:
        print("\nTop 5 pools by votes:")
        top_pools = combined_df.nlargest(5, "votes")
        for _, pool in top_pools.iterrows():
            symbol = pool.get("symbol", "Unknown")
            votes = pool.get("votes", 0)
            print(f"  {symbol}: {votes:,.0f} votes")

    # Export to CSV
    path = client.export_pools_with_rewards()
    print(f"\nCombined data exported to: {path}")


if __name__ == "__main__":
    get_pools_with_rewards(ChainId.BASE)
