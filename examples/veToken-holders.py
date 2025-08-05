import sys
import os
from typing import Literal

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from sugar import Sugar
import config

AERO_LIST_TO_REMOVE = (
    "0xBDE0c70BdC242577c52dFAD53389F82fd149EA5a",  # Ouranous
    "0x834C0DA026d5F933C2c18Fa9F8Ba7f1f792fDa52",  # PGF
    "0x51E171d2FDe9b37BBBb624A53Ef54959422388E4",  # FS 1
    "0x5b1892b546002Ff3dd508500575bD6Bf7a101431",  # Echinacea
    "0x623cf63a1fa7068ebbdba9f2eb262613eab557a1",  # FS 2
)
VELO_LIST_TO_REMOVE = ("0x2A8951eFCD40529Dd6eDb3149CCbE4E3cE7d053d",)  # Echinacea


def process_ve_data(chain: Literal["base", "op"]):
    """Process ve data for specified chain and export holders to CSV."""
    sugar = Sugar(chain)
    sugar.relay_all(config.COLUMNS_RELAY_EXPORT, config.COLUMNS_RELAY_EXPORT_RENAME)
    data, block_num = sugar.ve_all(
        columns_export=("id", "account", "governance_amount"),
        index_id=False,
    )

    if chain == "op":
        data = data[~data["account"].isin(VELO_LIST_TO_REMOVE)]
    elif chain == "base":
        data = data[~data["account"].isin(AERO_LIST_TO_REMOVE)]
    grouped = (
        data.groupby("account")
        .agg({"governance_amount": "sum", "id": lambda x: ",".join(map(str, x))})
        .rename(columns={"id": "Lock IDs"})
    )
    grouped.sort_values("governance_amount", ascending=False, inplace=True)
    grouped.rename(
        columns={"account": "Account", "governance_amount": "veAERO Amount"},
        inplace=True,
    )

    token_name = "AERO" if chain == "base" else "VELO"
    sugar._export_csv(grouped, f"ve{token_name}_holders_{block_num}.csv")


if __name__ == "__main__":
    process_ve_data("base")
    # process_ve_data("op")
