"""Typed data models for Sugar Python.

These dataclasses are the primary, pandas-free return types. Every reader can
return these (or plain dicts via :func:`to_dict`); DataFrame output is an opt-in
convenience layer on top (see ``sugar[export]``).

Amounts are exposed both raw (on-chain integer) and human-scaled (``Decimal``
with token decimals applied), so callers can trust or re-derive values. USD
valuations carry their price source for auditability.
"""

from __future__ import annotations

import dataclasses
from dataclasses import dataclass, field
from decimal import Decimal
from enum import Enum


class PositionKind(str, Enum):
    """Normalized position categories across protocols."""

    VE = "ve"          # voting-escrow lock
    LP = "lp"          # classic (v2) liquidity position
    CL = "cl"          # concentrated liquidity position
    STAKED = "staked"  # gauge-staked liquidity
    RELAY = "relay"    # veNFT deposited into a Relay (managed veNFT)


@dataclass(slots=True)
class TokenAmount:
    """A token quantity, optionally priced in USD.

    ``amount`` is human-scaled (decimals applied); ``amount_raw`` is the raw
    on-chain integer. ``usd`` is derived and never stored, so it can never drift
    from ``amount``/``price_usd``.
    """

    address: str
    symbol: str
    decimals: int
    amount: Decimal
    amount_raw: int
    price_usd: Decimal | None = None
    price_source: str | None = None  # e.g. "oracle", "coingecko", "defillama"

    @property
    def usd(self) -> Decimal | None:
        """Human amount * price, or None if unpriced."""
        if self.price_usd is None:
            return None
        return self.amount * self.price_usd


@dataclass(slots=True)
class Token:
    """ERC-20 token metadata as surfaced by LpSugar.tokens()."""

    address: str
    symbol: str
    decimals: int
    listed: bool
    account_balance_raw: int = 0
    price_usd: Decimal | None = None
    price_source: str | None = None

    @classmethod
    def from_tuple(cls, t: tuple) -> Token:
        """Build from a raw LpSugar.tokens() row.

        Layout: (token_address, symbol, decimals, account_balance, listed, emerging).
        """
        return cls(
            address=t[0],
            symbol=t[1],
            decimals=int(t[2]),
            listed=bool(t[4]),
            account_balance_raw=int(t[3]),
        )


@dataclass(slots=True)
class VeNFT:
    """A voting-escrow NFT (lock) from VeSugar.

    ``governance_amount`` is the only balance that remains populated once a
    veNFT is deposited into a Relay (see :class:`Relay` and PositionKind.RELAY).
    """

    id: int
    account: str
    decimals: int
    amount: Decimal            # locked principal (human-scaled)
    amount_raw: int
    voting_amount: Decimal     # voting power (decays)
    governance_amount: Decimal # survives Relay deposit
    rebase_amount: Decimal
    expires_at: int
    voted_at: int
    token: str
    permanent: bool
    delegate_id: int
    managed_id: int            # non-zero => deposited into this managed/relay veNFT

    @property
    def in_relay(self) -> bool:
        """True when this veNFT is deposited into a Relay/managed veNFT."""
        return self.managed_id != 0

    @classmethod
    def from_tuple(cls, t: tuple) -> VeNFT:
        """Build from a raw VeSugar.all()/byId() row.

        Layout: (id, account, decimals, amount, voting_amount, governance_amount,
        rebase_amount, expires_at, voted_at, votes, token, permanent, delegate_id,
        managed_id). Balances are scaled by ``decimals``.
        """
        decimals = int(t[2])
        scale = Decimal(10) ** decimals
        return cls(
            id=int(t[0]),
            account=t[1],
            decimals=decimals,
            amount=Decimal(t[3]) / scale,
            amount_raw=int(t[3]),
            voting_amount=Decimal(t[4]) / scale,
            governance_amount=Decimal(t[5]) / scale,
            rebase_amount=Decimal(t[6]) / scale,
            expires_at=int(t[7]),
            voted_at=int(t[8]),
            token=t[10],
            permanent=bool(t[11]),
            delegate_id=int(t[12]),
            managed_id=int(t[13]),
        )


