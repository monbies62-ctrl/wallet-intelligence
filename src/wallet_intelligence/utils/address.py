"""Address validation and formatting utilities."""

from __future__ import annotations

import re


def is_valid_evm_address(address: str) -> bool:
    """Check if string is a valid EVM address."""
    return bool(re.match(r"^0x[0-9a-fA-F]{40}$", address))


def is_valid_solana_address(address: str) -> bool:
    """Check if string is a valid Solana address (base58, 32-44 chars)."""
    return bool(re.match(r"^[1-9A-HJ-NP-Za-km-z]{32,44}$", address))


def normalize_address(address: str, chain: str = "ethereum") -> str:
    """Normalize address to lowercase (EVM) or as-is (Solana)."""
    if chain == "solana":
        return address
    return address.lower()


def format_address(address: str, chars: int = 6) -> str:
    """Format address for display: 0x1234...5678."""
    if len(address) <= chars * 2 + 2:
        return address
    return f"{address[:chars + 2]}...{address[-chars:]}"


def format_value_usd(value: float) -> str:
    """Format USD value for display."""
    if value >= 1_000_000:
        return f"${value / 1_000_000:.2f}M"
    elif value >= 1_000:
        return f"${value / 1_000:.1f}K"
    else:
        return f"${value:.2f}"
