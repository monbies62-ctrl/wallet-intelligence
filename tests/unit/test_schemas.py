"""Unit tests for API schemas."""

import pytest
from pydantic import ValidationError
from wallet_intelligence.api.schemas import WalletCreate, AlertCreate
from wallet_intelligence.models.wallet import Chain, AlertType


def test_wallet_create_valid():
    wallet = WalletCreate(address="0x1234", chain=Chain.ETHEREUM, label="Test")
    assert wallet.address == "0x1234"
    assert wallet.chain == Chain.ETHEREUM


def test_wallet_create_default_tags():
    wallet = WalletCreate(address="0x1234", chain=Chain.ETHEREUM)
    assert wallet.tags == []


def test_alert_create_valid():
    alert = AlertCreate(alert_type=AlertType.WHALE_TX, threshold_usd=100000)
    assert alert.alert_type == AlertType.WHALE_TX
    assert alert.notify_telegram is True
    assert alert.notify_discord is False
