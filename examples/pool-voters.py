import sys
import os
from typing import Union, Tuple, Literal


sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from sugar import Sugar
import config


def get_voters(
    chain: Literal["base", "op"],
    pools: Union[str, Tuple[str]],
    master_export: bool = True,
    override: bool = True,
):
    env_var = f"VE_ALL_LIMIT_{chain.upper()}"
    """Get voters for specified pools."""
    sugar = Sugar(chain)
    sugar.lp_all(override=override)
    sugar.relay_all(
        config.COLUMNS_RELAY_EXPORT,
        config.COLUMNS_RELAY_EXPORT_RENAME,
        override=override,
    )
    _, block_num = sugar.ve_all(
        columns_export=config.COLUMNS_VENFT_EXPORT,
        columns_rename=config.COLUMNS_VENFT_EXPORT_RENAME,
        override=override,
    )

    sugar.voters(pools, block_num, master_export=master_export)


if __name__ == "__main__":
    pools_base = (
        "0xC75799e0646470128a42D07335aB3BFa9E8Ee7C2",
        "0xe7e01f38470136dE763d22e534e53C8BCdbA3f39",
    )
    get_voters(
        "base",
        "0x1524a14C55f097bb54F0b24383f3ae3e3743804A",
        master_export=False,
        override=False,
    )
