import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from sugar import Sugar
import config


def calculate_max_locked_percentage(chain: str):
    sugar = Sugar(chain)
    sugar.relay_all(config.COLUMNS_RELAY_EXPORT, config.COLUMNS_RELAY_EXPORT_RENAME)

    data, _ = sugar.ve_all(
        columns_export=config.COLUMNS_VENFT_EXPORT,
        columns_rename=config.COLUMNS_VENFT_EXPORT_RENAME,
    )

    max_locked = data.loc[data["expires_at"] == 0, "governance_amount"].sum()
    expires = data.loc[data["expires_at"] != 0, "governance_amount"].sum()

    percentage = 100 * max_locked / (max_locked + expires)

    return percentage


if __name__ == "__main__":
    base_percentage = calculate_max_locked_percentage("base")
    op_percentage = calculate_max_locked_percentage("op")
    print(f"\nveAERO Max Locked Percentage = {base_percentage:.2f}%\n")
    print(f"\nveVELO Max Locked Percentage = {op_percentage:.2f}%\n")
