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
    usd_value: Decimal = Decimal(0)
    locked: bool = False
    meta: dict = field(default_factory=dict)  # kind-specific extras (venft id, expiry, ...)


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
    if dataclasses.is_dataclass(obj) and not isinstance(obj, type):
        return {f.name: to_dict(getattr(obj, f.name)) for f in dataclasses.fields(obj)}
    if isinstance(obj, Enum):
        return obj.value
    if isinstance(obj, (list, tuple)):
        return [to_dict(v) for v in obj]
    if isinstance(obj, dict):
        return {k: to_dict(v) for k, v in obj.items()}
    return obj
