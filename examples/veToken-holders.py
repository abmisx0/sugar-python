import sys
import os
from typing import Literal

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from sugar import Sugar
import config


def process_ve_data(chain: Literal["base", "op"]):
    sugar = Sugar(chain)
    sugar.relay_all(config.COLUMNS_RELAY_EXPORT, config.COLUMNS_RELAY_EXPORT_RENAME)
    data, block_num = sugar.ve_all(
        columns_export=("id", "account", "governance_amount"), index_id=False, override=False
    )

    grouped = (
        data.groupby("account")
        .agg({"governance_amount": "sum", "id": lambda x: ",".join(map(str, x))})
        .rename(columns={"id": "locks"})
    )
    grouped.sort_values("governance_amount", ascending=False, inplace=True)

    token_name = "AERO" if chain == "base" else "VELO"
    sugar._export_csv(grouped, f"ve{token_name}_holders_{block_num}.csv")


if __name__ == "__main__":
    for chain in ("base", "op"):
        process_ve_data(chain)
