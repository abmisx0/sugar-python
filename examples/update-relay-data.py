import sys
import os
from typing import Literal

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from sugar import Sugar
import config


def update_relay_data(chain: Literal["base", "op"]):
    sugar = Sugar(chain)
    sugar.relay_all(config.COLUMNS_RELAY_EXPORT, config.COLUMNS_RELAY_EXPORT_RENAME)


if __name__ == "__main__":
    for chain in ("base", "op"):
        update_relay_data(chain)
