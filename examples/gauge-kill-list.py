import sys
import os
from typing import List, Dict
from concurrent.futures import ThreadPoolExecutor, as_completed

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from sugar import Sugar

COLUMNS_GAUGE_KILL_EXPORT = ["symbol", "gauge"]


def process_chain(chain: str, to_unlist: List[str]):
    sugar = Sugar(chain)
    lps = sugar.lp_all()
    tokens = sugar.lp_tokens(listed=False)
    unlisted = tokens[~tokens["listed"]].index.to_list()

    gauges_alive = lps[lps["gauge_alive"]]

    kill_types = [("to_kill", to_unlist), ("kill", unlisted)]
    filtered_gauges = (
        (
            kill_type,
            gauges_alive[gauges_alive["token0"].isin(token_list) | gauges_alive["token1"].isin(token_list)],
        )
        for kill_type, token_list in kill_types
    )

    [
        sugar._export_csv(gauges[COLUMNS_GAUGE_KILL_EXPORT], f"gauges_{kill_type}_list_{chain}.csv")
        for kill_type, gauges in filtered_gauges
    ]


def main():
    chains_data: Dict[str, List[str]] = {
        "base": [
            "0xEFb97aaF77993922aC4be4Da8Fbc9A2425322677",
            "0xe2c86869216aC578bd62a4b8313770d9EE359A05",
            "0x994ac01750047B9d35431a7Ae4Ed312ee955E030",
            "0xEcE7B98bD817ee5B1F2f536dAf34D0B6af8Bb542",
            "0x489fe42C267fe0366B16b0c39e7AEEf977E841eF",
            "0x7ED613AB8b2b4c6A781DDC97eA98a666c6437511",
            "0x00e1724885473B63bCE08a9f0a52F35b0979e35A",
            "0xc43F3Ae305a92043bd9b62eBd2FE14F7547ee485",
            "0xBa5E6fa2f33f3955f0cef50c63dCC84861eAb663",
            "0x04D1963C76EB1BEc59d0eEb249Ed86F736B82993",
            "0x348Fdfe2c35934A96C1353185F09D0F9efBAdA86",
        ],
        "op": [
            "0x47536F17F4fF30e64A96a7555826b8f9e66ec468",
            "0x39FdE572a18448F8139b7788099F0a0740f51205",
            "0xB153FB3d196A8eB25522705560ac152eeEc57901",
            "0x8901cB2e82CC95c01e42206F8d1F417FE53e7Af0",
            "0x7aE97042a4A0eB4D1eB370C34BfEC71042a056B7",
            "0x46f21fDa29F1339e0aB543763FF683D399e393eC",
            "0xb396b31599333739A97951b74652c117BE86eE1D",
            "0x28b42698Caf46B4B012CF38b6C75867E0762186D",
            "0x2513486f18eeE1498D7b6281f668B955181Dd0D9",
            "0xfDeFFc7Ad816BF7867C642dF7eBC2CC5554ec265",
        ],
    }

    with ThreadPoolExecutor() as executor:
        futures = [
            executor.submit(process_chain, chain, unlisted_tokens)
            for chain, unlisted_tokens in chains_data.items()
        ]

        for future in as_completed(futures):
            future.result()


if __name__ == "__main__":
    main()
