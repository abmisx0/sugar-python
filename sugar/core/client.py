"""Main SugarClient facade for Sugar Python library."""

from __future__ import annotations

import logging
from decimal import Decimal
from pathlib import Path
from typing import TYPE_CHECKING

import pandas as pd

from sugar.config.chains import ChainConfig, ChainId, get_chain_config
from sugar.contracts.lp_sugar import LpSugar
from sugar.contracts.price_oracle import SpotPriceOracle
from sugar.contracts.relay_sugar import RelaySugar
from sugar.contracts.rewards_sugar import RewardsSugar
from sugar.contracts.ve_sugar import VeSugar
from sugar.core.exceptions import ContractNotAvailableError
from sugar.core.web3_provider import Web3Provider
from sugar.models import AccountPosition, PositionKind, TokenAmount, VeNFT
from sugar.services.data_processor import DataProcessor
from sugar.services.export import ExportService
from sugar.services.price_provider import (
    CoinGeckoPriceSource,
    DefiLlamaPriceSource,
    OraclePriceSource,
    PriceProvider,
)
from sugar.services.snapshot import SnapshotStore

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)


class SugarClient:
    """
    Main facade for interacting with Sugar Protocol contracts.

    Provides a unified interface to all Sugar contracts with automatic
    chain configuration, price fetching, and data processing.

    Example:
        >>> from sugar import SugarClient, ChainId
        >>> client = SugarClient(ChainId.BASE)
        >>> pools = client.lp.all_paginated()
        >>> client.get_pools_with_rewards()
    """

    def __init__(
        self,
        chain: ChainId | str,
        export_dir: str | Path = ".",
        snapshot: bool = True,
        snapshot_dir: str | Path | None = None,
        *,
        rpc_url: str | None = None,
    ) -> None:
        """
        Initialize SugarClient for a specific chain.

        Args:
            chain: Chain identifier (ChainId enum or string like "base", "op").
            rpc_url: Explicit RPC endpoint URL. If omitted, falls back to the
                chain's RPC environment variable (e.g. RPC_LINK_BASE), loaded
                from .env. Constructor injection lets you reuse RPC URLs you
                already derive from an Alchemy/Infura key without a parallel
                .env.
            export_dir: Base directory for data exports.
            snapshot: Whether to automatically persist every fetched dataset
                to the snapshot store (Sugar only serves real-time data, so
                snapshots build a local history across runs).
            snapshot_dir: Root directory for snapshots. Defaults to the
                SUGAR_SNAPSHOT_DIR env var, falling back to ./sugar-snapshots.

        Raises:
            ValueError: If chain is not supported.
            RpcConnectionError: If RPC connection fails.
        """
        self._config = get_chain_config(chain)
        self._provider = Web3Provider(self._config, rpc_url=rpc_url)
        self._export = ExportService(export_dir)
        self._snapshots = SnapshotStore(snapshot_dir) if snapshot else None

        # Initialize LP Sugar (always available)
        self._lp = LpSugar(
            self._provider,
            self._config.lp_sugar_address,
            self._config.connectors,
        )

        # Lazy-initialized optional contracts
        self._ve: VeSugar | None = None
        self._relay: RelaySugar | None = None
        self._rewards: RewardsSugar | None = None
        self._price_oracle: SpotPriceOracle | None = None
        self._price_provider: PriceProvider | None = None
        self._data_processor: DataProcessor | None = None

        # Cached data
        self._tokens_df: pd.DataFrame | None = None

        logger.info(f"SugarClient initialized for {self._config.name}")

    @property
    def chain(self) -> ChainId:
        """Current chain ID."""
        return self._config.chain_id

    @property
    def chain_name(self) -> str:
        """Current chain name."""
        return self._config.name

    @property
    def config(self) -> ChainConfig:
        """Current chain configuration."""
        return self._config

    @property
    def block_number(self) -> int:
        """Current block number."""
        return self._provider.block_number

    @property
    def lp(self) -> LpSugar:
        """LpSugar contract - always available."""
        return self._lp

    @property
    def ve(self) -> VeSugar:
        """
        VeSugar contract.

        Raises:
            ContractNotAvailableError: If VeSugar is not deployed on this chain.
        """
        if not self._config.has_ve:
            raise ContractNotAvailableError("VeSugar", self._config.name)

        if self._ve is None:
            self._ve = VeSugar(
                self._provider,
                self._config.ve_sugar_address,  # type: ignore
            )
        return self._ve

    @property
    def relay(self) -> RelaySugar:
        """
        RelaySugar contract.

        Raises:
            ContractNotAvailableError: If RelaySugar is not deployed on this chain.
        """
        if not self._config.has_relay:
            raise ContractNotAvailableError("RelaySugar", self._config.name)

        if self._relay is None:
            self._relay = RelaySugar(
                self._provider,
                self._config.relay_sugar_address,  # type: ignore
            )
        return self._relay

    @property
    def rewards(self) -> RewardsSugar:
        """
        RewardsSugar contract.

        Raises:
            ContractNotAvailableError: If RewardsSugar is not deployed on this chain.
        """
        if not self._config.has_rewards:
            raise ContractNotAvailableError("RewardsSugar", self._config.name)

        if self._rewards is None:
            self._rewards = RewardsSugar(
                self._provider,
                self._config.rewards_sugar_address,  # type: ignore
            )
        return self._rewards

    @property
    def prices(self) -> PriceProvider:
        """Price provider with fallback chain."""
        if self._price_provider is None:
            self._price_provider = self._create_price_provider()
        return self._price_provider

    @property
    def processor(self) -> DataProcessor:
        """Data processor service."""
        if self._data_processor is None:
            self._data_processor = DataProcessor(self.prices, self._provider)
        return self._data_processor

    def has_ve(self) -> bool:
        """Check if VeSugar is available on this chain."""
        return self._config.has_ve

    def has_relay(self) -> bool:
        """Check if RelaySugar is available on this chain."""
        return self._config.has_relay

    def has_rewards(self) -> bool:
        """Check if RewardsSugar is available on this chain."""
        return self._config.has_rewards

    def has_price_oracle(self) -> bool:
        """Check if Spot Price Oracle is available on this chain."""
        return self._config.has_price_oracle

    def _create_price_provider(self) -> PriceProvider:
        """Create price provider with all available sources."""
        oracle_source = None
        coingecko_source = None
        defillama_source = None

        # Create on-chain oracle source if available
        if self._config.has_price_oracle:
            if self._price_oracle is None:
                self._price_oracle = SpotPriceOracle(
                    self._provider,
                    self._config.price_oracle_address,  # type: ignore
                    self._config.connectors,
                )

            # By Sugar convention the first connector is the chain's stablecoin
            # (USDC), used for USD conversion.
            usdc_address = self._config.connectors[0] if self._config.connectors else None

            # Pass any already-cached token metadata so the oracle can adjust
            # rates for non-18-decimal tokens (e.g. 6-decimal USDC/USDT) on ANY
            # chain. If tokens haven't been fetched yet, get_tokens() will push
            # them in later (see below) — avoiding a prices<->get_tokens cycle.
            oracle_source = OraclePriceSource(
                self._price_oracle,
                usdc_address,
                tokens_df=self._tokens_df,
                chain_id=self._config.chain_id.value,
            )

        # Create CoinGecko source
        coingecko_source = CoinGeckoPriceSource(self._config.chain_id)

        # Create DefiLlama source
        defillama_source = DefiLlamaPriceSource(self._config.chain_id)

        return PriceProvider(
            oracle=oracle_source,
            coingecko=coingecko_source,
            defillama=defillama_source,
        )

    @staticmethod
    def _records(df: pd.DataFrame) -> list[dict]:
        """Convert a DataFrame to a list of plain dicts (JSON-friendly).

        A named/multi index (e.g. address, id, venft_id) is folded back in as a
        column so no data is lost; an anonymous RangeIndex is dropped.
        """
        if df.index.name is not None or isinstance(df.index, pd.MultiIndex):
            df = df.reset_index()
        return df.to_dict("records")

    def get_tokens(
        self, listed_only: bool = True, refresh: bool = False, df: bool = False
    ) -> list[dict] | pd.DataFrame:
        """
        Get token metadata.

        Args:
            listed_only: Whether to filter for listed tokens only.
            refresh: Whether to refresh cached data.
            df: If True, return a pandas DataFrame; otherwise a list[dict].

        Returns:
            Token metadata as list[dict] (default) or a DataFrame indexed by
            address when ``df=True``.
        """
        if self._tokens_df is None or refresh:
            raw_data = self._lp.tokens_paginated()
            self._tokens_df = self.processor.process_tokens(raw_data, listed_only=False)
            self._record_snapshot(self._tokens_df, "tokens")
            # Give the oracle token decimals so it can price non-18-decimal
            # tokens correctly. Only if a provider already exists — creating one
            # here would recurse (prices -> get_tokens -> processor -> prices).
            if self._price_provider is not None:
                self._price_provider.set_tokens_df(self._tokens_df)

        result = self._tokens_df[self._tokens_df["listed"]] if listed_only else self._tokens_df
        return result if df else self._records(result)

    def get_pools(self, filter_type: int = 0, df: bool = False) -> list[dict] | pd.DataFrame:
        """
        Get all liquidity pools.

        Args:
            filter_type: Filter type (0 = all, 1 = v2 only, 2 = CL only).
            df: If True, return a pandas DataFrame; otherwise a list[dict].

        Returns:
            Pool data as list[dict] (default) or a DataFrame when ``df=True``.
        """
        # Ensure tokens are loaded for symbol lookup
        tokens_df = self.get_tokens(listed_only=False, df=True)

        raw_data = self._lp.all_paginated(filter_type=filter_type)
        result = self.processor.process_lp_all(raw_data, tokens_df)
        self._record_snapshot(result, "pools")
        return result if df else self._records(result)

    def get_ve_positions(self, df: bool = False) -> list[dict] | pd.DataFrame:
        """
        Get all veNFT positions.

        Args:
            df: If True, return a pandas DataFrame; otherwise a list[dict].

        Returns:
            veNFT data as list[dict] (default) or a DataFrame indexed by ID
            when ``df=True``.

        Raises:
            ContractNotAvailableError: If VeSugar is not available.
        """
        raw_data = self.ve.all_paginated()
        result = self.processor.process_ve_all(raw_data)
        self._record_snapshot(result, "ve_positions")
        return result if df else self._records(result)

    def get_relays(
        self, filter_inactive: bool = True, df: bool = False
    ) -> list[dict] | pd.DataFrame:
        """
        Get all relay data.

        Args:
            filter_inactive: Whether to filter out inactive relays.
            df: If True, return a pandas DataFrame; otherwise a list[dict].

        Returns:
            Relay data as list[dict] (default) or a DataFrame indexed by
            venft_id when ``df=True``.

        Raises:
            ContractNotAvailableError: If RelaySugar is not available.
        """
        raw_data = self.relay.all()
        result = self.processor.process_relay_all(
            raw_data, filter_inactive=filter_inactive
        )
        self._record_snapshot(result, "relays")
        return result if df else self._records(result)

    def get_epochs_latest(self, df: bool = False) -> list[dict] | pd.DataFrame:
        """
        Get latest epoch rewards for all pools.

        Args:
            df: If True, return a pandas DataFrame; otherwise a list[dict].

        Returns:
            Epoch data as list[dict] (default) or a DataFrame when ``df=True``.

        Raises:
            ContractNotAvailableError: If RewardsSugar is not available.
        """
        tokens_df = self.get_tokens(listed_only=False, df=True)
        # Use pool count to inform pagination limit
        pool_count = self._lp.count()
        raw_data = self.rewards.epochs_latest_paginated(max_offset=pool_count)
        result = self.processor.process_epochs_latest(raw_data, tokens_df)
        self._record_snapshot(result, "epochs_latest")
        return result if df else self._records(result)

    def get_pools_with_rewards(
        self, only_with_rewards: bool = True, df: bool = False
    ) -> list[dict] | pd.DataFrame:
        """
        Get combined LP and epoch rewards data with priced fees and incentives.

        This is the main convenience method that combines:
        - LpSugar.all() pool data
        - RewardsSugar.epochsLatest() reward data
        - Priced incentives (voting incentives) and fees in USD

        Returned columns include:
        - tvl_usd: Total value locked (reserve0_usd + reserve1_usd)
        - pool_fees_usd: Trading fees (token0_fees_usd + token1_fees_usd)
        - projected_pool_fees_usd: Projected fees for full epoch
        - incentives_usd: Voting incentives in USD
        - gauge_fees_usd: Gauge fees in USD

        Args:
            only_with_rewards: If True (default), only include pools that have
                epoch rewards data. This is faster as it reduces the number of
                pools to process. If False, include all pools.
            df: If True, return a pandas DataFrame; otherwise a list[dict].

        Returns:
            Combined pool info + priced rewards as list[dict] (default) or a
            DataFrame when ``df=True``.

        Raises:
            ContractNotAvailableError: If RewardsSugar is not available.
        """
        tokens_df = self.get_tokens(listed_only=True, df=True)
        lp_df = self.get_pools(df=True)
        epochs_df = self.get_epochs_latest(df=True)

        result = self.processor.combine_lp_with_rewards(
            lp_df, epochs_df, tokens_df, only_with_rewards=only_with_rewards
        )
        self._record_snapshot(result, "pools_with_rewards")
        return result if df else self._records(result)

    def _token_amount(
        self,
        address: str,
        raw: int,
        decimals: int,
        symbol: str | None = None,
        price: bool = True,
    ) -> TokenAmount:
        """Build a priced TokenAmount from a raw on-chain integer."""
        amount = Decimal(raw) / (Decimal(10) ** decimals)
        price_usd = None
        price_source = None
        if price and raw != 0:
            try:
                result = self.prices.get_price_usd(address)
                if result is not None:
                    price_usd = result.price
                    price_source = result.source
            except Exception as exc:  # pricing must never break aggregation
                logger.debug(f"price lookup failed for {address}: {exc}")
        return TokenAmount(
            address=address,
            symbol=symbol or "?",
            decimals=decimals,
            amount=amount,
            amount_raw=raw,
            price_usd=price_usd,
            price_source=price_source,
        )

    def _token_meta(self) -> dict[str, tuple[str, int]]:
        """Map lower-cased token address -> (symbol, decimals)."""
        df = self.get_tokens(listed_only=False, df=True)
        return {
            str(addr).lower(): (row["symbol"], int(row["decimals"]))
            for addr, row in df.iterrows()
        }

    def positions_by_account(
        self, account: str, price: bool = True
    ) -> list[AccountPosition]:
        """
        Return an account's entire footprint on this chain as typed positions.

        Stitches veNFT locks (resolving Relay/managed-veNFT principal), and LP /
        concentrated-liquidity positions into one normalized, mergeable list.
        Every token carries a raw + human amount and, when ``price=True``, a USD
        price with its source.

        Args:
            account: Wallet address (any case).
            price: Whether to attach USD prices.

        Returns:
            List of AccountPosition. Use ``sugar.to_dict`` for plain dicts.
        """
        protocol = "aerodrome" if self._config.chain_id == ChainId.BASE else "velodrome"
        chain = self.chain_name
        chain_id = self._config.chain_id.value
        out: list[AccountPosition] = []
        meta = self._token_meta()  # cached token symbol/decimals lookup

        # --- veNFT locks (with Relay/managed-veNFT resolution) ---
        if self.has_ve():
            venfts = [VeNFT.from_tuple(v) for v in self.ve.by_account(account)]
            # For relay-deposited veNFTs, the exact principal + rewards live in
            # RelaySugar.account_venfts (ve.by_account reports amount=0).
            relay_map: dict[int, tuple[int, int]] = {}
            if self.has_relay() and any(v.managed_id != 0 for v in venfts):
                for r in self.relay.all(account):
                    for entry in r[16]:  # account_venfts: (venft_id, amount, rewards)
                        relay_map[int(entry[0])] = (int(entry[1]), int(entry[2]))

            for ve in venfts:
                if ve.managed_id != 0 and ve.id in relay_map:
                    principal_raw, reward_raw = relay_map[ve.id]
                    kind = PositionKind.RELAY
                else:
                    principal_raw = ve.amount_raw
                    reward_raw = int(ve.rebase_amount * (Decimal(10) ** ve.decimals))
                    kind = PositionKind.VE
                if principal_raw == 0 and reward_raw == 0:
                    continue
                sym, _ = meta.get(ve.token.lower(), ("?", ve.decimals))
                lock = self._token_amount(
                    ve.token, principal_raw, ve.decimals, symbol=sym, price=price
                )
                rewards = (
                    [self._token_amount(ve.token, reward_raw, ve.decimals, symbol=sym, price=price)]
                    if reward_raw
                    else []
                )
                out.append(
                    AccountPosition(
                        protocol=protocol,
                        chain=chain,
                        chain_id=chain_id,
                        kind=kind,
                        tokens=[lock],
                        rewards=rewards,
                        locked=True,
                        usd_value=(lock.usd or Decimal(0)),
                        meta={
                            "venft_id": ve.id,
                            "expires_at": ve.expires_at,
                            "managed_id": ve.managed_id,
                        },
                    )
                )

        # --- LP / concentrated-liquidity positions ---
        lp_positions = self.lp.positions_paginated(account)
        if lp_positions:
            # Map pool address -> token0/token1/type/emissions_token via get_pools
            # (byAddress reverts for some CL pools, so use the full pool set).
            pools_df = self.get_pools(df=True).reset_index()
            pool_map = {
                str(row["lp"]).lower(): row for _, row in pools_df.iterrows()
            }
            for p in lp_positions:
                pool_addr = p[1]
                pool = pool_map.get(pool_addr.lower())
                if pool is None:
                    continue
                t0, t1 = pool["token0"], pool["token1"]
                pool_type = pool["type"]
                emissions_token = pool["emissions_token"]
                s0, d0 = meta.get(t0.lower(), ("?", 18))
                s1, d1 = meta.get(t1.lower(), ("?", 18))
                se, de = meta.get(emissions_token.lower(), ("?", 18))

                tok0 = self._token_amount(t0, int(p[4]), d0, symbol=s0, price=price)
                tok1 = self._token_amount(t1, int(p[5]), d1, symbol=s1, price=price)

                rewards: list[TokenAmount] = []
                if p[8]:
                    rewards.append(self._token_amount(t0, int(p[8]), d0, symbol=s0, price=price))
                if p[9]:
                    rewards.append(self._token_amount(t1, int(p[9]), d1, symbol=s1, price=price))
                if p[10]:
                    rewards.append(
                        self._token_amount(
                            emissions_token, int(p[10]), de, symbol=se, price=price
                        )
                    )

                usd = (tok0.usd or Decimal(0)) + (tok1.usd or Decimal(0))
                out.append(
                    AccountPosition(
                        protocol=protocol,
                        chain=chain,
                        chain_id=chain_id,
                        kind=PositionKind.CL if pool_type > 0 else PositionKind.LP,
                        tokens=[tok0, tok1],
                        rewards=rewards,
                        pool=pool_addr,
                        usd_value=usd,
                        locked=False,
                        meta={"position_id": int(p[0]), "pool_type": int(pool_type)},
                    )
                )

        return out

    @property
    def snapshots(self) -> SnapshotStore | None:
        """Snapshot store (None if snapshotting was disabled)."""
        return self._snapshots

    def _record_snapshot(self, df: pd.DataFrame, dataset: str) -> None:
        """Persist a fetched dataset to the snapshot store (best-effort)."""
        if self._snapshots is None:
            return
        try:
            self._snapshots.save(
                df,
                dataset=dataset,
                chain=self._config.name.lower(),
                block=self.block_number,
            )
        except Exception as exc:
            # Snapshotting must never break a live fetch.
            logger.warning(f"Failed to snapshot {dataset}: {exc}")

    def load_snapshot(self, dataset: str, block: int | None = None) -> pd.DataFrame:
        """
        Load a previously snapshotted dataset for this chain.

        Args:
            dataset: Dataset name ("pools", "tokens", "ve_positions",
                "relays", "epochs_latest", "pools_with_rewards").
            block: Specific block to load. Defaults to the latest snapshot.

        Returns:
            The snapshotted DataFrame.

        Raises:
            FileNotFoundError: If no matching snapshot exists.
            RuntimeError: If snapshotting was disabled for this client.
        """
        if self._snapshots is None:
            raise RuntimeError("Snapshotting is disabled for this client")
        return self._snapshots.load(dataset, self._config.name.lower(), block=block)

    def snapshot_history(self, dataset: str) -> pd.DataFrame:
        """
        List recorded snapshots of a dataset for this chain.

        Args:
            dataset: Dataset name (see load_snapshot).

        Returns:
            DataFrame with columns block, fetched_at, rows, file.

        Raises:
            RuntimeError: If snapshotting was disabled for this client.
        """
        if self._snapshots is None:
            raise RuntimeError("Snapshotting is disabled for this client")
        return self._snapshots.history(dataset, self._config.name.lower())

    def export_dataframe(
        self,
        df: pd.DataFrame,
        name: str,
        subdirectory: str = "data",
        include_block: bool = True,
        index: bool = True,
    ) -> Path:
        """
        Export any DataFrame to CSV with standard naming.

        This is a generalized export function for any DataFrame.

        Args:
            df: DataFrame to export.
            name: Base name for the file (e.g., "pools", "tokens").
            subdirectory: Subdirectory within export dir (e.g., "data-pools").
            include_block: Whether to include block number in filename.
            index: Whether to include DataFrame index in output.

        Returns:
            Path to exported file.
        """
        chain = self._config.name.lower()
        if include_block:
            filename = f"{name}_{chain}_{self.block_number}.csv"
        else:
            filename = f"{name}_{chain}.csv"

        return self._export.to_csv(df, filename, subdirectory=subdirectory, index=index)
