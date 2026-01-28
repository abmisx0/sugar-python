"""Tests for chain configuration."""

import pytest

from sugar.config.chains import (
    CHAIN_CONFIGS,
    ChainConfig,
    ChainId,
    get_chain_config,
)
from sugar.core.exceptions import ChainNotSupportedError


class TestChainId:
    """Test ChainId enum."""

    def test_all_chains_defined(self) -> None:
        """All expected chains should be defined."""
        expected_chains = [
            "OPTIMISM",
            "BASE",
            "MODE",
            "LISK",
            "FRAXTAL",
            "INK",
            "SONEIUM",
            "METAL",
            "CELO",
            "SUPERSEED",
            "SWELL",
            "UNICHAIN",
        ]
        for chain in expected_chains:
            assert hasattr(ChainId, chain)

    def test_chain_ids_are_integers(self) -> None:
        """Chain IDs should be integers."""
        for chain in ChainId:
            assert isinstance(chain.value, int)

    def test_known_chain_ids(self) -> None:
        """Verify known chain IDs."""
        assert ChainId.OPTIMISM.value == 10
        assert ChainId.BASE.value == 8453
        assert ChainId.MODE.value == 34443


class TestChainConfig:
    """Test ChainConfig dataclass."""

    def test_all_chains_have_config(self) -> None:
        """Every ChainId should have a corresponding config."""
        for chain_id in ChainId:
            assert chain_id in CHAIN_CONFIGS

    def test_config_has_required_fields(self) -> None:
        """Each config should have required fields."""
        for chain_id, config in CHAIN_CONFIGS.items():
            assert isinstance(config, ChainConfig)
            assert config.chain_id == chain_id
            assert config.name
            assert config.rpc_env_var
            assert config.lp_sugar_address
            assert config.rewards_sugar_address

    def test_base_config(self) -> None:
        """Base chain should have full contract support."""
        config = CHAIN_CONFIGS[ChainId.BASE]
        assert config.has_ve
        assert config.has_relay
        assert config.has_rewards
        assert config.has_price_oracle
        assert config.ve_sugar_address is not None
        assert config.relay_sugar_address is not None
        assert config.price_oracle_address is not None

    def test_optimism_config(self) -> None:
        """Optimism chain should have full contract support."""
        config = CHAIN_CONFIGS[ChainId.OPTIMISM]
        assert config.has_ve
        assert config.has_relay
        assert config.has_rewards
        assert config.has_price_oracle

    def test_mode_config_no_ve(self) -> None:
        """Mode chain should not have VE or Relay."""
        config = CHAIN_CONFIGS[ChainId.MODE]
        assert not config.has_ve
        assert not config.has_relay
        assert config.has_rewards
        assert config.has_price_oracle
        assert config.ve_sugar_address is None
        assert config.relay_sugar_address is None


class TestGetChainConfig:
    """Test get_chain_config function."""

    def test_by_chain_id(self) -> None:
        """Should return config when given ChainId."""
        config = get_chain_config(ChainId.BASE)
        assert config.chain_id == ChainId.BASE

    def test_by_string_lowercase(self) -> None:
        """Should return config when given lowercase string."""
        config = get_chain_config("base")
        assert config.chain_id == ChainId.BASE

    def test_by_string_uppercase(self) -> None:
        """Should return config when given uppercase string."""
        config = get_chain_config("BASE")
        assert config.chain_id == ChainId.BASE

    def test_by_string_mixed_case(self) -> None:
        """Should return config when given mixed case string."""
        config = get_chain_config("Base")
        assert config.chain_id == ChainId.BASE

    def test_alias_op(self) -> None:
        """'op' should be alias for optimism."""
        config = get_chain_config("op")
        assert config.chain_id == ChainId.OPTIMISM

    def test_invalid_chain_raises(self) -> None:
        """Should raise error for unknown chain."""
        with pytest.raises(ValueError) as exc_info:
            get_chain_config("unknown_chain")
        assert "unknown_chain" in str(exc_info.value).lower()

    def test_invalid_type_raises(self) -> None:
        """Should raise error for invalid type."""
        with pytest.raises((ValueError, TypeError, AttributeError)):
            get_chain_config(12345)  # type: ignore


class TestConnectors:
    """Test connector configuration."""

    def test_base_has_connectors(self) -> None:
        """Base should have connector tokens."""
        config = CHAIN_CONFIGS[ChainId.BASE]
        assert len(config.connectors) > 0

    def test_optimism_has_connectors(self) -> None:
        """Optimism should have connector tokens."""
        config = CHAIN_CONFIGS[ChainId.OPTIMISM]
        assert len(config.connectors) > 0

    def test_connectors_are_addresses(self) -> None:
        """Connectors should be valid Ethereum addresses."""
        for config in CHAIN_CONFIGS.values():
            for connector in config.connectors:
                assert connector.startswith("0x")
                assert len(connector) == 42
