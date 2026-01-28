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
    "0x833589fcd6edb6e08f4c7c32d4f71b54bda02913",  # USDC
    "0xcbb7c0000ab88b473b1f5afd9ef808440eed33bf",  # cbBTC
    "0x60a3e35cc302bfa44cb288bc5a4f316fdb1adb42",  # EURC
    "0x2ae3f1ec7f1f5012cfeab0185bfc7aa3cf0dec22",  # cbETH
    "0xc1cba3fcea344f92d9239c08c0568f6f2f0ee452",  # wstETH
    "0x940181a94a35a4569e4529a3cdfb74e38fd98631",  # AERO
    "0xd9aaec86b65d86f6a7b5b1b0c42ffa531710b6ca",  # USDbC
    "0x4200000000000000000000000000000000000006",  # WETH
    "0xb79dd08ea68a908a97220c76d19a6aa9cbde4376",  # USD+
    "0xcfa3ef56d303ae4faaba0592388f19d7c3399fb4",  # eUSD
    "0x4621b7a9c75199271f773ebd9a499dbd165c3191",  # DOLA
    "0x50c5725949a6f0c72e6c4a641f24049a917db0cb",  # DAI
    "0xcb327b99ff831bf8223cced12b1338ff3aa322ff",  # bsdETH
)

CONNECTORS_OP = (
    "0x0b2c639c533813f4aa9d7837caf62653d097ff85",  # USDC
    "0x4200000000000000000000000000000000000006",  # WETH
    "0x94b008aa00579c1307b0ef2c499ad98a8ce58e58",  # USDT
    "0x6806411765af15bddd26f8f544a34cc40cb9838b",  # frxETH
    "0x4200000000000000000000000000000000000042",  # OP
    "0x2e3d870790dc77a83dd1d18184acc7439a53f475",  # FRAX
    "0x9560e827af36c94d2ac33a39bce1fe78631088db",  # VELO
    "0xc3864f98f2a61a7caeb95b039d031b4e2f55e0e9",  # OpenX
    "0xc5b001dc33727f8f26880b184090d3e252470d45",  # ERN
    "0x73cb180bf0521828d8849bc8cf2b920918e23032",  # USD+
    "0xda10009cbd5d07dd0cecc66161fc93d7c9000da1",  # DAI
    "0x6c84a8f1c29108f47a79964b5fe888d4f4d0de40",  # tBTC
    "0x1f32b1c2345538c0c6f582fcb022739c4a194ebb",  # wstETH
    "0xbfd291da8a403daaf7e5e9dc1ec0aceacd4848b9",  # USX
    "0x8c6f28f2f1a3c87f0f938b96d27520d9751ec8d9",  # sUSD
    "0x9bcef72be871e61ed4fbbc7630889bee758eb81d",  # rETH (Rocket Pool)
    "0xc40f949f8a4e094d1b49a23ea9241d289b7b2819",  # LUSD
    "0x9485aca5bbbe1667ad97c7fe7c4531a624c8b1ed",  # EURA
)

CONNECTORS_CELO = (
    "0x48065fbbe25f71c9282ddf5e1cd6d6a887483d5e",  # USDT
    "0xd221812de1bd094f35587ee8e174b07b6167d9af",  # WETH
    "0x471ece3750da237f93b8e339c536989b8978a438",  # CELO
)

CONNECTORS_INK = (
    "0x0200c29006150606b650577bbe7b6248f58470c1",  # USDT0
    "0x4200000000000000000000000000000000000006",  # WETH
    "0x73e0c0d45e048d25fc26fa3159b0aa04bfa4db98",  # kBTC
)

CONNECTORS_SONEIUM = (
    "0xba9986d2381edf1da03b0b9c1f8b00dc4aacc369",  # USDC.e
    "0x4200000000000000000000000000000000000006",  # WETH
    "0x2cae934a1e84f693fbb78ca5ed3b0a6893259441",  # ASTR
)

CONNECTORS_UNICHAIN = (
    "0x078d782b760474a361dda0af3839290b0ef57ad6",  # USDC
    "0x4200000000000000000000000000000000000006",  # WETH
)

CONNECTORS_LISK = (
    "0x43f2376d5d03553ae72f4a8093bbe9de4336eb08",  # USDT0
    "0x4200000000000000000000000000000000000006",  # WETH
    "0x03c7054bcb39f7b2e5b2c7acb37583e32d70cfa3",  # WBTC
    "0xac485391eb2d7d88253a7f1ef18c37f4242d1a24",  # LSK
)

CONNECTORS_SUPERSEED = (
    "0x1217bfe6c773eec6cc4a38b5dc45b92292b6e189",  # oUSDT
    "0x4200000000000000000000000000000000000006",  # WETH
    "0x6f36dbd829de9b7e077db8a35b480d4329ceb331",  # cbBTC
)

CONNECTORS_MODE = (
    "0x1217bfe6c773eec6cc4a38b5dc45b92292b6e189",  # oUSDT
    "0x4200000000000000000000000000000000000006",  # WETH
    "0xdfc7c877a950e49d2610114102175a06c2e3167a",  # MODE
)

CONNECTORS_METAL = (
    "0x51e85d70944256710cb141847f1a04f568c1db0e",  # USDC.e
    "0x4200000000000000000000000000000000000006",  # WETH
    "0x7f9adfbd38b669f03d1d11000bc76b9aaea28a81",  # VELO
    "0xbcfc435d8f276585f6431fc1b9ee9a850b5c00a9",  # MTL
)

