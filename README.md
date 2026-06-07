<div align="center">

# 🔍 Wallet Intelligence

**Real-time wallet tracking, whale monitoring, and smart money analytics powered by AI.**

### 🔗 [Live Demo](https://monbies62-ctrl.github.io/wallet-intelligence/)

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)

[Features](#features) · [Quick Start](#quick-start) · [API](#api) · [Architecture](#architecture)

</div>

---

## Features

| Feature | Description |
|---------|-------------|
| 🔗 **Multi-Chain** | Ethereum, Base, Arbitrum, Polygon, Solana |
| 🐋 **Whale Alerts** | Telegram, Discord, WebSocket notifications |
| 🧠 **AI Classification** | LLM-powered tx categorization (swap, lend, bridge, etc.) |
| 📊 **P&L Tracking** | Realized/unrealized gains per wallet |
| 💰 **Smart Money** | Track profitable wallets and funds |
| ⚡ **WebSocket** | Real-time transaction stream |
| 💲 **Price Oracle** | DexScreener + CoinGecko integration |
| 🏷️ **Wallet Labels** | Tag, categorize, and organize wallets |

## Quick Start

```bash
# Install
pip install wallet-intelligence

# Start server
wallet-intel serve --port 8080

# Add a wallet to track
curl -X POST http://localhost:8080/api/v1/wallets \
  -H "Content-Type: application/json" \
  -d '{"address": "0x...", "chain": "ethereum", "label": "Whale 1"}'

# Get whale transactions
curl http://localhost:8080/api/v1/whales?min_value_usd=100000
```

## API

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/v1/wallets` | List tracked wallets |
| `POST` | `/api/v1/wallets` | Add wallet to track |
| `GET` | `/api/v1/wallets/{addr}` | Wallet details + holdings |
| `GET` | `/api/v1/wallets/{addr}/txs` | Transaction history |
| `GET` | `/api/v1/wallets/{addr}/pnl` | P&L analysis |
| `GET` | `/api/v1/whales` | Recent whale transactions |
| `GET` | `/api/v1/analytics/smart-money` | Smart money wallets |
| `GET` | `/api/v1/analytics/volume` | Volume statistics |
| `GET` | `/api/v1/alerts` | List alert rules |
| `POST` | `/api/v1/alerts` | Create alert rule |
| `WS` | `/ws/live` | Real-time transaction stream |

## Configuration

```env
# RPC endpoints
ETH_RPC_URL=https://eth-mainnet.g.alchemy.com/v2/YOUR_KEY
BASE_RPC_URL=https://mainnet.base.org
ARB_RPC_URL=https://arb1.arbitrum.io/rpc
SOLANA_RPC_URL=https://api.mainnet-beta.solana.com

# Database
DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5432/wallet_intel
REDIS_URL=redis://localhost:6379

# Alerts
TELEGRAM_BOT_TOKEN=...
TELEGRAM_CHAT_ID=...
DISCORD_WEBHOOK_URL=...

# AI
OPENAI_API_KEY=...
AI_MODEL=gpt-4o-mini

# Thresholds
WHALE_THRESHOLD_ETH=100
WHALE_THRESHOLD_SOL=1000
```

## Architecture

```
┌─────────────────────────────────────────────┐
│            Dashboard (WebSocket)             │
├────────────┬────────────────────────────────┤
│  REST API  │       WebSocket API            │
│ /api/v1/*  │          /ws/live              │
├────────────┴────────────────────────────────┤
│              FastAPI Application             │
├─────────┬─────────┬─────────┬───────────────┤
│ EVM     │ Solana  │ Price   │ AI            │
│ Monitor │ Monitor │ Oracle  │ Classifier    │
├─────────┴─────────┴─────────┴───────────────┤
│           PostgreSQL + Redis                  │
└─────────────────────────────────────────────┘
```

## Docker

```bash
docker-compose -f docker/docker-compose.yml up -d
```

## License

MIT — see [LICENSE](LICENSE) for details.

---

<div align="center">
<strong>Track wallets. Spot whales. Analyze smart money.</strong>
<br><br>
<a href="https://monbies62-ctrl.github.io/wallet-intelligence/">Live Demo</a> ·
<a href="https://github.com/monbies62-ctrl/wallet-intelligence">GitHub</a>
</div>
