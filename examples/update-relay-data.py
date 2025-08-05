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
    base_data, base_block_num = update_relay_data("base", filter_inactive=False)
    op_data, op_block_num = update_relay_data("op", filter_inactive=False)

#     base_optimizer = "0x757C89D4C05A002A1C82E7D62F205B568DAF6124"
#     op_optimizer = "0x8D5E9423E8C80DE2CA42E922DA023D11F66C70ED"

#     text_0 = "Hey good morning team, we've identified that a Relay permissionless call is open to griefing attacks, which started taking place earlier today. This is now fully mitigated and requires your help to address the Relay you're managing. The nature of the attack is specific to some Relay voting rewards being compounded into low liquidity pools."
#     # text_1 = f"The fix we've implemented requires you to call `setOptimizer({base_optimizer})` using your manager address: {manager}"
#     # text_2 = f"Here's the contract address for your relay that'll have the `setOptimizer()` function, relay address: {relay}"
#     text_3 = "Please let us know if you have any questions."

#     # for i in range(len(base_data)):
#     #     print(f"\n\n{base_data.iloc[i]['name']}\n")
#     #     print(text_0)
#     #     text_1 = f"\nThe fix we've implemented on Base requires you to call `setOptimizer({base_optimizer})` using your manager address: {base_data.iloc[i]['manager']}"
#     #     text_2 = f"\nHere's the contract address for your relay that'll have the `setOptimizer()` function, relay address: {base_data.iloc[i]['relay']}\n"
#     #     print(text_1)
#     #     print(text_2)
#     #     print(text_3)

#     # data = pd.DataFrame(
#     #     {
#     #         "name": base_data.iloc[i]["name"],
#     #         "manager": base_data.iloc[i]["manager"],
#     #         "relay": base_data.iloc[i]["relay"],
#     #         "partner_message": text_0 + text_1 + text_2 + text_3,
#     #     }
#     # )
#     # data.to_csv("base_data.csv")

#     for i in range(len(op_data)):
#         print(f"\n\n{op_data.iloc[i]['name']}\n")
#         print(text_0)
#         text_1 = f"\nThe fix we've implemented on OPM requires you to call `setOptimizer({op_optimizer})` using your manager address: `{op_data.iloc[i]['manager']}`"
#         text_2 = f"\nHere's the contract address for your relay that'll have the `setOptimizer()` function, relay address: `{op_data.iloc[i]['relay']}`\n"
#         print(text_1)
#         print(text_2)
#         print(text_3)

#     # data = pd.DataFrame(
#     #     {
#     #         "name": op_data.iloc[i]["name"],
#     #         "manager": op_data.iloc[i]["manager"],
#     #         "relay": op_data.iloc[i]["relay"],
#     #         "partner_message": text_0 + text_1 + text_2 + text_3,
#     #     }
#     # )
#     # data.to_csv("op_data.csv")

# # There's also this other relay that'll require a similar tx on OPM:
