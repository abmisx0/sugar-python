import sys
import os
from typing import List, Dict
from concurrent.futures import ThreadPoolExecutor, as_completed
import pandas as pd

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from sugar import Sugar

COLUMNS_GAUGE_KILL_EXPORT = ["symbol", "gauge"]


def process_chain(chain: str, to_unlist: List[str]):
    """Process chain for gauge kill list."""
    sugar = Sugar(chain)
    tokens = sugar.lp_tokens(listed=False)
    lps = sugar.lp_all()
    unlisted = tokens[~tokens["listed"]].index.str.lower().to_list()

    gauges_alive = lps[lps["gauge_alive"]]

    kill_types = [("to_kill", to_unlist), ("kill", unlisted)]
    filtered_gauges = (
        (
            kill_type,
            gauges_alive[
                (gauges_alive["token0"].str.lower().isin(token_list))
                | (gauges_alive["token1"].str.lower().isin(token_list))
            ],
        )
        for kill_type, token_list in kill_types
    )

    [
        sugar._export_csv(gauges[COLUMNS_GAUGE_KILL_EXPORT], f"gauges_{kill_type}_list_{chain}.csv")
        for kill_type, gauges in filtered_gauges
    ]


def main():
    # Read CSV files to build kill lists
    chains_data: Dict[str, List[str]] = {"base": [], "op": []}
    cwd = os.path.dirname(os.path.abspath(__file__))
    for chain in chains_data:
        try:
            df = pd.read_csv(f"{cwd}/{chain}.csv")
            chains_data[chain] = df["address"].str.lower().tolist()
        except FileNotFoundError:
            print(f"Warning: {chain}.csv not found, using hardcoded list")

    with ThreadPoolExecutor() as executor:
        futures = [
            executor.submit(process_chain, chain, to_list_tokens)
            for chain, to_list_tokens in chains_data.items()
        ]

        for future in as_completed(futures):
            future.result()


if __name__ == "__main__":
    main()
