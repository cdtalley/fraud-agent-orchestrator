"""Feature engineering agent."""

from __future__ import annotations

from fraud_agent_orchestrator.config import Settings
from fraud_agent_orchestrator.models import DerivedFeatures, TransactionAlert


class FeatureAgent:
    risky_merchant_categories = {"electronics", "gift_cards", "crypto", "travel"}

    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def run(self, alert: TransactionAlert) -> DerivedFeatures:
        is_geo_mismatch = bool(
            alert.user_home_country and alert.user_home_country != alert.country
        )
        is_high_velocity = (
            alert.prior_transactions_1h >= self.settings.high_velocity_1h_threshold
        )
        is_high_amount = alert.amount >= self.settings.high_amount_threshold
        is_risky_merchant = alert.merchant_category in self.risky_merchant_categories
        auth_failure_ratio = (
            0.0
            if alert.auth_attempts_24h <= 0
            else alert.failed_auth_attempts_24h / alert.auth_attempts_24h
        )
        amount_bucket = (
            "high"
            if alert.amount >= self.settings.high_amount_threshold
            else ("medium" if alert.amount >= 500 else "low")
        )
        return DerivedFeatures(
            amount_z_bucket=amount_bucket,
            is_geo_mismatch=is_geo_mismatch,
            is_high_velocity=is_high_velocity,
            is_high_amount=is_high_amount,
            is_risky_merchant=is_risky_merchant,
            auth_failure_ratio=auth_failure_ratio,
        )
