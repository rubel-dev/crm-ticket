from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


EXPECTED_RESPONSE_KEYS = {
    "ticket_id",
    "case_type",
    "severity",
    "department",
    "agent_summary",
    "human_review_required",
    "confidence",
}


def test_sort_ticket_wrong_transfer() -> None:
    response = client.post(
        "/sort-ticket",
        json={
            "ticket_id": "T-001",
            "channel": "app",
            "locale": "en",
            "message": "I sent 5000 taka to a wrong number this morning, please help me get it back",
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body == {
        "ticket_id": "T-001",
        "case_type": "wrong_transfer",
        "severity": "high",
        "department": "dispute_resolution",
        "agent_summary": "Customer reports sending money to the wrong recipient and requests assistance.",
        "human_review_required": False,
        "confidence": 0.94,
    }


def test_sort_ticket_response_has_exact_keys() -> None:
    response = client.post(
        "/sort-ticket",
        json={"ticket_id": "T-KEYS", "message": "I need help with the app."},
    )

    assert response.status_code == 200
    assert set(response.json()) == EXPECTED_RESPONSE_KEYS


def test_sort_ticket_payment_failed() -> None:
    response = client.post(
        "/sort-ticket",
        json={"ticket_id": "T-PAY", "message": "Payment failed but my balance was deducted."},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["ticket_id"] == "T-PAY"
    assert body["case_type"] == "payment_failed"
    assert body["severity"] == "high"
    assert body["department"] == "payments_ops"
    assert body["human_review_required"] is False


def test_sort_ticket_simple_refund_goes_to_customer_support() -> None:
    response = client.post(
        "/sort-ticket",
        json={"ticket_id": "T-REF", "message": "I changed my mind and want a refund."},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["case_type"] == "refund_request"
    assert body["severity"] == "low"
    assert body["department"] == "customer_support"
    assert body["human_review_required"] is False


def test_sort_ticket_contested_refund_goes_to_dispute_resolution() -> None:
    response = client.post(
        "/sort-ticket",
        json={"ticket_id": "T-DISPUTE", "message": "Merchant refuses refund for a damaged order."},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["case_type"] == "refund_request"
    assert body["severity"] == "medium"
    assert body["department"] == "dispute_resolution"


def test_sort_ticket_phishing_priority() -> None:
    response = client.post(
        "/sort-ticket",
        json={
            "ticket_id": "T-002",
            "message": "Payment failed and someone called asking for my OTP.",
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["case_type"] == "phishing_or_social_engineering"
    assert body["severity"] == "critical"
    assert body["department"] == "fraud_risk"
    assert body["human_review_required"] is True
    assert "provide your OTP" not in body["agent_summary"]
