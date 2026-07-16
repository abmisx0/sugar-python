# Changelog

## 0.2.0

### Breaking change: readers return `list[dict]` by default

The data readers now return a **`list[dict]`** (plain, JSON-friendly rows)
instead of a pandas DataFrame. Affected methods:

- `get_tokens()`
- `get_pools()`
- `get_ve_positions()`
- `get_relays()`
- `get_epochs_latest()`
- `get_pools_with_rewards()`

**How to migrate:** pass `df=True` to get the previous DataFrame behavior
unchanged.

```python
# 0.1.x
pools = client.get_pools()              # DataFrame

# 0.2.0
pools = client.get_pools()              # list[dict]  (new default)
pools = client.get_pools(df=True)       # DataFrame   (same as 0.1.x)
```

So any 0.1.x call site keeps working by adding `df=True`:

```python
df = client.get_pools(df=True)
df = client.get_ve_positions(df=True)
df = client.get_pools_with_rewards(df=True)
```

`export_dataframe(...)` still expects a DataFrame, so pair it with `df=True`:

```python
client.export_dataframe(client.get_pools(df=True), "pools")
```

### Added

- **Typed dataclass models** (`sugar.models`): `TokenAmount` (raw + human
  amount, `price_usd`, `price_source`, derived `usd`), `Token`, `VeNFT`
  (`in_relay`), `Relay`, `AccountPosition`, `PositionKind`, and `to_dict()` for
  JSON-friendly conversion. Exported from the top-level `sugar` package.
- **`rpc_url` constructor injection**: `SugarClient(chain, rpc_url=...)` with the
  `RPC_LINK_<CHAIN>` env var as fallback.
- **Deployment drift-check**: `scripts/check_deployments.py` and a scheduled CI
  job compare pinned contract addresses against the canonical
  `velodrome-finance/sugar` deployments.

### Fixed

- Never include the RPC URL (may carry an API key) in connection-error messages.
- Don't log Etherscan HTTP errors verbatim (they embed the `apikey`).
- `VeSugar.all_paginated()` no longer loops forever on persistent RPC failure.
- `setup_logging()` is idempotent (no duplicate handlers).
- Zero prices from CoinGecko/DefiLlama are treated as "no price" (fallback
  continues) instead of being cached as a valid `$0`.
- A corrupt snapshot manifest line no longer breaks the whole dataset.
- Synced stale LpSugar/RewardsSugar addresses across all 12 chains to canonical.

## 0.1.0

Initial packaged release: multi-chain Sugar reads (LP, veNFT, Relay, Rewards),
price integration (oracle + CoinGecko + DefiLlama), persistent snapshots.
