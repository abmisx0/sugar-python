"""Tests for the typed data models."""

from __future__ import annotations

import json
from decimal import Decimal

from sugar.models import (
    AccountPosition,
    Portfolio,
    PositionKind,
    Relay,
    Token,
    TokenAmount,
    VeNFT,
    to_dict,
)


def _priced(symbol: str, amount: str, price: str, decimals: int = 18) -> TokenAmount:
    return TokenAmount(
        address="0x" + symbol.lower(),
        symbol=symbol,
        decimals=decimals,
        amount=Decimal(amount),
        amount_raw=int(Decimal(amount) * (10**decimals)),
        price_usd=Decimal(price),
        price_source="oracle",
    )


class TestPositionDerivedFields:
    def _pos(self) -> AccountPosition:
        return AccountPosition(
            protocol="velodrome",
            chain="Ink",
            chain_id=57073,
            kind=PositionKind.CL,
            tokens=[_priced("USDC", "100", "1"), _priced("USDe", "50", "1")],
            rewards=[_priced("USDC", "5", "1"), _priced("VELO", "10", "0.02")],
            usd_value=Decimal("150"),
        )

    def test_symbol_rewards_total(self) -> None:
        p = self._pos()
        assert p.symbol == "USDC/USDe"          # #4 convenience label
        assert p.usd_value == Decimal("150")    # principal only
        assert p.rewards_usd == Decimal("5.20")  # 5*1 + 10*0.02
        assert p.total_usd == Decimal("155.20")  # #2 principal + rewards

    def test_to_dict_folds_derived_fields(self) -> None:
        d = to_dict(self._pos())
        assert d["symbol"] == "USDC/USDe"
        assert d["rewards_usd"] == Decimal("5.20")
        assert d["total_usd"] == Decimal("155.20")

    def test_portfolio_totals(self) -> None:
        port = Portfolio(positions=[self._pos(), self._pos()])
        assert port.usd_value == Decimal("300")
        assert port.rewards_usd == Decimal("10.40")
        assert port.total_usd == Decimal("310.40")


class TestFromTuple:
    def test_token_from_tuple(self) -> None:
        # (address, symbol, decimals, account_balance, listed, emerging)
        tok = Token.from_tuple(("0xAbC", "AERO", 18, 5 * 10**18, True, False))
        assert tok.address == "0xAbC"
        assert tok.symbol == "AERO"
        assert tok.decimals == 18
        assert tok.listed is True
        assert tok.account_balance_raw == 5 * 10**18

    def test_venft_from_tuple_scales_by_decimals(self) -> None:
        row = (7, "0xacc", 18, 3 * 10**18, 2 * 10**18, 1 * 10**18, 0,
               123, 0, [], "0xtok", False, 0, 9)
        ve = VeNFT.from_tuple(row)
        assert ve.id == 7
        assert ve.amount == Decimal("3")
        assert ve.amount_raw == 3 * 10**18
        assert ve.voting_amount == Decimal("2")
        assert ve.governance_amount == Decimal("1")
        assert ve.expires_at == 123
        assert ve.managed_id == 9 and ve.in_relay is True

    def test_relay_from_tuple(self) -> None:
        row = (1, 18, 100 * 10**18, 90 * 10**18, 10 * 10**18, 0, [], "0xtok",
               4 * 10**18, True, 0, ["0xmgr"], "0xrelay", True, False, "Relay X", [11, 12])
        r = Relay.from_tuple(row)
        assert r.venft_id == 1
        assert r.amount == Decimal("100")
        assert r.voting_amount == Decimal("90")
        assert r.used_voting_amount == Decimal("10")
        assert r.name == "Relay X"
        assert r.compounder is True and r.inactive is False
        assert r.managers == ["0xmgr"] and r.account_venfts == [11, 12]


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
