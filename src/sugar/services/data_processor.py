"""Data processing service for Sugar Python library."""

from __future__ import annotations

import logging
from decimal import Decimal
from typing import TYPE_CHECKING

import pandas as pd
from web3 import Web3

from sugar.config.columns import (
    COLUMNS_LP,
    COLUMNS_LP_EPOCH,
    COLUMNS_RELAY,
    COLUMNS_TOKEN,
    COLUMNS_VENFT,
)
from sugar.utils.wei import from_wei

if TYPE_CHECKING:
    from sugar.core.web3_provider import Web3Provider
    from sugar.services.price_provider import PriceProvider

logger = logging.getLogger(__name__)

# Minimal ERC20 ABI for symbol lookup
ERC20_SYMBOL_ABI = [
    {
        "constant": True,
        "inputs": [],
        "name": "symbol",
        "outputs": [{"name": "", "type": "string"}],
        "type": "function",
    }
]


class DataProcessor:
    """
    Service for processing raw contract data into DataFrames.

    Handles column mapping, wei conversions, and data transformations.
    """

    def __init__(
        self,
        price_provider: PriceProvider | None = None,
        web3_provider: Web3Provider | None = None,
    ) -> None:
        """
        Initialize data processor.

        Args:
            price_provider: Optional price provider for pricing data.
            web3_provider: Optional web3 provider for on-chain lookups.
        """
        self._prices = price_provider
        self._web3_provider = web3_provider
        self._symbol_cache: dict[str, str] = {}

    def process_lp_all(
        self,
        raw_data: list[tuple],
        tokens_df: pd.DataFrame | None = None,
    ) -> pd.DataFrame:
        """
        Process raw LP data from LpSugar.all().

        Args:
            raw_data: Raw tuple data from contract.
            tokens_df: Optional token metadata DataFrame for symbol lookup.

        Returns:
            Processed DataFrame.
        """
        # Handle variable column count (some chains don't have 'root')
        if raw_data and len(raw_data[0]) == len(COLUMNS_LP) - 1:
            columns = COLUMNS_LP[:-1]  # Exclude 'root'
        else:
            columns = COLUMNS_LP

        df = pd.DataFrame(raw_data, columns=columns)
        df.drop_duplicates(subset=["lp"], inplace=True)

        # Fix empty symbols for CL pools
        if tokens_df is not None:
            empty_symbols = df["symbol"] == ""
            if empty_symbols.any():
                df.loc[empty_symbols, "symbol"] = df.loc[empty_symbols].apply(
                    lambda row: self._get_cl_symbol(row, tokens_df), axis=1
                )

        return df

    def _get_cl_symbol(self, row: pd.Series, tokens_df: pd.DataFrame) -> str:
        """Generate symbol for CL pools."""
        try:
            token0_symbol = self._get_token_symbol(row["token0"], tokens_df)
            token1_symbol = self._get_token_symbol(row["token1"], tokens_df)
            return f"CL{row['type']}-{token0_symbol}/{token1_symbol}"
        except Exception as e:
            logger.warning(f"Error creating CL symbol: {e}")
            return f"CL{row['type']}-Unknown"

    def _get_token_symbol(self, token_address: str, tokens_df: pd.DataFrame) -> str:
        """
        Get token symbol from DataFrame or fetch from chain.

        Args:
            token_address: Token contract address.
            tokens_df: Token metadata DataFrame.

        Returns:
            Token symbol or "UNKNOWN" if not found.
        """
        # Check DataFrame first
        if token_address in tokens_df.index:
            return tokens_df.loc[token_address, "symbol"]

        # Check cache
        if token_address in self._symbol_cache:
            return self._symbol_cache[token_address]

        # Try to fetch from chain
        if self._web3_provider is not None:
            symbol = self._fetch_symbol_from_chain(token_address)
            if symbol:
                self._symbol_cache[token_address] = symbol
                return symbol

        return "UNKNOWN"

    def _fetch_symbol_from_chain(self, token_address: str) -> str | None:
        """
        Fetch token symbol directly from the ERC20 contract.

        Args:
            token_address: Token contract address.

        Returns:
            Token symbol or None if fetch fails.
        """
        try:
            contract = self._web3_provider.web3.eth.contract(
                address=Web3.to_checksum_address(token_address),
                abi=ERC20_SYMBOL_ABI,
            )
            symbol = contract.functions.symbol().call()
            return symbol
        except Exception as e:
            logger.debug(f"Failed to fetch symbol for {token_address}: {e}")
            return None

    def process_tokens(
        self,
        raw_data: list[tuple],
        listed_only: bool = True,
    ) -> pd.DataFrame:
        """
        Process raw token data from LpSugar.tokens().

        Args:
            raw_data: Raw tuple data from contract.
            listed_only: Whether to filter for listed tokens only.

        Returns:
            Processed DataFrame indexed by token_address.
        """
        df = pd.DataFrame(raw_data, columns=COLUMNS_TOKEN)
        df.drop_duplicates(subset=["token_address"], inplace=True)
        df.set_index("token_address", inplace=True)
        df.drop("account_balance", axis=1, inplace=True)

        if listed_only:
            df = df[df["listed"]]

        return df

    def process_ve_all(
        self,
        raw_data: list[tuple],
        convert_amounts: bool = True,
        process_votes: bool = True,
    ) -> pd.DataFrame:
        """
        Process raw veNFT data from VeSugar.all().

        Args:
            raw_data: Raw tuple data from contract.
            convert_amounts: Whether to convert wei amounts to decimals.
            process_votes: Whether to process vote weights.

        Returns:
            Processed DataFrame indexed by id.
        """
        df = pd.DataFrame(raw_data, columns=COLUMNS_VENFT)
        df.drop_duplicates(subset=["id"], inplace=True)
        df.set_index("id", inplace=True)

        if convert_amounts:
            for col in [
                "amount",
                "voting_amount",
                "governance_amount",
                "rebase_amount",
            ]:
                df[col] = df[col].apply(lambda x: float(from_wei(x, 18)))

        if process_votes:
            df["votes"] = df.apply(
                lambda row: self._process_votes(row["votes"], row["governance_amount"]),
                axis=1,
            )

        return df

    def _process_votes(
        self,
        votes: list[tuple],
        governance_amount: float,
    ) -> list[tuple]:
        """Process votes to weight format."""
        if not votes or governance_amount == 0:
            return []

        return [
            (vote[0], min(float(from_wei(vote[1], 18)) / governance_amount, 1.0))
            for vote in votes
        ]

    def process_relay_all(
        self,
        raw_data: list[tuple],
        convert_amounts: bool = True,
        filter_inactive: bool = True,
    ) -> pd.DataFrame:
        """
        Process raw relay data from RelaySugar.all().

        Args:
            raw_data: Raw tuple data from contract.
            convert_amounts: Whether to convert wei amounts to decimals.
            filter_inactive: Whether to filter out inactive relays.

        Returns:
            Processed DataFrame indexed by venft_id.
        """
        df = pd.DataFrame(raw_data, columns=COLUMNS_RELAY)
        df.set_index("venft_id", inplace=True)

        if convert_amounts:
            for col in ["amount", "voting_amount", "used_voting_amount", "compounded"]:
                df[col] = df[col].apply(lambda x: float(from_wei(x, 18)))

            # Process votes with used_voting_amount
            df["votes"] = df.apply(
                lambda row: self._process_relay_votes(
                    row["votes"], row["used_voting_amount"]
                ),
                axis=1,
            )

        if filter_inactive:
            df = df[~df["inactive"]]

        return df

    def _process_relay_votes(
        self,
        votes: list[tuple],
        used_voting_amount: float,
    ) -> list[tuple]:
        """Process relay votes to weight format."""
        if not votes or used_voting_amount == 0:
            return []

        return [
            (vote[0], float(from_wei(vote[1], 18)) / used_voting_amount)
            for vote in votes
        ]

    def process_epochs_latest(
        self,
        raw_data: list[tuple],
        tokens_df: pd.DataFrame | None = None,
    ) -> pd.DataFrame:
        """
        Process raw epoch data from RewardsSugar.epochsLatest().

        Args:
            raw_data: Raw tuple data from contract.
            tokens_df: Optional token metadata for decimal conversion.

        Returns:
            Processed DataFrame.
        """
        df = pd.DataFrame(raw_data, columns=COLUMNS_LP_EPOCH)

        # Convert votes and emissions
        df["votes"] = df["votes"].apply(lambda x: float(from_wei(x, 18)))
        df["emissions"] = df["emissions"].apply(lambda x: float(from_wei(x, 18)))

        # Process bribes and fees with token decimals
        if tokens_df is not None:
            df["bribes"] = df["bribes"].apply(
                lambda x: self._process_rewards_with_decimals(x, tokens_df)
            )
            df["fees"] = df["fees"].apply(
                lambda x: self._process_rewards_with_decimals(x, tokens_df)
            )
        else:
            df["bribes"] = df["bribes"].apply(self._process_rewards_default)
            df["fees"] = df["fees"].apply(self._process_rewards_default)

        return df

    def _process_rewards_with_decimals(
        self,
        rewards: list[tuple],
        tokens_df: pd.DataFrame,
    ) -> list[tuple]:
        """Process reward tuples with proper decimal conversion."""
        if not rewards:
            return []

        result = []
        for token, amount in rewards:
            try:
                decimals = (
                    tokens_df.loc[token, "decimals"] if token in tokens_df.index else 18
                )
                result.append((token, float(from_wei(amount, decimals))))
            except Exception:
                result.append((token, float(from_wei(amount, 18))))
        return result

    def _process_rewards_default(self, rewards: list[tuple]) -> list[tuple]:
        """Process reward tuples with default 18 decimals."""
        if not rewards:
            return []
        return [(token, float(from_wei(amount, 18))) for token, amount in rewards]

    def combine_lp_with_rewards(
        self,
        lp_df: pd.DataFrame,
        epochs_df: pd.DataFrame,
        tokens_df: pd.DataFrame | None = None,
        only_with_rewards: bool = True,
    ) -> pd.DataFrame:
        """
        Combine LP data with latest epoch rewards.

        Args:
            lp_df: LP data from process_lp_all().
            epochs_df: Epoch data from process_epochs_latest().
            tokens_df: Token metadata for pricing.
            only_with_rewards: If True, only include pools that have epoch rewards
                (inner join). If False, include all pools (left join).

        Returns:
            Combined DataFrame with LP info and rewards.
        """
        # Merge on lp address - use inner join to only get pools with rewards
        join_type = "inner" if only_with_rewards else "left"
        combined = lp_df.merge(
            epochs_df[["lp", "votes", "emissions", "bribes", "fees"]],
            on="lp",
            how=join_type,
            suffixes=("", "_epoch"),
        )

        # Add priced columns if price provider is available
        if self._prices and tokens_df is not None:
            combined["bribes_usd"] = combined["bribes"].apply(
                lambda x: (
                    self._price_rewards(x, tokens_df)
                    if isinstance(x, list) and x
                    else Decimal(0)
                )
            )
            combined["fees_usd"] = combined["fees"].apply(
                lambda x: (
                    self._price_rewards(x, tokens_df)
                    if isinstance(x, list) and x
                    else Decimal(0)
                )
            )

            # Add bribe token prices array
            combined["bribe_token_prices"] = combined["bribes"].apply(
                lambda x: (
                    self._get_reward_token_prices(x, tokens_df)
                    if isinstance(x, list) and x
                    else []
                )
            )

            # Convert reserves and fees from wei and price in USD
            combined["reserve0_usd"] = combined.apply(
                lambda row: self._price_token_amount(
                    row["reserve0"], row["token0"], tokens_df
                ),
                axis=1,
            )
            combined["reserve1_usd"] = combined.apply(
                lambda row: self._price_token_amount(
                    row["reserve1"], row["token1"], tokens_df
                ),
                axis=1,
            )
            combined["token0_fees_usd"] = combined.apply(
                lambda row: self._price_token_amount(
                    row["token0_fees"], row["token0"], tokens_df
                ),
                axis=1,
            )
            combined["token1_fees_usd"] = combined.apply(
                lambda row: self._price_token_amount(
                    row["token1_fees"], row["token1"], tokens_df
                ),
                axis=1,
            )
            combined["token0_usd"] = combined.apply(
                lambda row: self._get_token_price(row["token0"], tokens_df),
                axis=1,
            )
            combined["token1_usd"] = combined.apply(
                lambda row: self._get_token_price(row["token1"], tokens_df),
                axis=1,
            )

        return combined

    def _price_rewards(
        self,
        rewards: list[tuple],
        tokens_df: pd.DataFrame,
    ) -> Decimal:
        """Calculate total USD value of rewards."""
        if not rewards or not self._prices:
            return Decimal(0)

        total = Decimal(0)
        for token, amount in rewards:
            price_result = self._prices.get_price_usd(token)
            if price_result:
                total += Decimal(str(amount)) * price_result.price

        return total

    def _get_reward_token_prices(
        self,
        rewards: list[tuple],
        tokens_df: pd.DataFrame,
    ) -> list[dict]:
        """Get array of token prices for rewards."""
        if not rewards or not self._prices:
            return []

        prices = []
        for token, amount in rewards:
            price_result = self._prices.get_price_usd(token)
            if price_result:
                prices.append(
                    {
                        "token": token,
                        "amount": float(amount),
                        "price_usd": float(price_result.price),
                        "value_usd": float(Decimal(str(amount)) * price_result.price),
                    }
                )
            else:
                prices.append(
                    {
                        "token": token,
                        "amount": float(amount),
                        "price_usd": None,
                        "value_usd": None,
                    }
                )

        return prices

    def _get_token_decimals(
        self,
        token_address: str,
        tokens_df: pd.DataFrame,
    ) -> int:
        """Get token decimals from DataFrame or default to 18."""
        try:
            if token_address in tokens_df.index:
                return int(tokens_df.loc[token_address, "decimals"])
        except Exception:
            pass
        return 18

    def _price_token_amount(
        self,
        amount_wei: int,
        token_address: str,
        tokens_df: pd.DataFrame,
    ) -> Decimal:
        """Convert wei amount to USD value."""
        if not self._prices or amount_wei == 0:
            return Decimal(0)

        decimals = self._get_token_decimals(token_address, tokens_df)
        amount = from_wei(amount_wei, decimals)

        price_result = self._prices.get_price_usd(token_address)
        if price_result:
            return Decimal(str(amount)) * price_result.price

        return Decimal(0)

    def _get_token_price(
        self,
        token_address: str,
        tokens_df: pd.DataFrame,
    ) -> Decimal | None:
        """Get token price in USD."""
        if not self._prices:
            return None

        price_result = self._prices.get_price_usd(token_address)
        if price_result:
            return price_result.price

        return None
