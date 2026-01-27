"""Example: Update veNFT lock data for a chain.

This script demonstrates how to fetch and export veNFT (vote-escrow NFT)
data using the new SugarClient API.
"""

from sugar import SugarClient, ChainId


def update_lock_data(chain: ChainId | str) -> None:
    """Update lock data for specified chain."""
    client = SugarClient(chain)

    if not client.has_ve():
        print(f"VE Sugar not available on {client.chain_name}")
        return

    print(f"Fetching veNFT data for {client.chain_name}...")
    print("Note: This may take a while for chains with many veNFTs")

    # Get veNFT data as DataFrame
    ve_df = client.get_ve_positions()
    print(f"Found {len(ve_df)} veNFTs")

    # Export to CSV
    path = client.export_ve_positions()
    print(f"veNFTs exported to: {path}")


if __name__ == "__main__":
    update_lock_data(ChainId.BASE)
    # update_lock_data(ChainId.OPTIMISM)
