"""Service for fetching deployment addresses and ABIs from external sources."""

from __future__ import annotations

import json
import logging
import os
import re
from pathlib import Path
from typing import Any

import requests

logger = logging.getLogger(__name__)

# GitHub raw content URLs
SUGAR_REPO_BASE = "https://raw.githubusercontent.com/velodrome-finance/sugar/main"
DEPLOYMENTS_BASE = f"{SUGAR_REPO_BASE}/deployments"

# Chain name to file mapping
CHAIN_ENV_FILES = {
    "base": "base.env",
    "optimism": "optimism.env",
    "mode": "mode.env",
    "lisk": "lisk.env",
    "fraxtal": "fraxtal.env",
    "ink": "ink.env",
    "soneium": "soneium.env",
    "metal": "metall2.env",
    "celo": "celo.env",
    "superseed": "superseed.env",
    "swell": "swell.env",
    "unichain": "unichain.env",
}

# Chain ID to name mapping
CHAIN_ID_TO_NAME = {
    8453: "base",
    10: "optimism",
    34443: "mode",
    1135: "lisk",
    252: "fraxtal",
    57073: "ink",
    1868: "soneium",
    1750: "metal",
    42220: "celo",
    5330: "superseed",
    1923: "swell",
    130: "unichain",
}

# Blockscout API URLs by chain
BLOCKSCOUT_APIS = {
    8453: "https://base.blockscout.com/api",  # Base
    10: "https://optimism.blockscout.com/api",  # Optimism
    34443: "https://explorer.mode.network/api",  # Mode
    1135: "https://blockscout.lisk.com/api",  # Lisk
    252: "https://fraxscan.com/api",  # Fraxtal
    57073: "https://explorer.inkonchain.com/api",  # Ink
    1868: "https://soneium.blockscout.com/api",  # Soneium
    1750: "https://explorer.metall2.com/api",  # Metal
    42220: "https://explorer.celo.org/mainnet/api",  # Celo
    5330: "https://explorer.superseed.xyz/api",  # Superseed
    1923: "https://explorer.swellnetwork.io/api",  # Swell
    130: "https://unichain.blockscout.com/api",  # Unichain
}

# Etherscan API URLs by chain
ETHERSCAN_APIS = {
    8453: "https://api.basescan.org/api",
    10: "https://api-optimistic.etherscan.io/api",
    252: "https://api.fraxscan.com/api",
    42220: "https://api.celoscan.io/api",
}


def fetch_chain_deployment(chain_name: str) -> str:
    """
    Fetch the deployment env file for a specific chain from the sugar repository.

    Args:
        chain_name: Chain name (e.g., "base", "optimism").

    Returns:
        Content of the chain's .env file.

    Raises:
        ValueError: If chain name is not recognized.
        requests.HTTPError: If the request fails.
    """
    chain_name = chain_name.lower()
    if chain_name not in CHAIN_ENV_FILES:
        raise ValueError(f"Unknown chain: {chain_name}. Available: {list(CHAIN_ENV_FILES.keys())}")

    env_file = CHAIN_ENV_FILES[chain_name]
    url = f"{DEPLOYMENTS_BASE}/{env_file}"

    response = requests.get(url, timeout=10)
    response.raise_for_status()
    return response.text


