"""Tests for price provider service."""

from __future__ import annotations

from decimal import Decimal
from unittest.mock import MagicMock, patch

import pytest

from sugar.config.chains import ChainId
from sugar.core.exceptions import PriceNotAvailableError
from sugar.services.price_provider import (
    CoinGeckoPriceSource,
    DefiLlamaPriceSource,
    OraclePriceSource,
    PriceProvider,
    PriceResult,
)


class TestOraclePriceSource:
    """Test on-chain oracle price source."""

    def test_get_price_usd(self) -> None:
        """Should get price from oracle."""
        mock_oracle = MagicMock()
        # Oracle returns rate as Decimal
        mock_oracle.get_rate.return_value = Decimal("2000")

        source = OraclePriceSource(mock_oracle, "0xusdc")
        price = source.get_price_usd("0xweth")

        assert price == Decimal("2000")

    def test_get_price_usd_no_usdc(self) -> None:
        """Should fallback to ETH rate when no USDC address configured."""
        mock_oracle = MagicMock()
        mock_oracle.get_rate_to_eth.return_value = Decimal("1")

        source = OraclePriceSource(mock_oracle, None)
        price = source.get_price_usd("0xweth")

        # Returns ETH-denominated rate
        assert price == Decimal("1")

    def test_get_price_usd_oracle_error(self) -> None:
        """Should return None on oracle error."""
        mock_oracle = MagicMock()
        mock_oracle.get_rate.side_effect = Exception("Oracle error")
        mock_oracle.get_rate_to_eth.side_effect = Exception("Oracle error")

        source = OraclePriceSource(mock_oracle, "0xusdc")
        price = source.get_price_usd("0xweth")

        assert price is None


class TestCoinGeckoPriceSource:
    """Test CoinGecko price source."""

    @patch("sugar.services.price_provider.requests.Session")
    def test_get_price_usd(self, mock_session_class: MagicMock) -> None:
        """Should get price from CoinGecko."""
        mock_session = MagicMock()
        mock_session_class.return_value = mock_session
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"0xweth": {"usd": 2000.0}}
        mock_session.get.return_value = mock_response

        source = CoinGeckoPriceSource(ChainId.BASE)
        price = source.get_price_usd("0xweth")

        assert price == Decimal("2000.0")

    @patch("sugar.services.price_provider.requests.Session")
    def test_get_price_usd_not_found(self, mock_session_class: MagicMock) -> None:
        """Should return None when token not found."""
        mock_session = MagicMock()
        mock_session_class.return_value = mock_session
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {}
        mock_session.get.return_value = mock_response

        source = CoinGeckoPriceSource(ChainId.BASE)
        price = source.get_price_usd("0xunknown")

        assert price is None

    @patch("sugar.services.price_provider.requests.Session")
    def test_get_price_usd_api_error(self, mock_session_class: MagicMock) -> None:
        """Should return None on API error."""
        mock_session = MagicMock()
        mock_session_class.return_value = mock_session
        mock_session.get.side_effect = Exception("Network error")

        source = CoinGeckoPriceSource(ChainId.BASE)
        price = source.get_price_usd("0xweth")

        assert price is None


class TestDefiLlamaPriceSource:
    """Test DefiLlama price source."""

    @patch("sugar.services.price_provider.requests.Session")
    def test_get_price_usd(self, mock_session_class: MagicMock) -> None:
        """Should get price from DefiLlama."""
        mock_session = MagicMock()
        mock_session_class.return_value = mock_session
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "coins": {"base:0xweth": {"price": 2000.0}}
        }
        mock_session.get.return_value = mock_response

        source = DefiLlamaPriceSource(ChainId.BASE)
        price = source.get_price_usd("0xweth")

        assert price == Decimal("2000.0")

    @patch("sugar.services.price_provider.requests.Session")
    def test_get_price_usd_not_found(self, mock_session_class: MagicMock) -> None:
        """Should return None when token not found."""
        mock_session = MagicMock()
        mock_session_class.return_value = mock_session
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"coins": {}}
        mock_session.get.return_value = mock_response

        source = DefiLlamaPriceSource(ChainId.BASE)
        price = source.get_price_usd("0xunknown")

        assert price is None


