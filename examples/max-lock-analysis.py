import sys
import os
import concurrent.futures
from typing import Tuple

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from sugar import Sugar
import config


def calculate_max_locked_percentage(chain: str) -> Tuple[str, float, str]:
    """
    Calculate max locked percentage for specified chain.

    Args:
        chain: Chain identifier string

    Returns:
        Tuple containing (chain, percentage, token_name)
    """
    token_name = {"base": "veAERO", "op": "veVELO"}.get(chain, chain)

    # Initialize Sugar once
    sugar = Sugar(chain)
    sugar.relay_all(config.COLUMNS_RELAY_EXPORT, config.COLUMNS_RELAY_EXPORT_RENAME)

    # Fetch data
    data, _ = sugar.ve_all(
        columns_export=config.COLUMNS_VENFT_EXPORT,
        columns_rename=config.COLUMNS_VENFT_EXPORT_RENAME,
    )

    # Use boolean indexing directly for filtering
    max_locked = data.loc[data["expires_at"] == 0, "governance_amount"].sum()
    expires = data.loc[data["expires_at"] != 0, "governance_amount"].sum()

    # Calculate percentage
    percentage = (
        100 * max_locked / (max_locked + expires) if (max_locked + expires) > 0 else 0
    )

    return chain, percentage, token_name


def main():
    """Run analysis for multiple chains in parallel and print results."""
    chains = ["base", "op"]

    # Use ThreadPoolExecutor to run calculations concurrently
    with concurrent.futures.ThreadPoolExecutor() as executor:
        # Submit all tasks and collect futures
        futures = [
            executor.submit(calculate_max_locked_percentage, chain) for chain in chains
        ]

        # Process results as they complete
        for future in concurrent.futures.as_completed(futures):
            try:
                chain, percentage, token_name = future.result()
                print(f"\n{token_name} Max Locked Percentage = {percentage:.2f}%\n")
            except Exception as e:
                print(f"Error processing chain: {e}")


if __name__ == "__main__":
    main()