def parse_chain_deployment(env_content: str) -> dict[str, str]:
    """
    Parse contract addresses from a chain's deployment env content.

    The env file format includes chain ID suffix:
        CHAIN_ID=8453
        LP_SUGAR_ADDRESS_8453=0x...
        VE_SUGAR_ADDRESS_8453=0x...
        etc.

    Args:
        env_content: Content of the chain's .env file.

    Returns:
        Dictionary of contract_type -> address (without chain ID suffix).
    """
    addresses: dict[str, str] = {}
    chain_id: str | None = None

    # First pass: get chain ID
    for line in env_content.split("\n"):
        line = line.strip()
        if line.startswith("CHAIN_ID="):
            chain_id = line.split("=", 1)[1].strip()
            break

    if not chain_id:
        logger.warning("No CHAIN_ID found in deployment file")
        chain_id = ""

    addresses["chain_id"] = chain_id

    # Contract type patterns (key prefix -> normalized name)
    # These match the format: KEY_CHAINID=address
    sugar_contracts = {
        "LP_SUGAR_ADDRESS": "lp_sugar",
        "VE_SUGAR_ADDRESS": "ve_sugar",
        "RELAY_SUGAR_ADDRESS": "relay_sugar",
        "REWARDS_SUGAR_ADDRESS": "rewards_sugar",
        "TOKEN_SUGAR": "token_sugar",
        "LP_HELPER": "lp_helper",
    }

    infrastructure_contracts = {
        "VOTER": "voter",
        "REGISTRY": "registry",
        "CONVERTOR": "convertor",
        "SLIPSTREAM_HELPER": "slipstream_helper",
        "ALM_FACTORY": "alm_factory",
        "DIST": "distribution",
        "GOVERNOR": "governor",
        "SWAPPER": "swapper",
        "V2_LAUNCHER": "v2_launcher",
        "CL_LAUNCHER": "cl_launcher",
        "RELAY_REGISTRY_ADDRESSES": "relay_registries",
    }

    all_mappings = {**sugar_contracts, **infrastructure_contracts}

    for line in env_content.split("\n"):
        line = line.strip()
        if not line or line.startswith("#"):
            continue

        if "=" not in line:
            continue

        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip("'\"")

        # Strip chain ID suffix if present
        key_base = key
        if chain_id and key.endswith(f"_{chain_id}"):
            key_base = key[: -(len(chain_id) + 1)]

        # Map known contract types
        if key_base in all_mappings:
            addresses[all_mappings[key_base]] = value

    return addresses


def fetch_all_deployments() -> dict[str, dict[str, str]]:
    """
    Fetch deployment addresses for all supported chains.

    Returns:
        Dictionary of chain_name -> contract_type -> address.
    """
    all_deployments: dict[str, dict[str, str]] = {}

    for chain_name in CHAIN_ENV_FILES:
        try:
            env_content = fetch_chain_deployment(chain_name)
            addresses = parse_chain_deployment(env_content)
            all_deployments[chain_name] = addresses
            logger.info(f"Fetched deployment addresses for {chain_name}")
        except Exception as e:
            logger.warning(f"Failed to fetch deployment for {chain_name}: {e}")

    return all_deployments


def get_sugar_addresses(chain_id: int) -> dict[str, str | None]:
    """
    Get Sugar contract addresses for a chain in a convenient format.

    Args:
        chain_id: Chain ID (e.g., 8453 for Base).

    Returns:
        Dictionary with keys: lp_sugar, ve_sugar, relay_sugar, rewards_sugar.
        Values are addresses or None if not available.

    Raises:
        ValueError: If chain ID is not supported.
    """
    chain_name = CHAIN_ID_TO_NAME.get(chain_id)
    if not chain_name:
        raise ValueError(f"Unknown chain ID: {chain_id}. Supported: {list(CHAIN_ID_TO_NAME.values())}")

    env_content = fetch_chain_deployment(chain_name)
    addresses = parse_chain_deployment(env_content)

    return {
        "lp_sugar": addresses.get("lp_sugar"),
        "ve_sugar": addresses.get("ve_sugar"),
        "relay_sugar": addresses.get("relay_sugar"),
        "rewards_sugar": addresses.get("rewards_sugar"),
    }


def fetch_abi_from_blockscout(
    chain_id: int,
    address: str,
) -> list[dict[str, Any]] | None:
    """
    Fetch contract ABI from Blockscout API.

    Args:
        chain_id: Chain ID.
        address: Contract address.

    Returns:
        Contract ABI as list of dicts, or None if not found.
    """
    if chain_id not in BLOCKSCOUT_APIS:
        logger.warning(f"No Blockscout API configured for chain {chain_id}")
        return None

    api_url = BLOCKSCOUT_APIS[chain_id]

    try:
        response = requests.get(
            api_url,
            params={
                "module": "contract",
                "action": "getabi",
                "address": address,
            },
            timeout=10,
        )
        response.raise_for_status()
        data = response.json()

        if data.get("status") == "1" and data.get("result"):
            return json.loads(data["result"])
        else:
            logger.warning(f"Failed to fetch ABI from Blockscout: {data.get('message')}")
            return None

    except Exception as e:
        logger.warning(f"Error fetching ABI from Blockscout: {e}")
        return None


