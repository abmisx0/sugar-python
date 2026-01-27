"""Chain configuration for Sugar Python library."""

from dataclasses import dataclass
from enum import Enum


class ChainId(Enum):
    """Supported chain identifiers."""

    OPTIMISM = 10
    BASE = 8453
    MODE = 34443
    LISK = 1135
    FRAXTAL = 252
    INK = 57073
    SONEIUM = 1868
    METAL = 1750
    CELO = 42220
    SUPERSEED = 5330
    SWELL = 1923
    UNICHAIN = 130


@dataclass(frozen=True)
class ChainConfig:
    """Immutable chain configuration."""

    chain_id: ChainId
    name: str
    rpc_env_var: str

    # Contract addresses (None if not deployed)
    lp_sugar_address: str
    rewards_sugar_address: str | None = None
    ve_sugar_address: str | None = None
    relay_sugar_address: str | None = None
    price_oracle_address: str | None = None

    # Token connectors for price queries
    connectors: tuple[str, ...] = ()

    @property
    def has_ve(self) -> bool:
        """Check if VeSugar is available on this chain."""
        return self.ve_sugar_address is not None

    @property
    def has_relay(self) -> bool:
        """Check if RelaySugar is available on this chain."""
        return self.relay_sugar_address is not None

    @property
    def has_rewards(self) -> bool:
        """Check if RewardsSugar is available on this chain."""
        return self.rewards_sugar_address is not None

    @property
    def has_price_oracle(self) -> bool:
        """Check if Spot Price Oracle is available on this chain."""
        return self.price_oracle_address is not None


# Connector tokens for price queries by chain
CONNECTORS_BASE = (
    "0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913",  # USDC
    "0x940181a94A35A4569E4529A3CDfB74e38FD98631",  # AERO
    "0x50c5725949A6F0c72E6C4a641F24049A917DB0Cb",  # DAI
    "0x4621b7A9c75199271F773Ebd9A499dbd165c3191",  # DOLA
    "0x4200000000000000000000000000000000000006",  # WETH
    "0xB79DD08EA68A908A97220C76d19A6aA9cBDE4376",  # USD+
    "0xf7A0dd3317535eC4f4d29ADF9d620B3d8D5D5069",  # stERN
    "0xCfA3Ef56d303AE4fAabA0592388F19d7C3399FB4",  # eUSD
    "0xCb327b99fF831bF8223cCEd12B1338FF3aA322Ff",  # bsdETH
    "0x2Ae3F1Ec7F1F5012CFEab0185bfc7aa3cf0DEc22",  # cbETH
    "0xc1CBa3fCea344f92D9239c08C0568f6F2F0ee452",  # wstETH
    "0x60a3E35Cc302bFA44Cb288Bc5a4F316Fdb1adb42",  # EURC
    "0xd9aAEc86B65D86f6A7B5B1b0c42FFA531710b6CA",  # USDbC
    "0xcbB7C0000aB88B473b1f5aFd9ef808440eed33Bf",  # cbBTC
)

CONNECTORS_OP = (
    "0x9560e827aF36c94D2Ac33a39bCE1Fe78631088Db",  # VELO
    "0x4200000000000000000000000000000000000042",  # OP
    "0x4200000000000000000000000000000000000006",  # WETH
    "0x9Bcef72be871e61ED4fBbc7630889beE758eb81D",  # rETH (Rocket Pool)
    "0x2E3D870790dC77A83DD1d18184Acc7439A53f475",  # FRAX
    "0x8c6f28f2F1A3C87F0f938b96d27520d9751ec8d9",  # sUSD
    "0x1F32b1c2345538c0c6f582fCB022739c4A194Ebb",  # wstETH
    "0xbfD291DA8A403DAAF7e5E9DC1ec0aCEaCd4848B9",  # USX
    "0xc3864f98f2a61A7cAeb95b039D031b4E2f55e0e9",  # OpenX
    "0x9485aca5bbBE1667AD97c7fE7C4531a624C8b1ED",  # agEUR
    "0xDA10009cBd5D07dd0CeCc66161FC93D7c9000da1",  # DAI
    "0x73cb180bf0521828d8849bc8CF2B920918e23032",  # USD+
    "0x6806411765Af15Bddd26f8f544A34cC40cb9838B",  # frxETH
    "0x6c2f7b6110a37b3B0fbdd811876be368df02E8B0",  # rETH (Star)
    "0xc5b001DC33727F8F26880B184090D3E252470D45",  # ERN
    "0x6c84a8f1c29108F47a79964b5Fe888D4f4D0dE40",  # tBTC
    "0xc40F949F8a4e094D1b49a23ea9241D289B7b2819",  # LUSD
    "0x94b008aA00579c1307B0EF2c499aD98a8ce58e58",  # USDT
    "0x0b2C639c533813f4Aa9D7837CAf62653d097Ff85",  # USDC
)

