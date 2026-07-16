"""Tests for the typed data models."""

from __future__ import annotations

import json
from decimal import Decimal

from sugar.models import (
    AccountPosition,
    PositionKind,
    TokenAmount,
    VeNFT,
    to_dict,
)


class TestTokenAmount:
    def test_usd_derived(self) -> None:
        t = TokenAmount(
            address="0xabc",
            symbol="AERO",
            decimals=18,
            amount=Decimal("10"),
            amount_raw=10 * 10**18,
            price_usd=Decimal("1.25"),
            price_source="oracle",
        )
        assert t.usd == Decimal("12.50")

    def test_usd_none_when_unpriced(self) -> None:
        t = TokenAmount("0xabc", "AERO", 18, Decimal("10"), 10 * 10**18)
        assert t.usd is None


class TestVeNFT:
    def test_in_relay_flag(self) -> None:
        base = {
            "id": 1, "account": "0xacc", "decimals": 18, "amount": Decimal(0), "amount_raw": 0,
            "voting_amount": Decimal(0), "governance_amount": Decimal(5),
            "rebase_amount": Decimal(0), "expires_at": 0, "voted_at": 0, "token": "0xt",
            "permanent": False, "delegate_id": 0,
        }
        assert VeNFT(managed_id=0, **base).in_relay is False
        assert VeNFT(managed_id=42, **base).in_relay is True


class TestToDict:
    def test_nested_tokenamount_keeps_usd_and_enum_becomes_value(self) -> None:
        pos = AccountPosition(
            protocol="aerodrome",
            chain="Base",
            chain_id=8453,
            kind=PositionKind.VE,
            tokens=[
                TokenAmount("0xabc", "AERO", 18, Decimal("2"), 2 * 10**18,
                            price_usd=Decimal("1.5"), price_source="oracle")
            ],
            usd_value=Decimal("3"),
            locked=True,
        )
        d = to_dict(pos)

        assert d["kind"] == "ve"  # enum -> value
        assert d["tokens"][0]["usd"] == Decimal("3.0")  # derived property preserved
        assert d["tokens"][0]["price_source"] == "oracle"
        # JSON-serializable with default=str for Decimals
        assert json.dumps(d, default=str)
