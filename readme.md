# Sugar Python Library

Python library for interacting with Sugar Protocol contracts on multiple EVM chains.

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

# Export data to CSV
client.export_pools()
client.export_tokens()
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
# Export to CSV
client.export_pools()              # data-lp/lp_all_base_*.csv
client.export_tokens()             # data-lp/lp_tokens_base.csv
client.export_ve_positions()       # data-ve/ve_all_base_*.csv
client.export_relays()             # data-relay/relay_all_base_*.csv
client.export_epochs()             # data-rewards/epochs_latest_base_*.csv
client.export_pools_with_rewards() # data-combined/pools_with_rewards_base_*.csv
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

## Supported Chains

| Chain | ID | LP | VE | Relay | Rewards | Oracle |
|-------|-----|:--:|:--:|:-----:|:-------:|:------:|
| Base | 8453 | Yes | Yes | Yes | Yes | Yes |
| Optimism | 10 | Yes | Yes | Yes | Yes | Yes |
| Mode | 34443 | Yes | - | - | Yes | Yes |
| Lisk | 1135 | Yes | - | - | Yes | Yes |
| Fraxtal | 252 | Yes | - | - | Yes | Yes |
| Ink | 57073 | Yes | - | - | Yes | Yes |
| Soneium | 1868 | Yes | - | - | Yes | Yes |
| Metal | 1750 | Yes | - | - | Yes | Yes |
| Celo | 42220 | Yes | - | - | Yes | Yes |
| Superseed | 5330 | Yes | - | - | Yes | Yes |
| Swell | 1923 | Yes | - | - | Yes | Yes |
| Unichain | 130 | Yes | - | - | Yes | Yes |

## Examples

See the `examples/` directory for complete usage examples:

- `update-lp-data.py` - Export LP pool and token data
- `update-relay-data.py` - Export relay data
- `update-lock-data.py` - Export veNFT lock data
- `pools-with-rewards.py` - Combined LP + rewards with pricing
- `max-lock-analysis.py` - Analyze max-locked veNFTs
- `pool-voters.py` - Analyze voters for specific pools
- `veToken-holders.py` - Analyze veToken holder distribution

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
│   ├── __init__.py          # Public API
│   ├── core/
│   │   ├── client.py        # SugarClient facade
│   │   ├── web3_provider.py # Web3 connection
│   │   ├── pagination.py    # Pagination utilities
│   │   └── exceptions.py    # Custom exceptions
│   ├── contracts/
│   │   ├── lp_sugar.py      # LP Sugar wrapper
│   │   ├── ve_sugar.py      # VE Sugar wrapper
│   │   ├── relay_sugar.py   # Relay Sugar wrapper
│   │   ├── rewards_sugar.py # Rewards Sugar wrapper
│   │   └── price_oracle.py  # Spot Price Oracle
│   ├── config/
│   │   ├── chains.py        # Chain configurations
│   │   ├── addresses.py     # Contract addresses
│   │   ├── columns.py       # DataFrame columns
│   │   └── abis/            # Contract ABIs
│   ├── services/
│   │   ├── data_processor.py  # Data transformation
│   │   ├── price_provider.py  # Price fetching
│   │   └── export.py          # CSV/JSON export
│   └── utils/
│       ├── wei.py           # Wei conversion
│       └── cache.py         # Caching utilities
├── tests/
│   ├── unit/                # Unit tests
│   └── integration/         # Integration tests
└── examples/                # Usage examples
```

## License

GNU General Public License v3.0 (GPL-3.0)

See [LICENSE](LICENSE) file for full license text.
