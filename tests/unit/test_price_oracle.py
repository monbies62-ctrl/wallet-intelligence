"""Unit tests for price oracle."""

import pytest
from wallet_intelligence.services.price_oracle import PriceOracle


@pytest.mark.asyncio
async def test_price_oracle_init():
    oracle = PriceOracle()
    assert oracle._cache_ttl == 60


@pytest.mark.asyncio
async def test_native_chain_mapping():
    oracle = PriceOracle()
    # Verify all chains have native token addresses
    chains = ["ethereum", "base", "arbitrum", "polygon", "solana"]
    for chain in chains:
        # Should not raise
        await oracle.get_native_price(chain)
