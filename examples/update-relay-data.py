import sys
import os
from typing import Literal

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from sugar import Sugar
import config
import pandas as pd


def update_relay_data(
    chain: Literal["base", "op"], filter_inactive: bool = True, override: bool = True
):
    """Update relay data for specified chain."""
    sugar = Sugar(chain)
    return sugar.relay_all(
        columns_export=config.COLUMNS_RELAY_EXPORT,
        columns_rename=config.COLUMNS_RELAY_EXPORT_RENAME,
        override=override,
        filter_inactive=filter_inactive,
    )


if __name__ == "__main__":
    base_data, base_block_num = update_relay_data("base")  # , filter_inactive=False)
    op_data, op_block_num = update_relay_data("op")  # , filter_inactive=False)
