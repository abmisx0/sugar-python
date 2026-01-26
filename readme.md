# Sugar Python Library

Python wrapper for Velodrome/Aerodrome Sugar contracts across 12 Superchain deployments.

## Supported Chains

| Chain | LP Sugar | Rewards Sugar | VE Sugar | Relay Sugar |
|-------|:--------:|:-------------:|:--------:|:-----------:|
| Optimism | ✅ | ✅ | ✅ | ✅ |
| Base | ✅ | ✅ | ✅ | ✅ |
| Mode | ✅ | ✅ | ❌ | ❌ |
| Lisk | ✅ | ✅ | ❌ | ❌ |
| Fraxtal | ✅ | ✅ | ❌ | ❌ |
| Metal L2 | ✅ | ✅ | ❌ | ❌ |
| Ink | ✅ | ✅ | ❌ | ❌ |
| Soneium | ✅ | ✅ | ❌ | ❌ |
| Superseed | ✅ | ✅ | ❌ | ❌ |
| Swell | ✅ | ✅ | ❌ | ❌ |
| Unichain | ✅ | ✅ | ❌ | ❌ |
| Celo | ✅ | ✅ | ❌ | ❌ |

## Installation

### Dependencies

```bash
pip install pandas web3 python-dotenv
```

Optional (for Dune queries):
```bash
pip install dune-client
```

### Configuration

1. Copy `.env.example` to `.env`:
```bash
cp .env.example .env
```

2. Add RPC URLs for the chains you want to use. Free RPCs available at [chainlist.org](https://chainlist.org).

## Usage

### Basic Usage

```python
from sugar import Sugar

# Initialize for any supported chain
sugar = Sugar('base')  # or 'op', 'mode', 'lisk', etc.

# Get all LP data
lp_data = sugar.lp_all()

# Get token list
tokens = sugar.lp_tokens()
```

### LpSugar Methods

```python
# Get all liquidity pools
lp_data = sugar.lp_all(limit=500, index_lp=False)

# Get token data
tokens = sugar.lp_tokens(limit=1000, listed=True)

# Get epoch data for a pool
epochs = sugar.lp_epochsByAddress(address='0x...', limit=50)
```

### RewardsSugar Methods (All Chains)

```python
# Get latest epoch data for all pools
epochs = sugar.rewards_epochs_latest(limit=100)

# Get epoch history for a specific pool
pool_epochs = sugar.rewards_epochs_by_address(address='0x...', limit=50)

# Get claimable rewards for a veNFT
rewards = sugar.rewards_claimable(venft_id=12345)

# Get rewards for a veNFT on a specific pool
pool_rewards = sugar.rewards_by_pool(venft_id=12345, pool_address='0x...')
```

### VeSugar Methods (OP/Base Only)

```python
sugar = Sugar('op')

# Get all veNFT data
ve_data, block = sugar.ve_all()

# Get voters for specific pools
sugar.voters(pool_address='0x...', block_num=block)
```

### RelaySugar Methods (OP/Base Only)

```python
sugar = Sugar('base')

# Get all relay data
relay_data, block = sugar.relay_all()

# Get depositors for a specific relay
sugar.relay_depositors(mveNFT_ID=12345, block_num=block)
```

## Chain Configuration

All chain configurations are in `chains.py`:

```python
from chains import list_chains, chains_with_ve, get_chain

# List all supported chains
print(list_chains())
# ['op', 'base', 'mode', 'lisk', 'fraxtal', 'metal', 'ink', 'soneium', 'superseed', 'swell', 'unichain', 'celo']

# Chains with VeSugar
print(chains_with_ve())
# ['op', 'base']

# Get chain config
config = get_chain('base')
print(config['contracts']['lp_sugar'])
# '0x9DE6Eab7a910A288dE83a04b6A43B52Fd1246f1E'
```

## Data Output

Data is cached to directories by type:
- `data-lp/` - LP and token data
- `data-ve/` - veNFT data (OP/Base)
- `data-relay/` - Relay data (OP/Base)
- `data-rewards/` - Rewards data
- `data-voters/` - Voter analysis

## Todo

- [ ] Add token pricing via spot-price-aggregator oracle
- [ ] Add connector tokens for all chains

## Resources

- [Velodrome Finance](https://velodrome.finance)
- [Aerodrome Finance](https://aerodrome.finance)
- [Sugar Contracts](https://github.com/velodrome-finance/sugar)
