# Chain configurations for Sugar contracts
# Data sourced from: https://github.com/velodrome-finance/sugar/tree/main/deployments

CHAINS = {
    "op": {
        "name": "Optimism",
        "chain_id": 10,
        "rpc_env": "RPC_LINK_OP",
        "contracts": {
            "lp_sugar": "0x1d5E1893fCfb62CAaCE48eB2BAF7a6E134a8a27c",
            "rewards_sugar": "0x62CCFB2496f49A80B0184AD720379B529E9152fB",
            "ve_sugar": "0xFE0a44d356a9F52c9F1bE0ba0f0877d986438c9C",
            "relay_sugar": "0x5197Eb73253EF90E2089ad7308E572Ea6898c8D7",
            "voter": "0x41C914ee0c7E1A5edCD0295623e6dC557B5aBf3C",
            "ve_nft": "0xFAf8FD17D9840595845582fCB047DF13f006787d",
        },
        "has_ve": True,
        "has_relay": True,
    },
    "base": {
        "name": "Base",
        "chain_id": 8453,
        "rpc_env": "RPC_LINK_BASE",
        "contracts": {
            "lp_sugar": "0x9DE6Eab7a910A288dE83a04b6A43B52Fd1246f1E",
            "rewards_sugar": "0xD4aD2EeeB3314d54212A92f4cBBE684195dEfe3E",
            "ve_sugar": "0x4d6A741cEE6A8cC5632B2d948C050303F6246D24",
            "relay_sugar": "0x3dd0849D66DBd63D06f11442502e200601c50790",
            "voter": "0x16613524e02ad97eDfeF371bC883F2F5d6C480A5",
            "ve_nft": "0xeBf418Fe2512e7E6bd9b87a8F0f294aCDC67e6B4",
        },
        "has_ve": True,
        "has_relay": True,
    },
    "mode": {
        "name": "Mode",
        "chain_id": 34443,
        "rpc_env": "RPC_LINK_MODE",
        "contracts": {
            "lp_sugar": "0x280AC155a06e2aDB0718179C2f916BA90C32FEAB",
            "rewards_sugar": "0xD5d3ABAcB8CF075636792658EE0be8B03AF517B8",
            "voter": "0x97cDBCe21B6fd0585d29E539B1B99dAd328a1123",
        },
        "has_ve": False,
        "has_relay": False,
    },
    "lisk": {
        "name": "Lisk",
        "chain_id": 1135,
        "rpc_env": "RPC_LINK_LISK",
        "contracts": {
            "lp_sugar": "0x2002618dd63228670698200069E42f4422e82497",
            "rewards_sugar": "0xB1d0DFFe6260982164B53EdAcD3ccd58B081889d",
            "voter": "0x97cDBCe21B6fd0585d29E539B1B99dAd328a1123",
        },
        "has_ve": False,
        "has_relay": False,
    },
    "fraxtal": {
        "name": "Fraxtal",
        "chain_id": 252,
        "rpc_env": "RPC_LINK_FRAXTAL",
        "contracts": {
            "lp_sugar": "0xc703cDA5468bE663e4546C495E1D0E503082A8e0",
            "rewards_sugar": "0xbDD1d5A9d9566F575bC59cE33C8F77ACa5cF924b",
            "voter": "0x97cDBCe21B6fd0585d29E539B1B99dAd328a1123",
        },
        "has_ve": False,
        "has_relay": False,
    },
    "metal": {
        "name": "Metal L2",
        "chain_id": 1750,
        "rpc_env": "RPC_LINK_METAL",
        "contracts": {
            "lp_sugar": "0xB2CaA2742DD3b640e7f76EdfE74C84f725150014",
            "rewards_sugar": "0xbDD1d5A9d9566F575bC59cE33C8F77ACa5cF924b",
            "voter": "0x97cDBCe21B6fd0585d29E539B1B99dAd328a1123",
        },
        "has_ve": False,
        "has_relay": False,
    },
    "ink": {
        "name": "Ink",
        "chain_id": 57073,
        "rpc_env": "RPC_LINK_INK",
        "contracts": {
            "lp_sugar": "0x46e07c9b4016f8E5c3cD0b2fd20147A4d0972120",
            "rewards_sugar": "0xc100DC20aff9907E833a6aDEDDB52fC310554fF2",
            "voter": "0x97cDBCe21B6fd0585d29E539B1B99dAd328a1123",
        },
        "has_ve": False,
        "has_relay": False,
    },
    "soneium": {
        "name": "Soneium",
        "chain_id": 1868,
        "rpc_env": "RPC_LINK_SONEIUM",
        "contracts": {
            "lp_sugar": "0xf25D27572E122F78101FA5c37e94Cb2E880D8Edb",
            "rewards_sugar": "0xbDD1d5A9d9566F575bC59cE33C8F77ACa5cF924b",
            "voter": "0x97cDBCe21B6fd0585d29E539B1B99dAd328a1123",
        },
        "has_ve": False,
        "has_relay": False,
    },
    "superseed": {
        "name": "Superseed",
        "chain_id": 5330,
        "rpc_env": "RPC_LINK_SUPERSEED",
        "contracts": {
            "lp_sugar": "0x0Fb2AF1052D5f39540400E167EE5ACCb3cD2AF00",
            "rewards_sugar": "0xbDD1d5A9d9566F575bC59cE33C8F77ACa5cF924b",
            "voter": "0x97cDBCe21B6fd0585d29E539B1B99dAd328a1123",
        },
        "has_ve": False,
        "has_relay": False,
    },
    "swell": {
        "name": "Swell",
        "chain_id": 1923,
        "rpc_env": "RPC_LINK_SWELL",
        "contracts": {
            "lp_sugar": "0x215cEad02e0b9E0E494DD179585C18a772048a43",
            "rewards_sugar": "0xbDD1d5A9d9566F575bC59cE33C8F77ACa5cF924b",
            "voter": "0x97cDBCe21B6fd0585d29E539B1B99dAd328a1123",
        },
        "has_ve": False,
        "has_relay": False,
    },
    "unichain": {
        "name": "Unichain",
        "chain_id": 130,
        "rpc_env": "RPC_LINK_UNICHAIN",
        "contracts": {
            "lp_sugar": "0x46e07c9b4016f8E5c3cD0b2fd20147A4d0972120",
            "rewards_sugar": "0xbDD1d5A9d9566F575bC59cE33C8F77ACa5cF924b",
            "voter": "0x97cDBCe21B6fd0585d29E539B1B99dAd328a1123",
        },
        "has_ve": False,
        "has_relay": False,
    },
    "celo": {
        "name": "Celo",
        "chain_id": 42220,
        "rpc_env": "RPC_LINK_CELO",
        "contracts": {
            "lp_sugar": "0x9972174fcE4bdDFFff14bf2e18A287FDfE62c45E",
            "rewards_sugar": "0x2DCD9B33F0721000Dc1F8f84B804d4CFA23d7713",
            "voter": "0x97cDBCe21B6fd0585d29E539B1B99dAd328a1123",
        },
        "has_ve": False,
        "has_relay": False,
    },
}


def get_chain(chain_key: str) -> dict:
    """Get chain config by key (case-insensitive)."""
    key = chain_key.lower()
    if key not in CHAINS:
        available = ", ".join(CHAINS.keys())
        raise ValueError(f"Unknown chain '{chain_key}'. Available: {available}")
    return CHAINS[key]


def get_contract_address(chain_key: str, contract_type: str) -> str | None:
    """Get contract address for a chain. Returns None if not available."""
    chain = get_chain(chain_key)
    return chain["contracts"].get(contract_type)


def list_chains() -> list[str]:
    """List all supported chain keys."""
    return list(CHAINS.keys())


def chains_with_ve() -> list[str]:
    """List chains that have VeSugar deployed."""
    return [k for k, v in CHAINS.items() if v.get("has_ve")]


def chains_with_relay() -> list[str]:
    """List chains that have RelaySugar deployed."""
    return [k for k, v in CHAINS.items() if v.get("has_relay")]
