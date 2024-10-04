import pandas as pd
from sugar import Sugar
import config

if __name__ == "__main__":
    ##################### BASE #####################
    sugar = Sugar("base")
    sugar.relay_all(config.COLUMNS_RELAY_EXPORT, config.COLUMNS_RELAY_EXPORT_RENAME)
    data, block_num = sugar.ve_all(
        columns_export=config.COLUMNS_VENFT_EXPORT,
        columns_rename=config.COLUMNS_VENFT_EXPORT_RENAME,
    )

    data["locks"] = data.index
    total_votes = data.groupby("account")["governance_amount"].sum()
    venfts = (
        data.groupby("account")["locks"].apply(list).apply(lambda x: str(x).strip("[]"))
    )
    data = pd.concat([total_votes, venfts], axis=1).sort_values(
        "governance_amount", ascending=False
    )
    sugar._export_csv(data, f"veAERO_holders_{block_num}.csv")

    ##################### OP #####################
    sugar = Sugar("op")
    sugar.relay_all(config.COLUMNS_RELAY_EXPORT, config.COLUMNS_RELAY_EXPORT_RENAME)
    data, block_num = sugar.ve_all(
        columns_export=config.COLUMNS_VENFT_EXPORT,
        columns_rename=config.COLUMNS_VENFT_EXPORT_RENAME,
    )

    data["locks"] = data.index
    total_votes = data.groupby("account")["governance_amount"].sum()
    venfts = (
        data.groupby("account")["locks"].apply(list).apply(lambda x: str(x).strip("[]"))
    )
    data = pd.concat([total_votes, venfts], axis=1).sort_values(
        "governance_amount", ascending=False
    )
    sugar._export_csv(data, f"veVELO_holders_{block_num}.csv")
