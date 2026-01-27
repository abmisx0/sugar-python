"""Example: Update relay data for a chain.

This script demonstrates how to fetch and export relay data
using the new SugarClient API.
"""

from sugar import SugarClient, ChainId


def update_relay_data(chain: ChainId | str, filter_inactive: bool = True) -> None:
    """Update relay data for specified chain."""
    client = SugarClient(chain)

    if not client.has_relay():
        print(f"Relay Sugar not available on {client.chain_name}")
        return

    print(f"Fetching relay data for {client.chain_name}...")

    # Get relay data as DataFrame
    relay_df = client.get_relays(filter_inactive=filter_inactive)
    print(f"Found {len(relay_df)} relays")

    # Export to CSV
    path = client.export_relays()
    print(f"Relays exported to: {path}")


if __name__ == "__main__":
    update_relay_data(ChainId.BASE)
    update_relay_data(ChainId.OPTIMISM)
