import sys
import os
from typing import Literal

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from sugar import Sugar


def update_lp_data(chain: Literal["base", "op"]):
    """Update lp data for specified chain."""
    sugar = Sugar(chain)
    sugar.lp_tokens(listed=False)
    sugar.lp_all()


if __name__ == "__main__":
    # for chain in ("base", "op"):
    #     update_lp_data(chain)
    update_lp_data("base")
