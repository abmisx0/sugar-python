# Sugar Python Library

Python library for interacting with Velodrome/Aerodrome Sugar Protocol contracts on multiple EVM chains.

## Features

- **Multi-chain support**: 12 chains including Base, Optimism, Mode, Lisk, and more
- **Full contract coverage**: LpSugar, VeSugar, RelaySugar, RewardsSugar
- **Price integration**: On-chain oracle with CoinGecko and DefiLlama fallbacks
- **Type safety**: Full type hints and py.typed marker
- **Pandas integration**: All data returned as DataFrames
- **Automatic pagination**: Handles large datasets automatically

## Installation

```bash
pip install -e .
```

Or install dependencies directly:

```bash
pip install pandas web3 python-dotenv requests
```

## Quick Start

```python
from sugar import SugarClient, ChainId

# Initialize client for a chain
client = SugarClient(ChainId.BASE)

# Get all liquidity pools
pools = client.get_pools()

# Get token metadata
tokens = client.get_tokens()

# Get combined pools with rewards (fees + incentives priced in USD)
combined = client.get_pools_with_rewards()

# Export any DataFrame to CSV
client.export_dataframe(pools, "pools")
client.export_dataframe(tokens, "tokens", include_block=False)
```

## Configuration

Create a `.env` file with your RPC endpoints:

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

### Export Methods

```python
# Export any DataFrame to CSV with standard naming
client.export_dataframe(df, "pools")                    # exports/data/pools_base_12345678.csv
client.export_dataframe(df, "tokens", include_block=False)  # exports/data/tokens_base.csv
client.export_dataframe(df, "custom", subdirectory="my-data")  # exports/my-data/custom_base_12345678.csv
```

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

See the `examples/` directory for complete usage examples:

- `update-lp-data.py` - Export LP pool and token data
- `update-relay-data.py` - Export relay data
- `update-lock-data.py` - Export veNFT lock data
- `pools-with-rewards.py` - Combined LP + rewards with pricing (supports multi-chain)
- `max-lock-analysis.py` - Analyze max-locked veNFTs
- `pool-voters.py` - Analyze voters for specific pools
- `veToken-holders.py` - Analyze veToken holder distribution

### Multi-chain Example

The `pools-with-rewards.py` script supports fetching data from multiple chains:

```bash
# Aerodrome (Base only)
python examples/pools-with-rewards.py --aero

# Velodrome (all other chains)
python examples/pools-with-rewards.py --velo

# All chains
python examples/pools-with-rewards.py --all
```

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
mypy src/sugar/
```

### Linting

```bash
ruff check src/
ruff format src/
```

## Project Structure

```
sugar-python/
├── src/sugar/
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

GNU General Public License v3.0 (GPL-3.0)

See [LICENSE](LICENSE) file for full license text.
