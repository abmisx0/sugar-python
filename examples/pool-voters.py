import sys
import os
from typing import Union, Tuple

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from sugar import Sugar
import config


def get_voters(
    chain: str,
    pools: Union[str, Tuple[str]],
    master_export: bool = True,
    override: bool = True,
):
    """Get voters for specified pools."""
    sugar = Sugar(chain)
    sugar.relay_all(config.COLUMNS_RELAY_EXPORT, config.COLUMNS_RELAY_EXPORT_RENAME, override=override)

    _, block_num = sugar.ve_all(
        columns_export=config.COLUMNS_VENFT_EXPORT,
        columns_rename=config.COLUMNS_VENFT_EXPORT_RENAME,
        override=override,
    )

    sugar.voters(pools, block_num, master_export)


if __name__ == "__main__":
    pools_base = (
        "0x70aCDF2Ad0bf2402C957154f944c19Ef4e1cbAE1",
        "0x4e962BB3889Bf030368F56810A9c96B83CB3E778",
    )
    get_voters("base", pools_base, override=False)