CONNECTORS_MODE = (
    "0x4200000000000000000000000000000000000006",  # WETH
    "0xDfc7C877a950e49D2610114102175A06C2e3167a",  # MODE
    "0xf0F161fDA2712DB8b566946122a5af183995e2eD",  # USDT
    "0xE7798f023fC62146e8Aa1b36Da45fb70855a77Ea",  # DAI
)

# Chain configurations
CHAIN_CONFIGS: dict[ChainId, ChainConfig] = {
    ChainId.OPTIMISM: ChainConfig(
        chain_id=ChainId.OPTIMISM,
        name="Optimism",
        rpc_env_var="RPC_LINK_OP",
        lp_sugar_address="0x1d5E1893fCfb62CAaCE48eB2BAF7a6E134a8a27c",
        rewards_sugar_address="0x62CCFB2496f49A80B0184AD720379B529E9152fB",
        ve_sugar_address="0xFE0a44d356a9F52c9F1bE0ba0f0877d986438c9C",
        relay_sugar_address="0x5197Eb73253EF90E2089ad7308E572Ea6898c8D7",
        price_oracle_address="0x59114D308C6DE4A84F5F8cD80485a5481047b99f",
        connectors=CONNECTORS_OP,
    ),
    ChainId.BASE: ChainConfig(
        chain_id=ChainId.BASE,
        name="Base",
        rpc_env_var="RPC_LINK_BASE",
        lp_sugar_address="0x9DE6Eab7a910A288dE83a04b6A43B52Fd1246f1E",
        rewards_sugar_address="0xD4aD2EeeB3314d54212A92f4cBBE684195dEfe3E",
        ve_sugar_address="0x4d6A741cEE6A8cC5632B2d948C050303F6246D24",
        relay_sugar_address="0x3dd0849D66DBd63D06f11442502e200601c50790",
        price_oracle_address="0x8456038bdae8672f552182B0FC39b1917dE9a41A",
        connectors=CONNECTORS_BASE,
    ),
    ChainId.MODE: ChainConfig(
        chain_id=ChainId.MODE,
        name="Mode",
        rpc_env_var="RPC_LINK_MODE",
        lp_sugar_address="0x280AC155a06e2aDB0718179C2f916BA90C32FEAB",
        rewards_sugar_address="0xD5d3ABAcB8CF075636792658EE0be8B03AF517B8",
        price_oracle_address="0xbAEe949B52cb503e39f1Df54Dcee778da59E11bc",
        connectors=CONNECTORS_MODE,
    ),
    ChainId.LISK: ChainConfig(
        chain_id=ChainId.LISK,
        name="Lisk",
        rpc_env_var="RPC_LINK_LISK",
        lp_sugar_address="0x2002618dd63228670698200069E42f4422e82497",
        rewards_sugar_address="0xB1d0DFFe6260982164B53EdAcD3ccd58B081889d",
        price_oracle_address="0x59114D308C6DE4A84F5F8cD80485a5481047b99f",
    ),
    ChainId.FRAXTAL: ChainConfig(
        chain_id=ChainId.FRAXTAL,
        name="Fraxtal",
        rpc_env_var="RPC_LINK_FRAXTAL",
        lp_sugar_address="0xc703cDA5468bE663e4546C495E1D0E503082A8e0",
        rewards_sugar_address="0xbDD1d5A9d9566F575bC59cE33C8F77ACa5cF924b",
        price_oracle_address="0x59114D308C6DE4A84F5F8cD80485a5481047b99f",
    ),
    ChainId.INK: ChainConfig(
        chain_id=ChainId.INK,
        name="Ink",
        rpc_env_var="RPC_LINK_INK",
        lp_sugar_address="0x46e07c9b4016f8E5c3cD0b2fd20147A4d0972120",
        rewards_sugar_address="0xc100DC20aff9907E833a6aDEDDB52fC310554fF2",
        price_oracle_address="0x59114D308C6DE4A84F5F8cD80485a5481047b99f",
    ),
    ChainId.SONEIUM: ChainConfig(
        chain_id=ChainId.SONEIUM,
        name="Soneium",
        rpc_env_var="RPC_LINK_SONEIUM",
        lp_sugar_address="0xf25D27572E122F78101FA5c37e94Cb2E880D8Edb",
        rewards_sugar_address="0xbDD1d5A9d9566F575bC59cE33C8F77ACa5cF924b",
        price_oracle_address="0x59114D308C6DE4A84F5F8cD80485a5481047b99f",
    ),
    ChainId.METAL: ChainConfig(
        chain_id=ChainId.METAL,
        name="Metal L2",
        rpc_env_var="RPC_LINK_METAL",
        lp_sugar_address="0xB2CaA2742DD3b640e7f76EdfE74C84f725150014",
        rewards_sugar_address="0xbDD1d5A9d9566F575bC59cE33C8F77ACa5cF924b",
        price_oracle_address="0x59114D308C6DE4A84F5F8cD80485a5481047b99f",
    ),
    ChainId.CELO: ChainConfig(
        chain_id=ChainId.CELO,
        name="Celo",
        rpc_env_var="RPC_LINK_CELO",
        lp_sugar_address="0x9972174fcE4bdDFFff14bf2e18A287FDfE62c45E",
        rewards_sugar_address="0x2DCD9B33F0721000Dc1F8f84B804d4CFA23d7713",
        price_oracle_address="0xbf6d753FC4a10Ec5191c56BB3DC1e414b7572327",
    ),
    ChainId.SUPERSEED: ChainConfig(
        chain_id=ChainId.SUPERSEED,
        name="Superseed",
        rpc_env_var="RPC_LINK_SUPERSEED",
        lp_sugar_address="0x0Fb2AF1052D5f39540400E167EE5ACCb3cD2AF00",
        rewards_sugar_address="0xbDD1d5A9d9566F575bC59cE33C8F77ACa5cF924b",
        price_oracle_address="0x59114D308C6DE4A84F5F8cD80485a5481047b99f",
    ),
    ChainId.SWELL: ChainConfig(
        chain_id=ChainId.SWELL,
        name="Swell",
        rpc_env_var="RPC_LINK_SWELL",
        lp_sugar_address="0x215cEad02e0b9E0E494DD179585C18a772048a43",
        rewards_sugar_address="0xbDD1d5A9d9566F575bC59cE33C8F77ACa5cF924b",
        price_oracle_address="0x59114D308C6DE4A84F5F8cD80485a5481047b99f",
    ),
    ChainId.UNICHAIN: ChainConfig(
        chain_id=ChainId.UNICHAIN,
        name="Unichain",
        rpc_env_var="RPC_LINK_UNICHAIN",
        lp_sugar_address="0x46e07c9b4016f8E5c3cD0b2fd20147A4d0972120",
        rewards_sugar_address="0xbDD1d5A9d9566F575bC59cE33C8F77ACa5cF924b",
        price_oracle_address="0x59114D308C6DE4A84F5F8cD80485a5481047b99f",
    ),
}


