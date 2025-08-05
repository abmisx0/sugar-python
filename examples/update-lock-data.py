import sys
import os
from typing import Literal

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from sugar import Sugar
import config


def update_lock_data(chain: Literal["base", "op"]):
    """Update lock data for specified chain."""
    sugar = Sugar(chain)
    sugar.ve_all(
        columns_export=config.COLUMNS_VENFT_EXPORT,
        columns_rename=config.COLUMNS_VENFT_EXPORT_RENAME,
    )


if __name__ == "__main__":
    update_lock_data("base")
    # update_lock_data("op")
