"""Example: Analyze veToken holders.

This script demonstrates how to analyze veNFT holdings by account,
aggregating multiple veNFTs per account and filtering out specific addresses.
"""

from sugar import SugarClient, ChainId


# Addresses to exclude from analysis (e.g., protocol-owned or service accounts)
AERO_EXCLUDE = (
    "0xBDE0c70BdC242577c52dFAD53389F82fd149EA5a",  # Ouranous
    "0x834C0DA026d5F933C2c18Fa9F8Ba7f1f792fDa52",  # PGF
    "0x51E171d2FDe9b37BBBb624A53Ef54959422388E4",  # FS 1
    "0x5b1892b546002Ff3dd508500575bD6Bf7a101431",  # Echinacea
    "0x623cf63a1fa7068ebbdba9f2eb262613eab557a1",  # FS 2
)
VELO_EXCLUDE = (
    "0x2A8951eFCD40529Dd6eDb3149CCbE4E3cE7d053d",  # Echinacea
)


def process_ve_holders(chain: ChainId | str) -> None:
    """Process veNFT data and export holder analysis."""
    client = SugarClient(chain)

    print(f"Fetching veNFT data for {client.chain_name}...")

    if not client.has_ve():
        print(f"VE Sugar is not available on {client.chain_name}")
        return

    # Get VE positions data
    ve_df = client.get_ve_positions()
    block_num = client.block_number

    print(f"Total veNFTs: {len(ve_df)}")

    # Reset index to access 'id' as a column
    data = ve_df.reset_index()

    # Select relevant columns
    data = data[["id", "account", "governance_amount"]]

    # Filter out excluded addresses based on chain
    if client.chain == ChainId.BASE:
        exclude_list = AERO_EXCLUDE
        token_name = "AERO"
    elif client.chain == ChainId.OPTIMISM:
        exclude_list = VELO_EXCLUDE
        token_name = "VELO"
    else:
        exclude_list = ()
        token_name = "TOKEN"

    # Apply exclusion filter (case-insensitive)
    exclude_lower = [addr.lower() for addr in exclude_list]
    data = data[~data["account"].str.lower().isin(exclude_lower)]

    # Group by account and aggregate
    grouped = (
        data.groupby("account")
        .agg(
            {
                "governance_amount": "sum",
                "id": lambda x: ",".join(map(str, sorted(x))),
            }
        )
        .rename(
            columns={
                "id": "Lock IDs",
                "governance_amount": f"ve{token_name} Amount",
            }
        )
    )

    # Sort by amount descending
    grouped.sort_values(f"ve{token_name} Amount", ascending=False, inplace=True)

    print(f"\nTop 20 ve{token_name} holders:")
    print(grouped.head(20).to_string())
    print(f"\nTotal unique holders: {len(grouped)}")
    print(f"Total ve{token_name}: {grouped[f've{token_name} Amount'].sum():,.2f}")

    # Export to CSV
    export_path = f"ve{token_name}_holders_{block_num}.csv"
    grouped.to_csv(export_path)
    print(f"\nExported to: {export_path}")


if __name__ == "__main__":
    process_ve_holders(ChainId.BASE)
    # process_ve_holders(ChainId.OPTIMISM)
