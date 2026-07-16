"""Export tokens and pools for a chain to CSV.

Demonstrates the fetch + export_dataframe pattern. Output is written under
./output so nothing lands outside this directory.
"""

from sugar import ChainId, SugarClient, setup_logging

setup_logging()


def export_pools(chain: ChainId | str) -> None:
    client = SugarClient(chain, export_dir="output")

    tokens = client.get_tokens(listed_only=False)
    tokens_path = client.export_dataframe(tokens, "tokens", include_block=False)
    print(f"{len(tokens)} tokens -> {tokens_path}")

    pools = client.get_pools()
    pools_path = client.export_dataframe(pools, "pools")
    print(f"{len(pools)} pools -> {pools_path}")


if __name__ == "__main__":
    export_pools(ChainId.BASE)
