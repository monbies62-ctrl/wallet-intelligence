# Architecture

## System Overview

```
┌─────────────────────────────────────────────────────────┐
│                    React Dashboard                       │
│              (real-time WebSocket updates)               │
├──────────────────────┬──────────────────────────────────┤
│    REST API          │       WebSocket API              │
│  /api/v1/wallets     │       /ws/live                   │
│  /api/v1/whales      │                                  │
│  /api/v1/alerts      │                                  │
├──────────────────────┴──────────────────────────────────┤
│                    FastAPI Application                   │
├──────────┬──────────┬──────────┬────────────────────────┤
│ Services │          │          │                        │
│ Price    │ AI       │ Alert    │ Chain Monitors         │
│ Oracle   │ Classif. │ Service  │ EVM / Solana           │
├──────────┴──────────┴──────────┴────────────────────────┤
│              PostgreSQL + Redis Cache                    │
└─────────────────────────────────────────────────────────┘
```

## Data Flow

1. **Chain Monitors** poll RPC nodes for new blocks/transactions
2. **Price Oracle** enriches transactions with USD values
3. **AI Classifier** categorizes transactions (swap, lend, etc.)
4. **Alert Service** checks rules and sends notifications
5. **WebSocket** broadcasts live events to dashboard
6. **PostgreSQL** persists all data for historical queries

## Key Design Decisions

- **Async-first**: FastAPI + asyncpg for non-blocking I/O
- **Multi-chain**: Abstract chain interface, pluggable monitors
- **Cache layer**: Redis for hot data (prices, recent queries)
- **WebSocket**: Real-time updates without polling
- **AI-powered**: LLM classification for transaction analysis

## Scaling Considerations

- Chain monitors can run as separate workers
- Redis pub/sub for cross-instance WebSocket broadcast
- Read replicas for analytics queries
- TimescaleDB for time-series transaction data
