import pytest


@pytest.fixture
def sample_alert():
    return {
        "transaction_id": "txn_test",
        "user_id": "u1",
        "timestamp": "2026-04-09T12:00:00Z",
        "amount": 50.0,
        "currency": "USD",
        "merchant_category": "grocery",
        "country": "US",
        "user_home_country": "US",
        "card_present": True,
        "auth_attempts_24h": 1,
        "failed_auth_attempts_24h": 0,
        "prior_transactions_1h": 0,
    }
