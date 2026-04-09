"""Intake agent for alert validation and normalization."""

from __future__ import annotations

from typing import Any

from fraud_agent_orchestrator.models import TransactionAlert


class IntakeAgent:
    required_fields = {
        "transaction_id",
        "user_id",
        "timestamp",
        "amount",
        "currency",
        "merchant_category",
        "country",
        "card_present",
        "auth_attempts_24h",
        "failed_auth_attempts_24h",
        "prior_transactions_1h",
    }

    def run(self, raw: dict[str, Any]) -> TransactionAlert:
        missing = self.required_fields - set(raw.keys())
        if missing:
            missing_fields = ", ".join(sorted(missing))
            raise ValueError(f"Missing required fields: {missing_fields}")
        amount = float(raw["amount"])
        if amount < 0:
            raise ValueError("amount must be non-negative")
        return TransactionAlert(
            transaction_id=str(raw["transaction_id"]).strip(),
            user_id=str(raw["user_id"]).strip(),
            timestamp=str(raw["timestamp"]).strip(),
            amount=amount,
            currency=str(raw["currency"]).upper().strip(),
            merchant_category=str(raw["merchant_category"]).strip().lower(),
            country=str(raw["country"]).upper().strip(),
            card_present=bool(raw["card_present"]),
            auth_attempts_24h=int(raw["auth_attempts_24h"]),
            failed_auth_attempts_24h=int(raw["failed_auth_attempts_24h"]),
            prior_transactions_1h=int(raw["prior_transactions_1h"]),
            user_home_country=(
                str(raw["user_home_country"]).upper().strip()
                if raw.get("user_home_country")
                else None
            ),
            metadata=raw.get("metadata", {}) or {},
        )
