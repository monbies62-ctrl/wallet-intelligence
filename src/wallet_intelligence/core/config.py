"""Application configuration."""

from __future__ import annotations

from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """Wallet Intelligence configuration."""

    # App
    app_name: str = "Wallet Intelligence"
    debug: bool = False
    log_level: str = "INFO"

    # Server
    host: str = "0.0.0.0"
    port: int = 8080

    # Database
    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/wallet_intel"
    redis_url: str = "redis://localhost:6379"

    # RPC endpoints
    eth_rpc_url: str = "https://eth-mainnet.g.alchemy.com/v2/demo"
    base_rpc_url: str = "https://mainnet.base.org"
    arb_rpc_url: str = "https://arb1.arbitrum.io/rpc"
    polygon_rpc_url: str = "https://polygon-rpc.com"
    solana_rpc_url: str = "https://api.mainnet-beta.solana.com"

    # External APIs
    etherscan_api_key: str = ""
    openai_api_key: str = ""
    dexscreener_api_url: str = "https://api.dexscreener.com/latest"
    defillama_api_url: str = "https://api.llama.fi"

    # Alerts
    telegram_bot_token: str = ""
    telegram_chat_id: str = ""
    discord_webhook_url: str = ""

    # Monitoring
    poll_interval_seconds: int = 12
    whale_threshold_eth: float = 100.0
    whale_threshold_sol: float = 1000.0
    max_tracked_wallets: int = 1000

    # AI
    ai_classification_enabled: bool = True
    ai_model: str = "gpt-4o-mini"

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
