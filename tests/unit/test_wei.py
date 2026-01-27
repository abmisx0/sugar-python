"""Tests for wei conversion utilities."""

from decimal import Decimal

import pytest

from sugar.utils.wei import from_wei, to_wei


class TestFromWei:
    """Test from_wei conversion."""

    def test_default_18_decimals(self) -> None:
        """Should convert with 18 decimals by default."""
        result = from_wei(1000000000000000000)
        assert result == Decimal("1")

    def test_custom_decimals(self) -> None:
        """Should respect custom decimals."""
        # USDC has 6 decimals
        result = from_wei(1000000, decimals=6)
        assert result == Decimal("1")

    def test_8_decimals(self) -> None:
        """Should handle 8 decimals (WBTC)."""
        result = from_wei(100000000, decimals=8)
        assert result == Decimal("1")

    def test_zero(self) -> None:
        """Should handle zero."""
        result = from_wei(0)
        assert result == Decimal("0")

    def test_large_value(self) -> None:
        """Should handle large values."""
        result = from_wei(1000000000000000000000000)
        assert result == Decimal("1000000")

    def test_fractional_value(self) -> None:
        """Should handle fractional values."""
        result = from_wei(500000000000000000)
        assert result == Decimal("0.5")

    def test_string_input(self) -> None:
        """Should handle string input."""
        result = from_wei("1000000000000000000")
        assert result == Decimal("1")

    def test_precision(self) -> None:
        """Should maintain precision."""
        result = from_wei(123456789012345678)
        expected = Decimal("123456789012345678") / Decimal("1000000000000000000")
        assert result == expected


class TestToWei:
    """Test to_wei conversion."""

    def test_default_18_decimals(self) -> None:
        """Should convert with 18 decimals by default."""
        result = to_wei(1)
        assert result == 1000000000000000000

    def test_custom_decimals(self) -> None:
        """Should respect custom decimals."""
        result = to_wei(1, decimals=6)
        assert result == 1000000

    def test_decimal_input(self) -> None:
        """Should handle Decimal input."""
        result = to_wei(Decimal("1.5"))
        assert result == 1500000000000000000

    def test_float_input(self) -> None:
        """Should handle float input."""
        result = to_wei(0.5)
        assert result == 500000000000000000

    def test_string_input(self) -> None:
        """Should handle string input."""
        result = to_wei("1")
        assert result == 1000000000000000000

    def test_zero(self) -> None:
        """Should handle zero."""
        result = to_wei(0)
        assert result == 0

    def test_large_value(self) -> None:
        """Should handle large values."""
        result = to_wei(1000000)
        assert result == 1000000000000000000000000


class TestRoundTrip:
    """Test round-trip conversion."""

    def test_round_trip_integer(self) -> None:
        """Round-trip should preserve value for integers."""
        original = 1000000000000000000
        result = to_wei(from_wei(original))
        assert result == original

    def test_round_trip_decimal(self) -> None:
        """Round-trip should preserve value for decimals."""
        original = Decimal("1.5")
        result = from_wei(to_wei(original))
        assert result == original

    def test_round_trip_with_custom_decimals(self) -> None:
        """Round-trip should work with custom decimals."""
        original = 1000000
        result = to_wei(from_wei(original, decimals=6), decimals=6)
        assert result == original