class TestPriceProvider:
    """Test composite price provider."""

    def test_fallback_to_coingecko(self) -> None:
        """Should fallback to CoinGecko when oracle fails."""
        mock_oracle = MagicMock()
        mock_oracle.get_price_usd.return_value = None

        mock_coingecko = MagicMock()
        mock_coingecko.get_price_usd.return_value = Decimal("2000")

        mock_defillama = MagicMock()

        provider = PriceProvider(
            oracle=mock_oracle,
            coingecko=mock_coingecko,
            defillama=mock_defillama,
        )

        result = provider.get_price_usd("0xweth")

        assert result is not None
        assert result.price == Decimal("2000")
        assert result.source == "coingecko"
        mock_oracle.get_price_usd.assert_called_once()
        mock_coingecko.get_price_usd.assert_called_once()

    def test_fallback_to_defillama(self) -> None:
        """Should fallback to DefiLlama when CoinGecko fails."""
        mock_oracle = MagicMock()
        mock_oracle.get_price_usd.return_value = None

        mock_coingecko = MagicMock()
        mock_coingecko.get_price_usd.return_value = None

        mock_defillama = MagicMock()
        mock_defillama.get_price_usd.return_value = Decimal("2000")

        provider = PriceProvider(
            oracle=mock_oracle,
            coingecko=mock_coingecko,
            defillama=mock_defillama,
        )

        result = provider.get_price_usd("0xweth")

        assert result is not None
        assert result.price == Decimal("2000")
        assert result.source == "defillama"

    def test_oracle_priority(self) -> None:
        """Should use oracle first when available."""
        mock_oracle = MagicMock()
        mock_oracle.get_price_usd.return_value = Decimal("2000")

        mock_coingecko = MagicMock()
        mock_defillama = MagicMock()

        provider = PriceProvider(
            oracle=mock_oracle,
            coingecko=mock_coingecko,
            defillama=mock_defillama,
        )

        result = provider.get_price_usd("0xweth")

        assert result is not None
        assert result.price == Decimal("2000")
        assert result.source == "oracle"
        mock_coingecko.get_price_usd.assert_not_called()
        mock_defillama.get_price_usd.assert_not_called()

    def test_no_sources(self) -> None:
        """Should return None when no sources available."""
        provider = PriceProvider(
            oracle=None,
            coingecko=None,
            defillama=None,
        )

        result = provider.get_price_usd("0xweth")

        assert result is None

    def test_all_sources_fail(self) -> None:
        """Should return None when all sources fail."""
        mock_oracle = MagicMock()
        mock_oracle.get_price_usd.return_value = None

        mock_coingecko = MagicMock()
        mock_coingecko.get_price_usd.return_value = None

        mock_defillama = MagicMock()
        mock_defillama.get_price_usd.return_value = None

        provider = PriceProvider(
            oracle=mock_oracle,
            coingecko=mock_coingecko,
            defillama=mock_defillama,
        )

        result = provider.get_price_usd("0xweth")

        assert result is None

    def test_raise_on_failure(self) -> None:
        """Should raise exception when requested and all fail."""
        mock_oracle = MagicMock()
        mock_oracle.get_price_usd.return_value = None

        provider = PriceProvider(oracle=mock_oracle)

        with pytest.raises(PriceNotAvailableError):
            provider.get_price_usd("0xweth", raise_on_failure=True)

    def test_get_prices_batch(self) -> None:
        """Should get multiple prices."""
        mock_coingecko = MagicMock()
        mock_coingecko.get_price_usd.side_effect = [
            Decimal("2000"),
            Decimal("1"),
        ]

        provider = PriceProvider(coingecko=mock_coingecko)

        results = provider.get_prices_batch(["0xweth", "0xusdc"])

        assert len(results) == 2
        assert results["0xweth"] is not None
        assert results["0xweth"].price == Decimal("2000")
        assert results["0xusdc"] is not None
        assert results["0xusdc"].price == Decimal("1")
