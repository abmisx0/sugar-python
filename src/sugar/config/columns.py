"""DataFrame column definitions for Sugar Python library."""

# LP (Liquidity Pool) columns from LpSugar.all()
COLUMNS_LP = (
    "lp",
    "symbol",
    "decimals",
    "liquidity",
    "type",
    "tick",
    "sqrt_ratio",
    "token0",
    "reserve0",
    "staked0",
    "token1",
    "reserve1",
    "staked1",
    "gauge",
    "gauge_liquidity",
    "gauge_alive",
    "fee",
    "bribe",
    "factory",
    "emissions",
    "emissions_token",
    "emissions_cap",
    "pool_fee",
    "unstaked_fee",
    "token0_fees",
    "token1_fees",
    "locked",
    "emerging",
    "created_at",
    "nfpm",
    "alm",
    "root",
)

# Columns that need wei conversion in LP data
COLUMNS_LP_CONVERT = (
    "reserve0",
    "staked0",
    "reserve1",
    "staked1",
    "emissions",
    "token0_fees",
    "token1_fees",
)

# Token columns from LpSugar.tokens()
COLUMNS_TOKEN = (
    "token_address",
    "symbol",
    "decimals",
    "account_balance",
    "listed",
    "emerging",
)

# Position columns from LpSugar.positions()
COLUMNS_POSITION = (
    "id",
    "lp",
    "liquidity",
    "staked",
    "amount0",
    "amount1",
    "staked0",
    "staked1",
    "unstaked_earned0",
    "unstaked_earned1",
    "emissions_earned",
    "tick_lower",
    "tick_upper",
    "sqrt_ratio_lower",
    "sqrt_ratio_upper",
    "locker",
    "unlocks_at",
    "alm",
)

# LP Epoch columns from RewardsSugar.epochsByAddress() / epochsLatest()
COLUMNS_LP_EPOCH = (
    "ts",
    "lp",
    "votes",
    "emissions",
    "incentives",  # voting incentives (formerly "bribes")
    "fees",
)

# Columns that need conversion in LP Epoch data
COLUMNS_LP_EPOCH_CONVERT = (
    "votes",
    "emissions",
    "incentives",
    "fees",
)

# Reward columns from RewardsSugar.rewards()
COLUMNS_REWARD = (
    "venft_id",
    "lp",
    "amount",
    "token",
    "fee",
    "bribe",
)

# veNFT columns from VeSugar.all()
COLUMNS_VENFT = (
    "id",
    "account",
    "decimals",
    "amount",  # locked balance
    "voting_amount",  # ve balance (accounts for voting decay)
    "governance_amount",  # is the only one that shows when in a relay
    "rebase_amount",
    "expires_at",
    "voted_at",
    "votes",
    "token",
    "permanent",
    "delegate_id",
    "managed_id",
)

# Columns that need wei conversion in veNFT data
COLUMNS_VENFT_ETH = (
    "amount",
    "voting_amount",
    "governance_amount",
    "rebase_amount",
    "votes",
)

# Default export columns for veNFT
COLUMNS_VENFT_EXPORT = (
    "account",
    "amount",
    "voting_amount",
    "governance_amount",
    "rebase_amount",
    "expires_at",
    "votes",
    "managed_id",
)

# Relay columns from RelaySugar.all()
COLUMNS_RELAY = (
    "venft_id",
    "decimals",
    "amount",  # locked balance being managed
    "voting_amount",  # ve balance being managed (accounts for voting decay)
    "used_voting_amount",
    "voted_at",
    "votes",
    "token",
    "compounded",
    "withdrawable",
    "run_at",
    "manager",  # manager address
    "relay",  # relay address
    "inactive",
    "name",
    "account_venfts",
)

# Columns that need wei conversion in Relay data
COLUMNS_RELAY_ETH = (
    "amount",
    "voting_amount",
    "used_voting_amount",
    "votes",
    "compounded",
)

# Default export columns for Relay
COLUMNS_RELAY_EXPORT = (
    "name",
    "inactive",
    "manager",
    "relay",
    "voting_amount",
    "used_voting_amount",
    "votes",
)

# Column rename mappings
COLUMN_RENAMES = {
    "votes": "votes (lp, weight)",
    "incentives": "incentives (token, amount)",
}
