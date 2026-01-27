"""Example: Update LP pool data for a chain.

This script demonstrates how to fetch and export LP pool data
using the new SugarClient API.
"""

from sugar import SugarClient, ChainId


def update_lp_data(chain: ChainId | str) -> None:
    """Update LP data for specified chain."""
    client = SugarClient(chain)

    print(f"Fetching LP data for {client.chain_name}...")

    # Export tokens
    token_path = client.export_tokens()
    print(f"Tokens exported to: {token_path}")

    # Export pools
    pool_path = client.export_pools()
    print(f"Pools exported to: {pool_path}")


if __name__ == "__main__":
    update_lp_data(ChainId.BASE)
    # update_lp_data(ChainId.OPTIMISM)
