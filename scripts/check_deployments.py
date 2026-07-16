"""Check pinned Sugar contract addresses against canonical deployments.

Fetches the official deployment files from
``velodrome-finance/sugar/main/deployments`` and compares the LP / Rewards /
VE / Relay Sugar addresses to what is pinned in ``sugar.config.chains``.

Addresses are deliberately pinned in the library (deterministic, offline,
reproducible) rather than fetched at runtime. Run this to detect when an
upstream redeploy has made a pin stale:

    python scripts/check_deployments.py

Exits non-zero if any pinned address drifts from canonical, so it can gate CI.
"""

from __future__ import annotations

import sys

import requests

from sugar.config.chains import CHAIN_CONFIGS, ChainId

BASE_URL = "https://raw.githubusercontent.com/velodrome-finance/sugar/main/deployments"

# ChainId -> deployment filename in the upstream repo.
DEPLOYMENT_FILES: dict[ChainId, str] = {
    ChainId.BASE: "base.env",
    ChainId.OPTIMISM: "optimism.env",
    ChainId.MODE: "mode.env",
    ChainId.LISK: "lisk.env",
    ChainId.FRAXTAL: "fraxtal.env",
    ChainId.INK: "ink.env",
    ChainId.SONEIUM: "soneium.env",
    ChainId.METAL: "metall2.env",
    ChainId.CELO: "celo.env",
    ChainId.SUPERSEED: "superseed.env",
    ChainId.SWELL: "swell.env",
    ChainId.UNICHAIN: "unichain.env",
}

# ChainConfig field -> upstream env var prefix (suffixed with the chain id).
FIELDS: dict[str, str] = {
    "lp_sugar_address": "LP_SUGAR_ADDRESS",
    "rewards_sugar_address": "REWARDS_SUGAR_ADDRESS",
    "ve_sugar_address": "VE_SUGAR_ADDRESS",
    "relay_sugar_address": "RELAY_SUGAR_ADDRESS",
}


def parse_env(text: str) -> dict[str, str]:
    """Parse KEY=value / KEY = value lines from an .env file."""
    out: dict[str, str] = {}
    for raw in text.splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        out[key.strip()] = value.strip().strip('"').strip("'")
    return out


def main() -> int:
    drift: list[str] = []
    errors: list[str] = []

    for chain_id, filename in DEPLOYMENT_FILES.items():
        config = CHAIN_CONFIGS[chain_id]
        try:
            resp = requests.get(f"{BASE_URL}/{filename}", timeout=15)
            resp.raise_for_status()
        except Exception as exc:  # noqa: BLE001 - report and continue
            errors.append(f"{config.name}: could not fetch {filename} ({type(exc).__name__})")
            continue

        env = parse_env(resp.text)
        for field, prefix in FIELDS.items():
            pinned = getattr(config, field)
            canonical = env.get(f"{prefix}_{chain_id.value}")
            if canonical is None:
                continue  # not deployed / not listed upstream
            if pinned is None or pinned.lower() != canonical.lower():
                drift.append(
                    f"{config.name} {field}: pinned={pinned} canonical={canonical}"
                )

    if errors:
        print("Fetch errors (could not verify):")
        for e in errors:
            print(f"  ! {e}")

    if drift:
        print("\nDRIFT DETECTED — pinned addresses differ from canonical:")
        for d in drift:
            print(f"  ✗ {d}")
        return 1

    if errors:
        # Nothing drifted, but we couldn't verify everything — fail so a
        # scheduled CI run doesn't go green having checked nothing.
        print("\nCould not verify all chains (see fetch errors above).")
        return 2

    print("All pinned addresses match canonical deployments. ✓")
    return 0


if __name__ == "__main__":
    sys.exit(main())
