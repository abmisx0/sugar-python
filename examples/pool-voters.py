"""Example: Get voters for specific pools.

This script demonstrates how to analyze voting patterns for specific pools
using the new SugarClient API.
"""

from sugar import SugarClient, ChainId


def get_voters_for_pool(chain: ChainId | str, pool_address: str) -> None:
    """Get and display voters for a specific pool."""
    client = SugarClient(chain)

    print(f"Fetching voting data for {client.chain_name}...")

    if not client.has_ve():
        print(f"VE Sugar is not available on {client.chain_name}")
        return

    # Get VE positions data
    ve_df = client.get_ve_positions()
    print(f"Total veNFT positions: {len(ve_df)}")

    # Get relay data if available
    relay_df = None
    if client.has_relay():
        relay_df = client.get_relays(filter_inactive=True)
        print(f"Active relays: {len(relay_df)}")

    # Filter votes for the specified pool
    pool_voters = []
    for idx, row in ve_df.iterrows():
        votes = row["votes"]
        if not votes:
            continue

        for lp, weight in votes:
            if lp.lower() == pool_address.lower():
                pool_voters.append(
                    {
                        "venft_id": idx,
                        "account": row["account"],
                        "governance_amount": row["governance_amount"],
                        "vote_weight": weight,
                        "vote_amount": row["governance_amount"] * weight,
                    }
                )

    if pool_voters:
        import pandas as pd

        voters_df = pd.DataFrame(pool_voters)
        voters_df.sort_values("vote_amount", ascending=False, inplace=True)
        print(f"\nFound {len(voters_df)} voters for pool {pool_address}:")
        print(voters_df.head(20).to_string())

        # Export to CSV
        export_path = f"pool_voters_{client.chain_name.lower()}_{client.block_number}.csv"
        voters_df.to_csv(export_path, index=False)
        print(f"\nExported to: {export_path}")
    else:
        print(f"No votes found for pool {pool_address}")


if __name__ == "__main__":
    # Example pool address on Base
    get_voters_for_pool(
        ChainId.BASE,
        "0x1524a14C55f097bb54F0b24383f3ae3e3743804A",
    )