def fetch_abi_from_etherscan(
    chain_id: int,
    address: str,
    api_key: str | None = None,
) -> list[dict[str, Any]] | None:
    """
    Fetch contract ABI from Etherscan API.

    Args:
        chain_id: Chain ID.
        address: Contract address.
        api_key: Etherscan API key (optional but recommended).

    Returns:
        Contract ABI as list of dicts, or None if not found.
    """
    if chain_id not in ETHERSCAN_APIS:
        logger.warning(f"No Etherscan API configured for chain {chain_id}")
        return None

    api_url = ETHERSCAN_APIS[chain_id]
    api_key = api_key or os.getenv("ETHERSCAN_API_KEY", "")

    try:
        response = requests.get(
            api_url,
            params={
                "module": "contract",
                "action": "getabi",
                "address": address,
                "apikey": api_key,
            },
            timeout=10,
        )
        response.raise_for_status()
        data = response.json()

        if data.get("status") == "1" and data.get("result"):
            return json.loads(data["result"])
        else:
            logger.warning(f"Failed to fetch ABI from Etherscan: {data.get('message')}")
            return None

    except Exception as e:
        logger.warning(f"Error fetching ABI from Etherscan: {e}")
        return None


def fetch_abi(
    chain_id: int,
    address: str,
    api_key: str | None = None,
) -> list[dict[str, Any]] | None:
    """
    Fetch contract ABI, trying Blockscout first then Etherscan.

    Args:
        chain_id: Chain ID.
        address: Contract address.
        api_key: Etherscan API key (optional).

    Returns:
        Contract ABI as list of dicts, or None if not found.
    """
    # Try Blockscout first (no API key needed)
    abi = fetch_abi_from_blockscout(chain_id, address)
    if abi:
        return abi

    # Fall back to Etherscan
    abi = fetch_abi_from_etherscan(chain_id, address, api_key)
    if abi:
        return abi

    return None


def save_abi(abi: list[dict[str, Any]], filename: str, abi_dir: Path | None = None) -> Path:
    """
    Save ABI to a JSON file.

    Args:
        abi: Contract ABI.
        filename: Filename (without path).
        abi_dir: Directory to save to (default: config/abis/).

    Returns:
        Path to saved file.
    """
    if abi_dir is None:
        abi_dir = Path(__file__).parent.parent / "config" / "abis"

    abi_dir.mkdir(parents=True, exist_ok=True)
    filepath = abi_dir / filename

    with open(filepath, "w") as f:
        json.dump(abi, f, indent=2)

    return filepath


class DeploymentFetcher:
    """
    Fetches and caches deployment addresses and ABIs.
    """

    def __init__(self) -> None:
        """Initialize the deployment fetcher."""
        self._addresses: dict[str, dict[str, str]] | None = None
        self._abis: dict[str, list[dict[str, Any]]] = {}

    def get_addresses(self, refresh: bool = False) -> dict[str, dict[str, str]]:
        """
        Get all deployment addresses from the sugar repo.

        Args:
            refresh: Whether to refresh cached addresses.

        Returns:
            Dictionary of chain -> contract_type -> address.
        """
        if self._addresses is None or refresh:
            env_content = fetch_env_example()
            self._addresses = parse_env_addresses(env_content)

        return self._addresses

    def get_abi(
        self,
        chain_id: int,
        address: str,
        contract_type: str,
        refresh: bool = False,
    ) -> list[dict[str, Any]] | None:
        """
        Get contract ABI, caching the result.

        Args:
            chain_id: Chain ID.
            address: Contract address.
            contract_type: Contract type (for caching key).
            refresh: Whether to refresh cached ABI.

        Returns:
            Contract ABI or None if not found.
        """
        cache_key = f"{chain_id}_{contract_type}"

        if cache_key not in self._abis or refresh:
            abi = fetch_abi(chain_id, address)
            if abi:
                self._abis[cache_key] = abi

        return self._abis.get(cache_key)


# Singleton instance
_deployment_fetcher: DeploymentFetcher | None = None


def get_deployment_fetcher() -> DeploymentFetcher:
    """Get the singleton deployment fetcher instance."""
    global _deployment_fetcher
    if _deployment_fetcher is None:
        _deployment_fetcher = DeploymentFetcher()
    return _deployment_fetcher
