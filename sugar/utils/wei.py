"""Wei conversion utilities for Sugar Python library."""

from decimal import Decimal


def from_wei(value: int, decimals: int = 18) -> Decimal:
    """
    Convert wei (smallest unit) to a decimal value.

    Args:
        value: Value in wei (smallest unit).
        decimals: Number of decimals for the token (default: 18).

    Returns:
        Decimal representation of the value.

    Examples:
        >>> from_wei(1000000000000000000, 18)
        Decimal('1')
        >>> from_wei(1000000, 6)  # USDC
        Decimal('1')
    """
    value = int(value)
    decimals = int(decimals)
    return Decimal(value) / Decimal(10**decimals)


def to_wei(value: Decimal | int | float, decimals: int = 18) -> int:
    """
    Convert a decimal value to wei (smallest unit).

    Args:
        value: Decimal value to convert.
        decimals: Number of decimals for the token (default: 18).

    Returns:
        Integer value in wei.

    Examples:
        >>> to_wei(1.5, 18)
        1500000000000000000
        >>> to_wei(1.5, 6)  # USDC
        1500000
    """
    return int(Decimal(str(value)) * Decimal(10**decimals))


def format_token_amount(
    value: int,
    decimals: int = 18,
    precision: int = 4,
) -> str:
    """
    Format a token amount for display.

    Args:
        value: Value in wei (smallest unit).
        decimals: Number of decimals for the token.
        precision: Number of decimal places in output.

    Returns:
        Formatted string representation.

    Examples:
        >>> format_token_amount(1234567890123456789, 18, 2)
        '1.23'
    """
    amount = from_wei(value, decimals)
    return f"{amount:.{precision}f}"