def get_chain_config(chain: ChainId | str) -> ChainConfig:
    """
    Get chain configuration by ChainId or name.

    Args:
        chain: ChainId enum or chain name string (e.g., "base", "optimism").

    Returns:
        ChainConfig for the specified chain.

    Raises:
        ValueError: If chain is not found.
    """
    if isinstance(chain, ChainId):
        return CHAIN_CONFIGS[chain]

    chain_upper = chain.upper()

    # Handle common aliases
    aliases = {
        "OP": ChainId.OPTIMISM,
        "OPTIMISM": ChainId.OPTIMISM,
        "BASE": ChainId.BASE,
        "MODE": ChainId.MODE,
        "LISK": ChainId.LISK,
        "FRAXTAL": ChainId.FRAXTAL,
        "INK": ChainId.INK,
        "SONEIUM": ChainId.SONEIUM,
        "METAL": ChainId.METAL,
        "METALL2": ChainId.METAL,
        "CELO": ChainId.CELO,
        "SUPERSEED": ChainId.SUPERSEED,
        "SWELL": ChainId.SWELL,
        "UNICHAIN": ChainId.UNICHAIN,
    }

    if chain_upper in aliases:
        return CHAIN_CONFIGS[aliases[chain_upper]]

    raise ValueError(f"Unknown chain: {chain}. Supported: {list(aliases.keys())}")
