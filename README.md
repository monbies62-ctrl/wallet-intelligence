# 🔍 Wallet Intelligence Dashboard

Real-time wallet tracking, whale monitoring, and smart money analytics powered by AI.

## Features

- **Wallet Tracking** — Monitor any EVM/Solana wallet in real-time
- **Whale Alerts** — Get notified when large transactions happen
- **Smart Money Analysis** — AI-powered transaction classification
- **P&L Tracking** — Track profit/loss across wallets and protocols
- **Multi-Chain** — Ethereum, Base, Arbitrum, Solana support
- **Real-time Dashboard** — WebSocket-powered live updates
- **Telegram/Discord Alerts** — Instant notifications for whale movements

## Quick Start

```bash
pip install wallet-intelligence
wallet-intel serve --port 8080
```

## Architecture

```
┌─────────────────────────────────────────────────────┐
│                   Dashboard (React)                  │
├─────────────────────────────────────────────────────┤
│              WebSocket API (FastAPI)                  │
├──────────┬──────────┬──────────┬────────────────────┤
│ EVM RPC  │ Solana   │ DeFi APIs│ AI Classifier      │
│ Monitor  │ Monitor  │ (DexScreener, DefiLlama)     │
├──────────┴──────────┴──────────┴────────────────────┤
│           PostgreSQL + Redis Cache                   │
└─────────────────────────────────────────────────────┘
```

## Configuration

```env
# RPC endpoints
ETH_RPC_URL=https://eth-mainnet.g.alchemy.com/v2/YOUR_KEY
BASE_RPC_URL=https://mainnet.base.org
ARB_RPC_URL=https://arb1.arbitrum.io/rpc
SOLANA_RPC_URL=https://api.mainnet-beta.solana.com

# AI classification
OPENAI_API_KEY=sk-...

# Database
DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5432/wallet_intel
REDIS_URL=redis://localhost:6379

# Alerts
TELEGRAM_BOT_TOKEN=...
DISCORD_WEBHOOK_URL=...
```

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/wallets` | GET/POST | Manage tracked wallets |
| `/api/v1/wallets/{address}` | GET | Wallet details + holdings |
| `/api/v1/wallets/{address}/txs` | GET | Transaction history |
| `/api/v1/wallets/{address}/pnl` | GET | P&L analysis |
| `/api/v1/whales` | GET | Recent whale transactions |
| `/api/v1/alerts` | GET/POST | Manage alert rules |
| `/api/v1/analytics/smart-money` | GET | Smart money movements |
| `/ws/live` | WS | Real-time transaction stream |

## License

MIT
