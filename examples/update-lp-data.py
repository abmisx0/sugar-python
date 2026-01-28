"""Example: Update LP pool data for a chain.

This script demonstrates how to fetch and export LP pool data
using the SugarClient API.
"""

from sugar import SugarClient, ChainId


def update_lp_data(chain: ChainId | str) -> None:
    """Update LP data for specified chain."""
    client = SugarClient(chain)

    print(f"Fetching LP data for {client.chain_name}...")

    # Get and export tokens
    tokens_df = client.get_tokens(listed_only=False)
    token_path = client.export_dataframe(tokens_df, "tokens", include_block=False)
    print(f"Tokens exported to: {token_path}")

    # Get and export pools
    pools_df = client.get_pools()
    pool_path = client.export_dataframe(pools_df, "pools")
    print(f"Pools exported to: {pool_path}")


if __name__ == "__main__":
    update_lp_data(ChainId.BASE)
    # update_lp_data(ChainId.OPTIMISM)
