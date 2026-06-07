"""Unit tests for database models."""

import pytest
from wallet_intelligence.models.wallet import Chain, AlertType


def test_chain_enum():
    assert Chain.ETHEREUM == "ethereum"
    assert Chain.SOLANA == "solana"
    assert len(Chain) == 5


def test_alert_type_enum():
    assert AlertType.WHALE_TX == "whale_tx"
    assert AlertType.LARGE_SWAP == "large_swap"


def test_chain_values():
    expected = {"ethereum", "base", "arbitrum", "polygon", "solana"}
    actual = {c.value for c in Chain}
    assert actual == expected
