"""Helpers for optional dependencies.

pandas (and pyarrow) are optional — only DataFrame returns, CSV export, and
snapshots need them. Typed/dict reads and ``positions_by_account`` do not, so
pandas is imported lazily via :func:`require_pandas` with a clear install hint.
"""

from __future__ import annotations

from typing import Any

_INSTALL_HINT = (
    "This feature needs pandas. Install the export extra:\n"
    "    pip install 'sugar-python[export]'"
)


def require_pandas() -> Any:
    """Return the pandas module, or raise a helpful ImportError if missing."""
    try:
        import pandas as pd
    except ImportError as exc:  # pragma: no cover - trivial
        raise ImportError(_INSTALL_HINT) from exc
    return pd


def has_pandas() -> bool:
    """True if pandas is importable."""
    try:
        import pandas  # noqa: F401

        return True
    except ImportError:
        return False
