import pytest

from fraud_agent_orchestrator.services.triage_service import execute_triage
from fraud_agent_orchestrator.settings.env import AppSettings


def test_execute_triage_low_risk(sample_alert):
    out = execute_triage(sample_alert, app_settings=AppSettings(opa_url=None))
    assert out["audit_verified"] is True
    assert out["result"]["decision"] in ("approve", "review", "escalate")
    assert "evidence_signature" in out
    assert out["evidence_signature"].startswith("sha256-hmac:")


def test_opa_escalate_on_kp():
    alert = {
        "transaction_id": "t1",
        "user_id": "u",
        "timestamp": "2026-04-09T12:00:00Z",
        "amount": 10.0,
        "currency": "USD",
        "merchant_category": "grocery",
        "country": "KP",
        "card_present": True,
        "auth_attempts_24h": 1,
        "failed_auth_attempts_24h": 0,
        "prior_transactions_1h": 0,
    }
    out = execute_triage(alert, app_settings=AppSettings(opa_url=None))
    # Python PolicyAgent already escalates restricted geo; KP triggers deny in OPA when enabled
    assert out["result"]["decision"] == "escalate"
