# Sugar Python Library

Python library for interacting with Velodrome/Aerodrome Sugar Protocol contracts on multiple EVM chains.

## Features

- **Multi-chain support**: 12 chains including Base, Optimism, Mode, Lisk, and more
- **Full contract coverage**: LpSugar, VeSugar, RelaySugar, RewardsSugar
- **Price integration**: On-chain oracle with CoinGecko and DefiLlama fallbacks
- **Persistent snapshots**: Every fetch is automatically indexed to disk for posterity (Sugar contracts only serve real-time data)
- **Type safety**: Full type hints, py.typed marker, and typed dataclass models
- **Dict-first, pandas-optional**: readers return `list[dict]` by default; pass `df=True` for a DataFrame
- **Automatic pagination**: Handles large datasets automatically

## Requirements

- Python 3.10+
- An RPC endpoint for at least one supported chain (public endpoints work; a free [dRPC](https://drpc.org/) or [Alchemy](https://www.alchemy.com/) key is recommended for full-chain crawls)

## Installation

The distribution is **`sugar-defi`** (the import stays `import sugar`).

```bash
# core: typed/dict reads + positions_by_account (no pandas)
pip install "git+https://github.com/abmisx0/sugar-python.git"

# with pandas: DataFrame returns (df=True), CSV export, snapshots
pip install "sugar-defi[export] @ git+https://github.com/abmisx0/sugar-python.git"

# pin a release
pip install "git+https://github.com/abmisx0/sugar-python.git@v0.3.0"
```

> Use a virtualenv (or `pipx`) — on a Homebrew/system Python, `pip install` may
> refuse with a PEP 668 "externally-managed-environment" error. `python -m venv
> .venv && source .venv/bin/activate` first.

Add it to `requirements.txt`:

```
sugar-defi @ git+https://github.com/abmisx0/sugar-python.git@v0.3.0
```

or `pyproject.toml`:

```toml
dependencies = [
    "sugar-defi @ git+https://github.com/abmisx0/sugar-python.git@v0.3.0",
]
```

## From Zero to CSV

```bash
git clone https://github.com/abmisx0/sugar-python.git
cd sugar-python
pip install -e ".[export]"   # [export] adds pandas for DataFrames/CSV/snapshots
cp .env.example .env         # then edit .env with your RPC endpoints
python examples/export_pools.py
```

This exports token metadata and pool data for Base under `output/`, and writes
block-stamped snapshots to `sugar-snapshots/`. See [EXPORTS.md](EXPORTS.md) for
the snapshot layout and the other example scripts.

> **pandas is optional.** The core install (above) gives you the typed/dict
> reads and `positions_by_account` with no pandas. Add the `export` extra for
> DataFrame returns (`df=True`), `export_dataframe`, and snapshots — see
> [Installation](#installation).

## Quick Start

```python
from sugar import SugarClient, ChainId

# RPC comes from the constructor (recommended) or the RPC_LINK_<CHAIN> env var
client = SugarClient(ChainId.BASE, rpc_url="https://base-mainnet.example/<key>")

# Readers return list[dict] by default (JSON-friendly, no pandas needed)
pools = client.get_pools()               # list[dict]
tokens = client.get_tokens()             # list[dict]
combined = client.get_pools_with_rewards()

# Prefer a pandas DataFrame? Pass df=True
pools_df = client.get_pools(df=True)     # DataFrame

# Export a DataFrame to CSV (pair with df=True)
client.export_dataframe(client.get_pools(df=True), "pools")
client.export_dataframe(client.get_tokens(df=True), "tokens", include_block=False)
```

> **Upgrading from 0.1.x?** Readers now return `list[dict]` by default instead of
> a DataFrame. Add `df=True` to any call to restore the old behavior. See
> [CHANGELOG.md](CHANGELOG.md).

### An account's entire footprint (portfolio)

`positions_by_account` returns a wallet's veNFT locks and LP/CL positions as one
normalized, priced list — Relay/managed-veNFT principal resolved, each token with
raw + human amount, USD price, and price source:

```python
from sugar import SugarClient, ChainId, to_dict

client = SugarClient(ChainId.BASE)
positions = client.positions_by_account("0x…")          # list[AccountPosition]
rows = [to_dict(p) for p in positions]                   # JSON-friendly dicts

for p in positions:
    print(p.symbol, p.usd_value, "+", p.rewards_usd, "rewards =", p.total_usd)
```

Each `AccountPosition` has:

- `symbol` — readable label (`"AERO"`, `"USDC/USDe"`) so you don't dig into `tokens[0]`
- `usd_value` — **principal only** (sum of `tokens`)
- `rewards_usd` — claimable rewards (sum of `rewards`), **not** in `usd_value`
- `total_usd` — `usd_value + rewards_usd` (use this for the full position value)
- `tokens` / `rewards` — each a `TokenAmount` with `amount`, `amount_raw`, `price_usd`, `price_source`

> **Principal vs. rewards.** `usd_value` is principal only; claimable rewards live
> in `rewards`. Sum `total_usd` (or `rewards_usd`) so you don't miss claimable value.

Across chains in one call, with graceful per-chain degradation:

```python
from sugar import positions_across_chains, ChainId

portfolio = positions_across_chains("0x…", chains=[ChainId.BASE, ChainId.OPTIMISM, ChainId.INK])
print(portfolio.usd_value, portfolio.rewards_usd, portfolio.total_usd)  # principal, rewards, both
print(portfolio.errors)        # any chains that failed (e.g. RPC down) — not raised
```

### Prices come from the on-chain oracle

USD prices are read from the Sugar spot-price **oracle** (falling back to
CoinGecko then DefiLlama), and each `TokenAmount` records which via
`price_source`. Oracle prices are on-chain spot and can differ from a CEX /
CoinGecko mid by a few percent — expect small reconciliation differences, and
use `price_source` (and the raw `amount`) if you want to re-price yourself.

### Providing an RPC endpoint

Pass `rpc_url` directly — handy when you already derive RPC URLs from an
Alchemy/Infura key and don't want a parallel `.env`:

```python
client = SugarClient(ChainId.BASE, rpc_url=my_alchemy_base_url)
```

If `rpc_url` is omitted, the client falls back to the chain's environment
variable (e.g. `RPC_LINK_BASE`), loaded from `.env`. See
[Configuration](#configuration).

### Plain dicts vs DataFrames

Readers return `list[dict]` by default — JSON-friendly and pandas-free, ideal
for merging into your own pipeline:

```python
rows = client.get_pools_with_rewards()   # list[dict]
```

Pass `df=True` on any reader to get a pandas DataFrame instead. Typed dataclass
models are also available (`from sugar import Token, VeNFT, Relay, TokenAmount`)
for callers who prefer attribute access; `to_dict()` converts them to plain
dicts.

### Read-only guarantee

This library is **read-only**. It issues `eth_call` requests only — it never
builds, signs, or broadcasts transactions and never needs a private key. Safe
to point at any account or contract for analysis.

To see per-call RPC progress while fetching, enable logging first:

```python
from sugar import setup_logging

setup_logging()  # INFO-level progress to stderr
```

## Configuration

Create a `.env` file with your RPC endpoints (copy `.env.example` to start):

```bash
# Required: At least one RPC endpoint
RPC_LINK_BASE=https://mainnet.base.org
RPC_LINK_OP=https://mainnet.optimism.io

# Optional: Additional chains
RPC_LINK_MODE=https://mainnet.mode.network/
RPC_LINK_LISK=https://rpc.api.lisk.com/
RPC_LINK_FRAXTAL=https://rpc.frax.com/
RPC_LINK_INK=https://rpc-gel.inkonchain.com/
RPC_LINK_SONEIUM=https://rpc.soneium.org/
RPC_LINK_METAL=https://rpc.metall2.com/
RPC_LINK_CELO=https://forno.celo.org
RPC_LINK_SUPERSEED=https://mainnet.superseed.xyz
RPC_LINK_SWELL=https://swell-mainnet.alt.technology
RPC_LINK_UNICHAIN=https://mainnet.unichain.org
```

## API Reference

### SugarClient

The main facade for interacting with Sugar Protocol.

```python
from sugar import SugarClient, ChainId

# Initialize with ChainId enum or string
client = SugarClient(ChainId.BASE)
client = SugarClient("base")  # Also works

# Properties
client.chain          # ChainId enum
client.chain_name     # "Base", "Optimism", etc.
client.block_number   # Current block number
```

### Contract Access

```python
# LP Sugar (always available)
client.lp.all_paginated()              # All pools with pagination
client.lp.by_address("0x...")          # Single pool by address
client.lp.tokens_paginated()           # All tokens
client.lp.count()                      # Total pool count

# VE Sugar (Base, Optimism only)
if client.has_ve():
    client.ve.all_paginated()          # All veNFTs
    client.ve.by_account("0x...")      # veNFTs by owner
    client.ve.by_id(123)               # Single veNFT

# Relay Sugar (Base, Optimism only)
if client.has_relay():
    client.relay.all()                 # All relays

# Rewards Sugar (all chains)
client.rewards.epochs_latest_paginated()     # Latest epoch rewards
client.rewards.epochs_by_address("0x...")    # Pool's epoch history
client.rewards.rewards(venft_id=123)         # Rewards for a veNFT
```

### Data Methods

High-level readers return `list[dict]` by default; pass `df=True` for a pandas
DataFrame. `get_tokens`, `get_ve_positions`, and `get_relays` work without
pandas installed; `get_pools`, `get_epochs_latest`, and `get_pools_with_rewards`
do their pricing/analytics in pandas, so they need the `export` extra.

```python
tokens = client.get_tokens()                 # list[dict] (pandas-free)
ve = client.get_ve_positions()               # list[dict] (pandas-free)
relays = client.get_relays()                 # list[dict] (pandas-free)

pools = client.get_pools()                   # list[dict] (needs sugar[export])
epochs = client.get_epochs_latest()          # list[dict] (needs sugar[export])
combined = client.get_pools_with_rewards()   # list[dict] (needs sugar[export])

pools_df = client.get_pools(df=True)         # pandas DataFrame
```

### Persistent Snapshots

Sugar contracts only serve real-time state — once a block passes, the data is
gone unless you saved it. When you fetch data as a DataFrame (`df=True`), the
client snapshots it to disk automatically, stamped with the block number,
building a local history across runs. (Snapshots are pandas-backed, so they need
the `export` extra.)

```python
client = SugarClient(ChainId.BASE)          # snapshots on by default
pools = client.get_pools(df=True)           # writes sugar-snapshots/base/pools/<block>.parquet

client.snapshot_history("pools")            # DataFrame: block, fetched_at, rows, file
old = client.load_snapshot("pools")         # latest snapshot
old = client.load_snapshot("pools", block=31000000)  # specific block

# Opt out, or relocate the store
client = SugarClient(ChainId.BASE, snapshot=False)
client = SugarClient(ChainId.BASE, snapshot_dir="/my/archive")
```

Snapshots are written as parquet (via `pyarrow`, included in the `export`
extra), falling back to gzipped CSV if parquet isn't available. The default
directory is `./sugar-snapshots`, overridable with the `SUGAR_SNAPSHOT_DIR`
environment variable. Datasets snapshotted: `pools`, `tokens`, `ve_positions`,
`relays`, `epochs_latest`, `pools_with_rewards`.

### Export Methods

```python
# Export any DataFrame to CSV with standard naming
client.export_dataframe(df, "pools")                    # data/pools_base_12345678.csv
client.export_dataframe(df, "tokens", include_block=False)  # data/tokens_base.csv
client.export_dataframe(df, "custom", subdirectory="my-data")  # my-data/custom_base_12345678.csv
```

Paths are relative to the client's `export_dir` (defaults to the working
directory).

### Price Provider

Access token prices with automatic fallback:

```python
# Get price through the price provider
result = client.prices.get_price_usd("0x...")
if result:
    print(f"Price: ${result.price}, Source: {result.source}")

# Batch price fetching
results = client.prices.get_prices_batch(["0x...", "0x..."])
```

Price sources (in order):

1. **On-chain Oracle** (Spot Price Aggregator)
2. **CoinGecko** (API fallback)
3. **DefiLlama** (Secondary API fallback)

### Combined Pools with Rewards

`get_pools_with_rewards()` returns rows (list[dict], or a DataFrame with
`df=True`) combining:

- **Pool data**: symbol, reserves, TVL, pool type, etc.
- **Epoch rewards**: votes, emissions for the current epoch
- **USD-priced fields**:
  - `tvl_usd` - Total value locked (reserve0_usd + reserve1_usd)
  - `pool_fees_usd` - Trading fees earned (token0_fees_usd + token1_fees_usd)
  - `projected_pool_fees_usd` - Projected fees for full epoch
  - `incentives_usd` - Voting incentives in USD
  - `gauge_fees_usd` - Gauge fees in USD

```python
# As a DataFrame (needs sugar[export])
df = client.get_pools_with_rewards(df=True)
print(df[["symbol", "tvl_usd", "incentives_usd", "gauge_fees_usd", "votes"]])

# Or as plain rows
for row in client.get_pools_with_rewards():
    print(row["symbol"], row["tvl_usd"], row["incentives_usd"])
```

## Supported Chains

| Chain | ID | LP | VE | Relay | Rewards | Oracle |
|-------|-----|:--:|:--:|:-----:|:-------:|:------:|
| Base | 8453 | ✓ | ✓ | ✓ | ✓ | ✓ |
| Optimism | 10 | ✓ | ✓ | ✓ | ✓ | ✓ |
| Mode | 34443 | ✓ | - | - | ✓ | ✓ |
| Lisk | 1135 | ✓ | - | - | ✓ | ✓ |
| Fraxtal | 252 | ✓ | - | - | ✓ | ✓ |
| Ink | 57073 | ✓ | - | - | ✓ | ✓ |
| Soneium | 1868 | ✓ | - | - | ✓ | ✓ |
| Metal | 1750 | ✓ | - | - | ✓ | ✓ |
| Celo | 42220 | ✓ | - | - | ✓ | ✓ |
| Superseed | 5330 | ✓ | - | - | ✓ | ✓ |
| Swell | 1923 | ✓ | - | - | ✓ | ✓ |
| Unichain | 130 | ✓ | - | - | ✓ | ✓ |

## Examples

See the `examples/` directory for runnable usage examples
(and [EXPORTS.md](EXPORTS.md) for where they write output):

- `quickstart.py` - Connect and read pools with rewards
- `export_pools.py` - Export token and pool data to CSV under `output/`
- `ve_holders.py` - Aggregate veNFT governance weight by holder
- `list_relays.py` - List active Relays (managed veNFTs)

## Development

### Run Tests

```bash
# Unit tests
pytest tests/unit/

# Integration tests (requires RPC endpoints)
pytest tests/integration/ -m integration
```

### Type Checking

```bash
mypy sugar/
```

### Linting

```bash
ruff check sugar/
ruff format sugar/
```

## Project Structure

```
sugar-python/
├── sugar/
│   ├── __init__.py          # Public API exports
│   ├── core/
│   │   ├── client.py        # SugarClient facade
│   │   ├── web3_provider.py # Web3 connection management
│   │   ├── pagination.py    # Pagination utilities
│   │   └── exceptions.py    # Custom exceptions
│   ├── contracts/
│   │   ├── lp_sugar.py      # LP Sugar wrapper
│   │   ├── ve_sugar.py      # VE Sugar wrapper
│   │   ├── relay_sugar.py   # Relay Sugar wrapper
│   │   ├── rewards_sugar.py # Rewards Sugar wrapper
│   │   └── price_oracle.py  # Spot Price Oracle wrapper
│   ├── config/
│   │   ├── chains.py        # Chain configurations
│   │   ├── columns.py       # DataFrame column definitions
│   │   └── abis/            # Contract ABIs
│   ├── services/
│   │   ├── data_processor.py  # Data transformation & USD pricing
│   │   ├── price_provider.py  # Multi-source price fetching
│   │   ├── snapshot.py        # Persistent block-stamped snapshots
│   │   └── export.py          # CSV/JSON export utilities
│   └── utils/
│       ├── wei.py           # Wei conversion utilities
│       ├── cache.py         # TTL caching decorator
│       └── logging.py       # Logging configuration
├── tests/
│   ├── unit/                # Unit tests (mocked)
│   └── integration/         # Integration tests (live RPC)
└── examples/                # Usage examples
```

## License

GNU General Public License v3.0 or later (GPL-3.0-or-later)

See [LICENSE](LICENSE) file for full license text.
