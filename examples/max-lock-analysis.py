"""Example: Analyze max-locked veNFT percentages.

This script demonstrates how to analyze veNFT data to calculate
the percentage of tokens that are max-locked (permanent locks).
"""

import concurrent.futures
from typing import Tuple

from sugar import SugarClient, ChainId


def calculate_max_locked_percentage(chain: ChainId) -> Tuple[str, float, str]:
    """
    Calculate max locked percentage for specified chain.

    Args:
        chain: Chain identifier

    Returns:
        Tuple containing (chain_name, percentage, token_name)
    """
    token_names = {
        ChainId.BASE: "veAERO",
        ChainId.OPTIMISM: "veVELO",
    }
    token_name = token_names.get(chain, "veToken")

    client = SugarClient(chain)

    if not client.has_ve():
        return client.chain_name, 0.0, token_name

    # Fetch veNFT data
    ve_df = client.get_ve_positions()

    # Analyze max-locked vs expiring
    # expires_at == 0 means permanent lock
    if "expires_at" in ve_df.columns and "amount" in ve_df.columns:
        max_locked = ve_df.loc[ve_df["expires_at"] == 0, "amount"].sum()
        expires = ve_df.loc[ve_df["expires_at"] != 0, "amount"].sum()

        # Calculate percentage
        total = max_locked + expires
        percentage = 100 * max_locked / total if total > 0 else 0
    else:
        percentage = 0.0

    return client.chain_name, percentage, token_name


def main() -> None:
    """Run analysis for multiple chains in parallel and print results."""
    chains = [ChainId.BASE, ChainId.OPTIMISM]

    # Use ThreadPoolExecutor to run calculations concurrently
    with concurrent.futures.ThreadPoolExecutor() as executor:
        # Submit all tasks and collect futures
        futures = [
            executor.submit(calculate_max_locked_percentage, chain) for chain in chains
        ]

        # Process results as they complete
        for future in concurrent.futures.as_completed(futures):
            try:
                chain_name, percentage, token_name = future.result()
                print(f"\n{token_name} ({chain_name}) Max Locked Percentage = {percentage:.2f}%\n")
            except Exception as e:
                print(f"Error processing chain: {e}")


if __name__ == "__main__":
    main()
