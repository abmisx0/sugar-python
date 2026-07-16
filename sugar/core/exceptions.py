"""Custom exceptions for Sugar Python library."""


class SugarError(Exception):
    """Base exception for all Sugar-related errors."""

    pass


class ContractNotAvailableError(SugarError):
    """Raised when a contract is not available on the specified chain."""

    def __init__(self, contract_type: str, chain_name: str) -> None:
        self.contract_type = contract_type
        self.chain_name = chain_name
        super().__init__(f"{contract_type} is not deployed on {chain_name}")


class ChainNotSupportedError(SugarError):
    """Raised when a chain is not supported."""

    def __init__(self, chain: str) -> None:
        self.chain = chain
        super().__init__(f"Chain '{chain}' is not supported")


class RpcConnectionError(SugarError):
    """Raised when RPC connection fails."""

    def __init__(self, chain: str, details: str | None = None) -> None:
        self.chain = chain
        self.details = details
        message = f"Failed to connect to RPC for chain '{chain}'"
        if details:
            message += f": {details}"
        super().__init__(message)


class PriceNotAvailableError(SugarError):
    """Raised when price cannot be fetched from any source."""

    def __init__(self, token_address: str, sources_tried: list[str] | None = None) -> None:
        self.token_address = token_address
        self.sources_tried = sources_tried or []
        sources_str = ", ".join(self.sources_tried) if self.sources_tried else "none"
        super().__init__(
            f"Could not fetch price for token {token_address}. Sources tried: {sources_str}"
        )


class PaginationError(SugarError):
    """Raised when pagination encounters an error."""

    def __init__(self, method: str, offset: int, details: str | None = None) -> None:
        self.method = method
        self.offset = offset
        self.details = details
        message = f"Pagination error in {method} at offset {offset}"
        if details:
            message += f": {details}"
        super().__init__(message)


class DataProcessingError(SugarError):
    """Raised when data processing fails."""

    def __init__(self, operation: str, details: str | None = None) -> None:
        self.operation = operation
        self.details = details
        message = f"Data processing error during {operation}"
        if details:
            message += f": {details}"
        super().__init__(message)
