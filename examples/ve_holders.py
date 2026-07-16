"""Aggregate veNFT positions by holder for a chain.

Sums governance weight per account across all veNFTs and prints the largest
holders. Shows how to work with the DataFrame returned by get_ve_positions().
"""

from sugar import ChainId, SugarClient, setup_logging

setup_logging()


def ve_holders(chain: ChainId | str, top: int = 20) -> None:
    client = SugarClient(chain)

    if not client.has_ve():
        print(f"VeSugar is not available on {client.chain_name}")
        return

    ve_df = client.get_ve_positions().reset_index()
    grouped = ve_df.groupby("account")["governance_amount"].sum().sort_values(ascending=False)

    print(f"{len(grouped)} unique holders on {client.chain_name}")
    print(grouped.head(top).to_string())


if __name__ == "__main__":
    ve_holders(ChainId.BASE)