@dataclass(slots=True)
class Relay:
    """A Relay (autocompounder / managed veNFT) from RelaySugar.

    ``amount``/``voting_amount`` are the *managed* principal and voting power the
    relay controls on behalf of depositors — the principal that individual
    deposited veNFTs report as ~0 via VotingEscrow.locked().
    """

    venft_id: int
    decimals: int
    amount: Decimal
    amount_raw: int
    voting_amount: Decimal
    used_voting_amount: Decimal
    token: str
    compounded: Decimal
    withdrawable: bool
    name: str
    relay: str
    compounder: bool
    inactive: bool
    managers: list[str] = field(default_factory=list)
    account_venfts: list[int] = field(default_factory=list)

    @classmethod
    def from_tuple(cls, t: tuple) -> Relay:
        """Build from a raw RelaySugar.all() row.

        Layout: (venft_id, decimals, amount, voting_amount, used_voting_amount,
        voted_at, votes, token, compounded, withdrawable, run_at, managers, relay,
        compounder, inactive, name, account_venfts). Balances scaled by ``decimals``.
        """
        decimals = int(t[1])
        scale = Decimal(10) ** decimals
        return cls(
            venft_id=int(t[0]),
            decimals=decimals,
            amount=Decimal(t[2]) / scale,
            amount_raw=int(t[2]),
            voting_amount=Decimal(t[3]) / scale,
            used_voting_amount=Decimal(t[4]) / scale,
            token=t[7],
            compounded=Decimal(t[8]) / scale,
            withdrawable=bool(t[9]),
            name=t[15],
            relay=t[12],
            compounder=bool(t[13]),
            inactive=bool(t[14]),
            managers=list(t[11]),
            account_venfts=list(t[16]),
        )


@dataclass(slots=True)
class AccountPosition:
    """A single normalized position held by an account, across protocols/chains.

    This is the flat, mergeable shape returned by
    ``SugarClient.positions_by_account`` — a common schema you can concatenate
    across wallets and chains into one book.
    """

    protocol: str          # "aerodrome" | "velodrome"
    chain: str
    chain_id: int
    kind: PositionKind
    tokens: list[TokenAmount] = field(default_factory=list)
    rewards: list[TokenAmount] = field(default_factory=list)
    pool: str | None = None
    usd_value: Decimal = Decimal(0)  # PRINCIPAL only (sum of tokens); see total_usd
    locked: bool = False
    meta: dict = field(default_factory=dict)  # kind-specific extras (venft id, expiry, ...)

    @property
    def symbol(self) -> str:
        """Readable label for the position — e.g. "AERO" or "USDC/USDC.e".

        Convenience so callers don't have to reach into ``tokens[0]``.
        """
        return "/".join(t.symbol for t in self.tokens)

    @property
    def rewards_usd(self) -> Decimal:
        """Total USD of claimable rewards (0 for unpriced)."""
        return sum((r.usd for r in self.rewards if r.usd is not None), Decimal(0))

    @property
    def total_usd(self) -> Decimal:
        """Principal + claimable rewards. ``usd_value`` alone is principal only."""
        return self.usd_value + self.rewards_usd


@dataclass(slots=True)
class ChainError:
    """A per-chain failure captured during a multi-chain query."""

    chain: str
    chain_id: int
    error: str


@dataclass(slots=True)
class Portfolio:
    """Result of a multi-chain positions query.

    Holds whatever succeeded (``positions``) plus per-chain failures
    (``errors``) so one unreachable RPC never sinks the whole call.
    """

    positions: list[AccountPosition] = field(default_factory=list)
    errors: list[ChainError] = field(default_factory=list)

    @property
    def usd_value(self) -> Decimal:
        """Total principal USD across all positions (excludes rewards)."""
        return sum((p.usd_value for p in self.positions), Decimal(0))

    @property
    def rewards_usd(self) -> Decimal:
        """Total claimable rewards USD across all positions."""
        return sum((p.rewards_usd for p in self.positions), Decimal(0))

    @property
    def total_usd(self) -> Decimal:
        """Principal + claimable rewards across all positions."""
        return sum((p.total_usd for p in self.positions), Decimal(0))


def to_dict(obj: object) -> object:
    """Recursively convert dataclasses/enums to plain (JSON-friendly) structures.

    Dataclasses -> dict, Enum -> its value, lists/tuples -> list, and derived
    ``@property`` values on :class:`TokenAmount` are folded in. ``Decimal`` is
    left intact for precision — pass ``default=str`` to ``json.dumps`` to
    serialize.
    """
    if isinstance(obj, TokenAmount):
        out = {f.name: to_dict(getattr(obj, f.name)) for f in dataclasses.fields(obj)}
        out["usd"] = to_dict(obj.usd)
        return out
    if isinstance(obj, AccountPosition):
        out = {f.name: to_dict(getattr(obj, f.name)) for f in dataclasses.fields(obj)}
        # fold in the derived convenience fields
        out["symbol"] = obj.symbol
        out["rewards_usd"] = to_dict(obj.rewards_usd)
        out["total_usd"] = to_dict(obj.total_usd)
        return out
    if dataclasses.is_dataclass(obj) and not isinstance(obj, type):
        return {f.name: to_dict(getattr(obj, f.name)) for f in dataclasses.fields(obj)}
    if isinstance(obj, Enum):
        return obj.value
    if isinstance(obj, (list, tuple)):
        return [to_dict(v) for v in obj]
    if isinstance(obj, dict):
        return {k: to_dict(v) for k, v in obj.items()}
    return obj
