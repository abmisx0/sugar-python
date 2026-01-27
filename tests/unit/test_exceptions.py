"""Tests for custom exceptions."""

import pytest

from sugar.core.exceptions import (
    ChainNotSupportedError,
    ContractNotAvailableError,
    DataProcessingError,
    PaginationError,
    PriceNotAvailableError,
    RpcConnectionError,
    SugarError,
)


class TestExceptionHierarchy:
    """Test exception class hierarchy."""

    def test_sugar_error_is_base(self) -> None:
        """SugarError should be the base exception."""
        assert issubclass(ContractNotAvailableError, SugarError)
        assert issubclass(ChainNotSupportedError, SugarError)
        assert issubclass(RpcConnectionError, SugarError)
        assert issubclass(PriceNotAvailableError, SugarError)
        assert issubclass(PaginationError, SugarError)
        assert issubclass(DataProcessingError, SugarError)

    def test_sugar_error_is_exception(self) -> None:
        """All custom exceptions should inherit from Exception."""
        assert issubclass(SugarError, Exception)


class TestContractNotAvailableError:
    """Test ContractNotAvailableError."""

    def test_message_formatting(self) -> None:
        """Error message should include contract and chain names."""
        error = ContractNotAvailableError("VeSugar", "Mode")
        assert "VeSugar" in str(error)
        assert "Mode" in str(error)

    def test_attributes(self) -> None:
        """Error should store contract and chain attributes."""
        error = ContractNotAvailableError("VeSugar", "Mode")
        assert error.contract_type == "VeSugar"
        assert error.chain_name == "Mode"


class TestChainNotSupportedError:
    """Test ChainNotSupportedError."""

    def test_message_formatting(self) -> None:
        """Error message should include chain name."""
        error = ChainNotSupportedError("unknown_chain")
        assert "unknown_chain" in str(error)

    def test_attributes(self) -> None:
        """Error should store chain attribute."""
        error = ChainNotSupportedError("unknown_chain")
        assert error.chain == "unknown_chain"


class TestRpcConnectionError:
    """Test RpcConnectionError."""

    def test_message_formatting(self) -> None:
        """Error message should include chain and details."""
        error = RpcConnectionError("Base", "connection timeout")
        assert "Base" in str(error)
        assert "connection timeout" in str(error)

    def test_attributes(self) -> None:
        """Error should store chain and details attributes."""
        error = RpcConnectionError("Base", "connection timeout")
        assert error.chain == "Base"
        assert error.details == "connection timeout"


class TestPriceNotAvailableError:
    """Test PriceNotAvailableError."""

    def test_message_formatting(self) -> None:
        """Error message should include token address."""
        error = PriceNotAvailableError("0x1234")
        assert "0x1234" in str(error)

    def test_attributes(self) -> None:
        """Error should store token attribute."""
        error = PriceNotAvailableError("0x1234")
        assert error.token_address == "0x1234"


class TestPaginationError:
    """Test PaginationError."""

    def test_basic_message(self) -> None:
        """Error should accept method and offset."""
        error = PaginationError("all", 100, "timeout")
        assert "all" in str(error)
        assert "100" in str(error)


class TestDataProcessingError:
    """Test DataProcessingError."""

    def test_basic_message(self) -> None:
        """Error should accept a basic message."""
        error = DataProcessingError("Processing failed")
        assert "Processing failed" in str(error)


class TestExceptionCatching:
    """Test that exceptions can be caught properly."""

    def test_catch_specific(self) -> None:
        """Specific exceptions should be catchable."""
        with pytest.raises(ContractNotAvailableError):
            raise ContractNotAvailableError("VeSugar", "Mode")

    def test_catch_base(self) -> None:
        """Base SugarError should catch derived exceptions."""
        with pytest.raises(SugarError):
            raise ContractNotAvailableError("VeSugar", "Mode")
