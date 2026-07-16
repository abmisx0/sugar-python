"""List active Relays (autocompounders/managed veNFTs) for a chain.

Relay data resolves managed-veNFT principal that a naive ve reader misses.
"""

from sugar import ChainId, SugarClient, setup_logging

setup_logging()


def list_relays(chain: ChainId | str) -> None:
    client = SugarClient(chain)

    if not client.has_relay():
        print(f"RelaySugar is not available on {client.chain_name}")
        return

    relays = client.get_relays(filter_inactive=True)
    print(f"{len(relays)} active relays on {client.chain_name}")
    print(relays.head())


if __name__ == "__main__":
    list_relays(ChainId.OPTIMISM)
