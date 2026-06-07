"""AI-powered transaction classification."""

from __future__ import annotations

import json
from dataclasses import dataclass

from openai import AsyncOpenAI

from wallet_intelligence.core.config import settings


@dataclass
class TxClassification:
    """Classification result."""

    category: str  # swap, transfer, lend, borrow, stake, bridge, nft_trade, etc.
    protocol: str | None  # Uniswap, Aave, etc.
    description: str  # human-readable description
    risk_score: float  # 0.0 (safe) to 1.0 (suspicious)
    confidence: float  # 0.0 to 1.0
    tags: list[str]  # defi, dex, lending, bridge, etc.


class AIClassifier:
    """Classify blockchain transactions using LLM."""

    def __init__(self):
        self._client: AsyncOpenAI | None = None
        self._enabled = settings.ai_classification_enabled

    async def start(self) -> None:
        if self._enabled and settings.openai_api_key:
            self._client = AsyncOpenAI(api_key=settings.openai_api_key)
        else:
            self._enabled = False

    async def classify_transaction(self, tx_data: dict) -> TxClassification:
        """Classify a transaction using AI."""
        if not self._enabled or not self._client:
            return TxClassification(
                category="unknown",
                protocol=None,
                description="AI classification disabled",
                risk_score=0.0,
                confidence=0.0,
                tags=[],
            )

        prompt = f"""Classify this blockchain transaction:

Chain: {tx_data.get("chain", "unknown")}
From: {tx_data.get("from_address", "")}
To: {tx_data.get("to_address", "")}
Value USD: ${tx_data.get("value_usd", 0):,.2f}
Method ID: {tx_data.get("method_id", "N/A")}
Token Transfers: {json.dumps(tx_data.get("token_transfers", []), indent=2)}
Input Data (first 100 bytes): {tx_data.get("input_data", "")[:100]}

Respond in JSON:
{{
    "category": "swap|transfer|lend|borrow|stake|unstake|bridge|nft_trade|approve|airdrop|other",
    "protocol": "protocol name or null",
    "description": "brief human-readable description",
    "risk_score": 0.0 to 1.0,
    "confidence": 0.0 to 1.0,
    "tags": ["tag1", "tag2"]
}}"""

        try:
            response = await self._client.chat.completions.create(
                model=settings.ai_model,
                messages=[
                    {"role": "system", "content": "You are a blockchain transaction analyst. Classify transactions accurately."},
                    {"role": "user", "content": prompt},
                ],
                temperature=0.1,
                max_tokens=300,
                response_format={"type": "json_object"},
            )

            result = json.loads(response.choices[0].message.content)
            return TxClassification(
                category=result.get("category", "unknown"),
                protocol=result.get("protocol"),
                description=result.get("description", ""),
                risk_score=float(result.get("risk_score", 0)),
                confidence=float(result.get("confidence", 0)),
                tags=result.get("tags", []),
            )
        except Exception as e:
            return TxClassification(
                category="unknown",
                protocol=None,
                description=f"Classification error: {str(e)[:100]}",
                risk_score=0.0,
                confidence=0.0,
                tags=[],
            )

    async def analyze_wallet_behavior(self, recent_txs: list[dict]) -> dict:
        """Analyze wallet behavior patterns from recent transactions."""
        if not self._enabled or not self._client or not recent_txs:
            return {"behavior": "unknown", "risk_level": "unknown"}

        tx_summaries = [
            f"- {tx.get('category', 'unknown')}: {tx.get('description', '')} (${tx.get('value_usd', 0):,.2f})"
            for tx in recent_txs[:20]
        ]

        prompt = f"""Analyze this wallet's recent transaction behavior:

{chr(10).join(tx_summaries)}

Respond in JSON:
{{
    "behavior": "trader|holder|yield_farmer|bot|whale|institution|unknown",
    "risk_level": "low|medium|high",
    "notable_patterns": ["pattern1", "pattern2"],
    "likely_profitable": true/false,
    "summary": "brief analysis"
}}"""

        try:
            response = await self._client.chat.completions.create(
                model=settings.ai_model,
                messages=[
                    {"role": "system", "content": "You are a blockchain wallet analyst."},
                    {"role": "user", "content": prompt},
                ],
                temperature=0.2,
                max_tokens=500,
                response_format={"type": "json_object"},
            )
            return json.loads(response.choices[0].message.content)
        except Exception:
            return {"behavior": "unknown", "risk_level": "unknown"}