CONNECTORS_SWELL = (
    "0x5d3a1ff2b6bab83b63cd9ad0787074081a52ef34",  # USDe
    "0x4200000000000000000000000000000000000006",  # WETH
    "0x2826d136f5630ada89c1678b64a61620aab77aea",  # SWELL
)

CONNECTORS_FRAXTAL = (
    "0xfc00000000000000000000000000000000000001",  # frxUSD
    "0xdcc0f2d8f90fde85b10ac1c8ab57dc0ae946a543",  # USDC
    "0xfc00000000000000000000000000000000000006",  # frxETH
    "0x5d3a1ff2b6bab83b63cd9ad0787074081a52ef34",  # USDe
    "0x211cc4dd073734da055fbf44a2b4667d5e5fe5d2",  # sUSDe
    "0xfc00000000000000000000000000000000000005",  # sfrxETH
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
        connectors=CONNECTORS_LISK,
    ),
    ChainId.FRAXTAL: ChainConfig(
        chain_id=ChainId.FRAXTAL,
        name="Fraxtal",
        rpc_env_var="RPC_LINK_FRAXTAL",
        lp_sugar_address="0xc703cDA5468bE663e4546C495E1D0E503082A8e0",
        rewards_sugar_address="0xbDD1d5A9d9566F575bC59cE33C8F77ACa5cF924b",
        price_oracle_address="0x59114D308C6DE4A84F5F8cD80485a5481047b99f",
        connectors=CONNECTORS_FRAXTAL,
    ),
    ChainId.INK: ChainConfig(
        chain_id=ChainId.INK,
        name="Ink",
        rpc_env_var="RPC_LINK_INK",
        lp_sugar_address="0x46e07c9b4016f8E5c3cD0b2fd20147A4d0972120",
        rewards_sugar_address="0xc100DC20aff9907E833a6aDEDDB52fC310554fF2",
        price_oracle_address="0x59114D308C6DE4A84F5F8cD80485a5481047b99f",
        connectors=CONNECTORS_INK,
    ),
    ChainId.SONEIUM: ChainConfig(
        chain_id=ChainId.SONEIUM,
        name="Soneium",
        rpc_env_var="RPC_LINK_SONEIUM",
        lp_sugar_address="0xf25D27572E122F78101FA5c37e94Cb2E880D8Edb",
        rewards_sugar_address="0xbDD1d5A9d9566F575bC59cE33C8F77ACa5cF924b",
        price_oracle_address="0x59114D308C6DE4A84F5F8cD80485a5481047b99f",
        connectors=CONNECTORS_SONEIUM,
    ),
    ChainId.METAL: ChainConfig(
        chain_id=ChainId.METAL,
        name="Metal L2",
        rpc_env_var="RPC_LINK_METAL",
        lp_sugar_address="0xB2CaA2742DD3b640e7f76EdfE74C84f725150014",
        rewards_sugar_address="0xbDD1d5A9d9566F575bC59cE33C8F77ACa5cF924b",
        price_oracle_address="0x59114D308C6DE4A84F5F8cD80485a5481047b99f",
        connectors=CONNECTORS_METAL,
    ),
    ChainId.CELO: ChainConfig(
        chain_id=ChainId.CELO,
        name="Celo",
        rpc_env_var="RPC_LINK_CELO",
        lp_sugar_address="0x9972174fcE4bdDFFff14bf2e18A287FDfE62c45E",
        rewards_sugar_address="0x2DCD9B33F0721000Dc1F8f84B804d4CFA23d7713",
        price_oracle_address="0xbf6d753FC4a10Ec5191c56BB3DC1e414b7572327",
        connectors=CONNECTORS_CELO,
    ),
    ChainId.SUPERSEED: ChainConfig(
        chain_id=ChainId.SUPERSEED,
        name="Superseed",
        rpc_env_var="RPC_LINK_SUPERSEED",
        lp_sugar_address="0x0Fb2AF1052D5f39540400E167EE5ACCb3cD2AF00",
        rewards_sugar_address="0xbDD1d5A9d9566F575bC59cE33C8F77ACa5cF924b",
        price_oracle_address="0x59114D308C6DE4A84F5F8cD80485a5481047b99f",
        connectors=CONNECTORS_SUPERSEED,
    ),
    ChainId.SWELL: ChainConfig(
        chain_id=ChainId.SWELL,
        name="Swell",
        rpc_env_var="RPC_LINK_SWELL",
        lp_sugar_address="0x215cEad02e0b9E0E494DD179585C18a772048a43",
        rewards_sugar_address="0xbDD1d5A9d9566F575bC59cE33C8F77ACa5cF924b",
        price_oracle_address="0x59114D308C6DE4A84F5F8cD80485a5481047b99f",
        connectors=CONNECTORS_SWELL,
    ),
    ChainId.UNICHAIN: ChainConfig(
        chain_id=ChainId.UNICHAIN,
        name="Unichain",
        rpc_env_var="RPC_LINK_UNICHAIN",
        lp_sugar_address="0x46e07c9b4016f8E5c3cD0b2fd20147A4d0972120",
        rewards_sugar_address="0xbDD1d5A9d9566F575bC59cE33C8F77ACa5cF924b",
        price_oracle_address="0x59114D308C6DE4A84F5F8cD80485a5481047b99f",
        connectors=CONNECTORS_UNICHAIN,
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
