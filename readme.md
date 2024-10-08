# Sugar Library (WiP)

Very early build, needs a lot more work

## Todo List

- [ ] Add prices method to price tokens from `LpEpoch` structs
- [ ] Fetch sugar addresses from official repo's `env.example` file

## Setup

### pip installs

```bash
pip install pandas web3 python-dotenv dune-client geckoterminal-api
```

### Update `.env` file with your API keys

Use the existing `.env.example` file and fill in your keys
> **Note:** Delete `.example` from the file name

```bash
DUNE_API_KEY=<your Dune API key>
RPC_LINK_OP=<your OP RPC link>
RPC_LINK_BASE=<your Base RPC link>
RPC_LINK_MODE=https://mainnet.mode.network/
RPC_LINK_BOB=https://rpc.gobob.xyz/
```
