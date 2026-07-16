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

## From Zero to CSV

```bash
git clone https://github.com/abmisx0/sugar-python.git
cd sugar-python
pip install -e .
cp .env.example .env     # then edit .env with your RPC endpoints
python examples/export_pools.py
```

This exports token metadata and pool data for Base under `output/`, and writes
block-stamped snapshots to `sugar-snapshots/`. See [EXPORTS.md](EXPORTS.md) for
the snapshot layout and the other example scripts.

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
total_usd = sum(p.usd_value for p in positions)
rows = [to_dict(p) for p in positions]                   # JSON-friendly dicts
```

Across chains in one call, with graceful per-chain degradation:

```python
from sugar import positions_across_chains, ChainId

portfolio = positions_across_chains("0x…", chains=[ChainId.BASE, ChainId.OPTIMISM, ChainId.INK])
print(portfolio.usd_value)     # total across all chains
print(portfolio.errors)        # any chains that failed (e.g. RPC down) — not raised
```

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

High-level methods that return processed DataFrames:

```python
# Get processed DataFrames
pools_df = client.get_pools()                # All pools
tokens_df = client.get_tokens()              # Token metadata
ve_df = client.get_ve_positions()            # veNFT positions
relays_df = client.get_relays()              # Relay data
epochs_df = client.get_epochs_latest()       # Latest epoch rewards

# Combined data with priced rewards
combined_df = client.get_pools_with_rewards()
```

### Persistent Snapshots

Sugar contracts only serve real-time state — once a block passes, the data is
gone unless you saved it. The client therefore snapshots every fetched dataset
to disk automatically, stamped with the block number, building a local history
across runs:

```python
client = SugarClient(ChainId.BASE)          # snapshots on by default
pools = client.get_pools()                  # writes sugar-snapshots/base/pools/<block>.csv.gz

client.snapshot_history("pools")            # DataFrame: block, fetched_at, rows, file
old = client.load_snapshot("pools")         # latest snapshot
old = client.load_snapshot("pools", block=31000000)  # specific block

# Opt out, or relocate the store
client = SugarClient(ChainId.BASE, snapshot=False)
client = SugarClient(ChainId.BASE, snapshot_dir="/my/archive")
```

Snapshots are written as parquet when `pyarrow` is installed
(`pip install -e ".[parquet]"`), otherwise as gzipped CSV. The default
directory is `./sugar-snapshots` and can be overridden with the
`SUGAR_SNAPSHOT_DIR` environment variable. Datasets snapshotted: `pools`,
`tokens`, `ve_positions`, `relays`, `epochs_latest`, `pools_with_rewards`.

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

The `get_pools_with_rewards()` method returns a DataFrame with:

- **Pool data**: symbol, reserves, TVL, pool type, etc.
- **Epoch rewards**: votes, emissions for the current epoch
- **USD-priced columns**:
  - `tvl_usd` - Total value locked (reserve0_usd + reserve1_usd)
  - `pool_fees_usd` - Trading fees earned (token0_fees_usd + token1_fees_usd)
  - `projected_pool_fees_usd` - Projected fees for full epoch
  - `incentives_usd` - Voting incentives in USD
  - `gauge_fees_usd` - Gauge fees in USD

```python
# Get combined data
df = client.get_pools_with_rewards()

# Access key columns
print(df[['symbol', 'tvl_usd', 'incentives_usd', 'gauge_fees_usd', 'votes']])
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
