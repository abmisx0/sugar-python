"""Quickstart: connect to a chain and read Sugar data.

Run:
    python examples/quickstart.py

Requires an RPC endpoint. Either set the chain's env var (e.g. RPC_LINK_BASE
in a .env file) or pass rpc_url= directly as shown below.
"""

from sugar import ChainId, SugarClient

# RPC via constructor injection (env var RPC_LINK_BASE is the fallback):
#   client = SugarClient(ChainId.BASE, rpc_url="https://base-mainnet.example/<key>")
client = SugarClient(ChainId.BASE)

print(f"Connected to {client.chain_name} @ block {client.block_number}")

# Pools with their current voting-incentive rewards, as a DataFrame.
pools = client.get_pools_with_rewards()
print(f"{len(pools)} pools")
print(pools.head())
