from sugar import Sugar
import config

if __name__ == "__main__":
    ##################### BASE #####################
    sugar = Sugar("base")
    sugar.relay_all(config.COLUMNS_RELAY_EXPORT, config.COLUMNS_RELAY_EXPORT_RENAME)

    data, block = sugar.ve_all(
        columns_export=config.COLUMNS_VENFT_EXPORT,
        columns_rename=config.COLUMNS_VENFT_EXPORT_RENAME,
    )
    veaero_max = data.loc[data["expires_at"] == 0, "governance_amount"].sum()
    veaero_expires = data.loc[data["expires_at"] != 0, "governance_amount"].sum()

    print(f"\nveAERO Max Locked Percentage = {100*veaero_max/(veaero_max+veaero_expires)}%\n")

    ##################### OP #####################
    sugar = Sugar("op")
    sugar.relay_all(config.COLUMNS_RELAY_EXPORT, config.COLUMNS_RELAY_EXPORT_RENAME)

    data, block = sugar.ve_all(
        columns_export=config.COLUMNS_VENFT_EXPORT,
        columns_rename=config.COLUMNS_VENFT_EXPORT_RENAME,
    )

    vevelo_max = data.loc[data["expires_at"] == 0, "governance_amount"].sum()
    vevelo_expires = data.loc[data["expires_at"] != 0, "governance_amount"].sum()

    print(f"\nveVELO Max Locked Percentage = {100*vevelo_max/(vevelo_max+vevelo_expires)}%\n")
